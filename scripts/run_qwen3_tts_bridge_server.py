#!/usr/bin/env python3
import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO

import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="OpenAI-speech compatible bridge for Qwen3-TTS"
    )
    parser.add_argument(
        "--model",
        default="Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
        help="Qwen3-TTS model id",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=18117, help="Bind port")
    parser.add_argument(
        "--device", default="cuda:0", help="Device map value, e.g. cuda:0 or cpu"
    )
    parser.add_argument(
        "--dtype",
        default="bfloat16",
        choices=["bfloat16", "float16", "float32"],
        help="Torch dtype used for model load",
    )
    parser.add_argument(
        "--default-language",
        default="english",
        help="Fallback language when request has no language",
    )
    parser.add_argument(
        "--default-voice",
        default="sohee",
        help="Fallback speaker when request has no voice",
    )
    return parser.parse_args()


def resolve_dtype(dtype_name: str) -> torch.dtype:
    if dtype_name == "bfloat16":
        return torch.bfloat16
    if dtype_name == "float16":
        return torch.float16
    return torch.float32


def main() -> None:
    args = parse_args()
    dtype = resolve_dtype(args.dtype)

    model = Qwen3TTSModel.from_pretrained(
        args.model,
        device_map=args.device,
        dtype=dtype,
    )

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            if self.path != "/v1/audio/speech":
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0") or 0)
                body = (
                    json.loads(self.rfile.read(content_length).decode("utf-8"))
                    if content_length > 0
                    else {}
                )

                text = body.get("text") or body.get("input") or ""
                speaker = body.get("voice") or args.default_voice
                language = body.get("language") or args.default_language

                wavs, sr = model.generate_custom_voice(
                    text=text,
                    speaker=speaker,
                    language=language,
                )

                buffer = BytesIO()
                sf.write(buffer, wavs[0], sr, format="WAV")
                payload = buffer.getvalue()

                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "audio/wav")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            except Exception as exc:
                message = json.dumps({"error": str(exc)}).encode("utf-8")
                self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(message)))
                self.end_headers()
                self.wfile.write(message)

        def log_message(self, *_: object) -> None:
            return

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(
        f"qwen3_tts bridge listening on http://{args.host}:{args.port}/v1/audio/speech"
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
