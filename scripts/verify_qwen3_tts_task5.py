# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnusedCallResult=false, reportImplicitOverride=false
from __future__ import annotations

import json
import math
import struct
import sys
import threading
import time
import wave
from dataclasses import asdict, dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from typing import cast


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from open_llm_vtuber.tts.tts_factory import TTSFactory  # pyright: ignore[reportMissingImports]


MULTILINGUAL_CASES: list[tuple[str, str]] = [
    ("ko", "안녕하세요 테스트입니다."),
    ("en", "Hello, this is a test."),
    ("ja", "こんにちは、テストです。"),
    ("mixed", "오늘 meeting은 3pm입니다."),
]


def _find_evidence_dir() -> Path:
    for base in [REPO_ROOT, *REPO_ROOT.parents]:
        candidate = base / ".sisyphus" / "evidence"
        if candidate.exists():
            return candidate
    fallback = REPO_ROOT / ".sisyphus" / "evidence"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def _build_wav_bytes(duration_sec: float = 0.4, sample_rate: int = 16000) -> bytes:
    buffer = BytesIO()
    amplitude = 32767
    frequency_hz = 440.0
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


def _read_wav_stats(path: Path) -> dict[str, int]:
    with wave.open(str(path), "rb") as wav_file:
        return {
            "channels": wav_file.getnchannels(),
            "sample_width": wav_file.getsampwidth(),
            "sample_rate": wav_file.getframerate(),
            "frame_count": wav_file.getnframes(),
        }


class _BaseHandler(BaseHTTPRequestHandler):
    wav_bytes: bytes = _build_wav_bytes()

    def _read_json(self) -> dict[str, object]:
        content_len = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_len) if content_len > 0 else b"{}"
        return cast(dict[str, object], json.loads(raw_body.decode("utf-8")))

    def _write_audio(self) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Length", str(len(self.wav_bytes)))
        self.end_headers()
        try:
            self.wfile.write(self.wav_bytes)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, format: str, *args: object) -> None:
        return


class _ImmediateAudioHandler(_BaseHandler):
    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/audio/speech":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        _ = self._read_json()
        self._write_audio()


class _DelayedAudioHandler(_BaseHandler):
    delay_seconds: float = 0.35

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/audio/speech":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        _ = self._read_json()
        time.sleep(self.delay_seconds)
        self._write_audio()


@dataclass
class CaseResult:
    name: str
    success: bool
    details: str
    artifact_path: str | None = None
    bytes_size: int | None = None
    wav_stats: dict[str, int] | None = None


def _start_mock_server(
    handler_cls: type[BaseHTTPRequestHandler],
) -> tuple[ThreadingHTTPServer, threading.Thread]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def _stop_mock_server(server: ThreadingHTTPServer, thread: threading.Thread) -> None:
    server.shutdown()
    server.server_close()
    thread.join(timeout=3)


def _run_positive_multilingual(evidence_dir: Path) -> list[CaseResult]:
    server, thread = _start_mock_server(_ImmediateAudioHandler)
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    results: list[CaseResult] = []

    try:
        engine = TTSFactory.get_tts_engine(
            "qwen3_tts",
            base_url=base_url,
            endpoint="/v1/audio/speech",
            model_name="Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
            language="auto",
            timeout=2.0,
            max_retries=1,
            output_format="wav",
            file_extension="wav",
        )

        for case_name, text in MULTILINGUAL_CASES:
            file_stem = f"qwen3_task5_{case_name}"
            output = engine.generate_audio(text, file_stem)
            if not output:
                results.append(
                    CaseResult(
                        name=case_name,
                        success=False,
                        details="Engine returned no output path",
                    )
                )
                continue

            output_path = Path(output)
            if not output_path.is_absolute():
                output_path = REPO_ROOT / output_path

            if not output_path.exists():
                results.append(
                    CaseResult(
                        name=case_name,
                        success=False,
                        details="Output file missing",
                        artifact_path=str(output_path),
                    )
                )
                continue

            size = output_path.stat().st_size
            if size <= 0:
                results.append(
                    CaseResult(
                        name=case_name,
                        success=False,
                        details="Output file is empty",
                        artifact_path=str(output_path),
                        bytes_size=size,
                    )
                )
                continue

            try:
                wav_stats = _read_wav_stats(output_path)
            except wave.Error as exc:
                results.append(
                    CaseResult(
                        name=case_name,
                        success=False,
                        details=f"Invalid WAV payload: {exc}",
                        artifact_path=str(output_path),
                        bytes_size=size,
                    )
                )
                continue

            if wav_stats["frame_count"] <= 0:
                results.append(
                    CaseResult(
                        name=case_name,
                        success=False,
                        details="WAV has zero frames",
                        artifact_path=str(output_path),
                        bytes_size=size,
                        wav_stats=wav_stats,
                    )
                )
                continue

            results.append(
                CaseResult(
                    name=case_name,
                    success=True,
                    details="Output file exists, non-zero size, valid WAV metadata",
                    artifact_path=str(output_path),
                    bytes_size=size,
                    wav_stats=wav_stats,
                )
            )
    finally:
        _stop_mock_server(server, thread)

    payload = {
        "task": "task-5-multilingual",
        "timestamp_epoch": time.time(),
        "cases": [asdict(result) for result in results],
    }
    (evidence_dir / "task-multilingual-results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return results


def _run_service_down_check(evidence_dir: Path) -> CaseResult:
    engine = TTSFactory.get_tts_engine(
        "qwen3_tts",
        base_url="http://127.0.0.1:9",
        endpoint="/v1/audio/speech",
        model_name="Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
        language="ko",
        timeout=0.5,
        max_retries=1,
        output_format="wav",
        file_extension="wav",
    )
    output = engine.generate_audio("service-down-check", "qwen3_task5_service_down")

    success = output is None
    result = CaseResult(
        name="service_down",
        success=success,
        details="Expected None when service is unreachable",
        artifact_path=str(output) if output else None,
    )

    payload = {
        "task": "task-5-failure-service-down",
        "timestamp_epoch": time.time(),
        "result": asdict(result),
    }
    (evidence_dir / "task-failure-service-down.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return result


def _run_timeout_check(evidence_dir: Path) -> CaseResult:
    server, thread = _start_mock_server(_DelayedAudioHandler)
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        engine = TTSFactory.get_tts_engine(
            "qwen3_tts",
            base_url=base_url,
            endpoint="/v1/audio/speech",
            model_name="Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
            language="ko",
            timeout=0.05,
            max_retries=1,
            output_format="wav",
            file_extension="wav",
        )
        output = engine.generate_audio("timeout-check", "qwen3_task5_timeout")
    finally:
        _stop_mock_server(server, thread)

    success = output is None
    result = CaseResult(
        name="timeout",
        success=success,
        details="Expected None when backend response exceeds timeout",
        artifact_path=str(output) if output else None,
    )

    payload = {
        "task": "task-5-failure-timeout",
        "timestamp_epoch": time.time(),
        "result": asdict(result),
    }
    (evidence_dir / "task-failure-timeout.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return result


def main() -> int:
    evidence_dir = _find_evidence_dir()
    evidence_dir.mkdir(parents=True, exist_ok=True)

    multilingual_results = _run_positive_multilingual(evidence_dir)
    service_down_result = _run_service_down_check(evidence_dir)
    timeout_result = _run_timeout_check(evidence_dir)

    all_results = multilingual_results + [service_down_result, timeout_result]
    passed = [result for result in all_results if result.success]
    failed = [result for result in all_results if not result.success]

    summary_payload = {
        "task": "task-5-qwen3-verification",
        "timestamp_epoch": time.time(),
        "passed_count": len(passed),
        "failed_count": len(failed),
        "all_passed": len(failed) == 0,
        "results": [asdict(result) for result in all_results],
    }
    (evidence_dir / "task-5-qwen3-verification.json").write_text(
        json.dumps(summary_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if failed:
        print("FAIL: qwen3_tts task-5 verification failed")
        for result in failed:
            print(f"- {result.name}: {result.details}")
        return 1

    print("PASS: qwen3_tts task-5 verification passed")
    print(f"Evidence directory: {evidence_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
