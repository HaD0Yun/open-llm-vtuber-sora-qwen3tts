# pyright: reportUnusedCallResult=false, reportUnknownVariableType=false, reportImplicitOverride=false
from __future__ import annotations

import json
import math
import os
import struct
import time
import wave
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from typing import cast


def _build_wav_bytes(duration_sec: float = 0.6, sample_rate: int = 16000) -> bytes:
    buffer = BytesIO()
    amplitude = 16000
    frequency_hz = 330.0
    frame_count = int(sample_rate * duration_sec)

    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for index in range(frame_count):
            sample = int(
                amplitude * math.sin(2 * math.pi * frequency_hz * index / sample_rate)
            )
            wav_file.writeframesraw(struct.pack("<h", sample))

    return buffer.getvalue()


class MockInferenceHandler(BaseHTTPRequestHandler):
    wav_bytes: bytes = _build_wav_bytes()
    request_log_path: str | None = os.environ.get("TASK6_MOCK_LOG")

    def _read_json(self) -> dict[str, object]:
        content_len = int(self.headers.get("Content-Length", "0"))
        if content_len <= 0:
            return {}
        raw_body = self.rfile.read(content_len)
        return cast(dict[str, object], json.loads(raw_body.decode("utf-8")))

    def _log(self, payload: dict[str, object]) -> None:
        if not self.request_log_path:
            return
        with open(self.request_log_path, "a", encoding="utf-8") as fp:
            fp.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def _write_json(self, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _write_sse_chat(self, message: str) -> None:
        chunks = [
            {
                "id": "chatcmpl-task6",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": "qwen3-mock",
                "choices": [
                    {"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}
                ],
            },
            {
                "id": "chatcmpl-task6",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": "qwen3-mock",
                "choices": [
                    {"index": 0, "delta": {"content": message}, "finish_reason": None}
                ],
            },
            {
                "id": "chatcmpl-task6",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": "qwen3-mock",
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            },
        ]

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        for chunk in chunks:
            payload = f"data: {json.dumps(chunk)}\n\n".encode("utf-8")
            self.wfile.write(payload)
            self.wfile.flush()
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/v1/models":
            self._write_json({"object": "list", "data": [{"id": "qwen3-mock"}]})
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/v1/chat/completions":
            body = self._read_json()
            self._log({"path": self.path, "body": body})
            self._write_sse_chat("Task6 smoke turn response for qwen3_tts playback.")
            return

        if self.path == "/v1/audio/speech":
            body = self._read_json()
            self._log({"path": self.path, "body": body})

            input_text = str(body.get("input", ""))
            if "TASK6_TTS_TIMEOUT" in input_text:
                time.sleep(1.2)

            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Content-Length", str(len(self.wav_bytes)))
            self.end_headers()
            self.wfile.write(self.wav_bytes)
            return

        self.send_error(HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> int:
    host = os.environ.get("TASK6_MOCK_HOST", "127.0.0.1")
    port = int(os.environ.get("TASK6_MOCK_PORT", "18080"))
    server = ThreadingHTTPServer((host, port), MockInferenceHandler)
    print(f"task6 mock inference server listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
