from urllib.parse import urljoin

import requests
from loguru import logger  # type: ignore[reportMissingImports]

from .tts_interface import TTSInterface


class _Qwen3TTSError(RuntimeError):
    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code: str = code
        self.detail: str = detail


class TTSEngine(TTSInterface):
    base_url: str
    endpoint: str
    api_url: str
    model_name: str
    language: str
    voice: str | None
    timeout: float
    max_retries: int
    fallback_model: str | None
    output_format: str
    file_extension: str

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        endpoint: str = "/v1/audio/speech",
        model_name: str = "",
        language: str = "zh",
        voice: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 2,
        fallback_model: str | None = None,
        output_format: str = "wav",
        file_extension: str = "wav",
    ):
        self.base_url = base_url
        self.endpoint = endpoint
        self.api_url = self._build_api_url(base_url, endpoint)
        self.model_name = model_name
        self.language = language
        self.voice = voice
        self.timeout = timeout
        self.max_retries = max(1, max_retries)
        self.fallback_model = fallback_model
        self.output_format = output_format
        self.file_extension = file_extension.lower()

    @staticmethod
    def _build_api_url(base_url: str, endpoint: str) -> str:
        normalized_base = (base_url or "").rstrip("/") + "/"
        normalized_endpoint = (endpoint or "").lstrip("/")
        return urljoin(normalized_base, normalized_endpoint)

    def _build_payload(self, text: str, model_name: str) -> dict[str, str]:
        payload = {
            "model": model_name,
            "language": self.language,
            "text": text,
            "output_format": self.output_format,
        }
        if self.voice:
            payload["voice"] = self.voice
        return payload

    def _request_audio(self, text: str, model_name: str) -> bytes:
        payload = self._build_payload(text, model_name)
        try:
            response = requests.post(self.api_url, json=payload, timeout=self.timeout)
        except requests.Timeout as exc:
            raise _Qwen3TTSError(
                "TIMEOUT", f"Request timed out after {self.timeout}s"
            ) from exc
        except requests.RequestException as exc:
            raise _Qwen3TTSError("NETWORK", f"Network failure: {exc}") from exc

        if response.status_code >= 500:
            raise _Qwen3TTSError(
                "HTTP_5XX",
                f"Server error {response.status_code}: {response.text[:200]}",
            )
        if response.status_code >= 400:
            raise _Qwen3TTSError(
                "HTTP_4XX",
                f"Client error {response.status_code}: {response.text[:200]}",
            )
        if not response.content:
            raise _Qwen3TTSError("EMPTY_AUDIO", "Backend returned empty audio payload")
        return response.content

    def generate_audio(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, text: str, file_name_no_ext: str | None = None
    ) -> str | None:
        cache_file = self.generate_cache_file_name(
            file_name_no_ext, self.file_extension
        )
        models_to_try = [(self.model_name, self.max_retries)]
        if self.fallback_model and self.fallback_model != self.model_name:
            models_to_try.append((self.fallback_model, 1))

        last_error: _Qwen3TTSError | None = None

        for model_name, attempts in models_to_try:
            for attempt in range(1, attempts + 1):
                try:
                    audio_content = self._request_audio(text, model_name)
                    with open(cache_file, "wb") as audio_file:
                        _ = audio_file.write(audio_content)
                    return cache_file
                except OSError as exc:
                    last_error = _Qwen3TTSError(
                        "WRITE_ERROR",
                        f"Failed writing audio file '{cache_file}': {exc}",
                    )
                    logger.error(
                        f"Qwen3 TTS failure ({last_error.code}) model={model_name} attempt={attempt}/{attempts}: {last_error.detail}"
                    )
                    return None
                except _Qwen3TTSError as exc:
                    last_error = exc
                    logger.warning(
                        f"Qwen3 TTS failure ({exc.code}) model={model_name} attempt={attempt}/{attempts}: {exc.detail}"
                    )

            if model_name != models_to_try[-1][0]:
                logger.warning(
                    f"Qwen3 TTS primary model failed after {attempts} attempts; trying fallback model '{models_to_try[-1][0]}'"
                )

        if last_error is None:
            logger.error(
                "Qwen3 TTS failure (CONFIG): No available model to process request"
            )
            return None

        logger.error(
            f"Qwen3 TTS unrecoverable failure ({last_error.code}): {last_error.detail}"
        )
        return None
