from urllib.parse import urljoin
import re

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
    base_instruct: str
    style_intensity: float

    _CANONICAL_LANGUAGE: dict[str, str] = {
        "auto": "Auto",
        "chinese": "Chinese",
        "english": "English",
        "japanese": "Japanese",
        "korean": "Korean",
        "german": "German",
        "french": "French",
        "russian": "Russian",
        "portuguese": "Portuguese",
        "spanish": "Spanish",
        "italian": "Italian",
    }

    _CANONICAL_VOICE: dict[str, str] = {
        "vivian": "Vivian",
        "serena": "Serena",
        "uncle_fu": "Uncle_Fu",
        "dylan": "Dylan",
        "eric": "Eric",
        "ryan": "Ryan",
        "aiden": "Aiden",
        "ono_anna": "Ono_Anna",
        "sohee": "Sohee",
    }

    _DEFAULT_STYLE_INTENSITY: float = 1.8

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
        fallback_model_name: str | None = None,
        output_format: str = "wav",
        file_extension: str = "wav",
        base_instruct: str = "",
        style_intensity: float = _DEFAULT_STYLE_INTENSITY,
    ):
        self.base_url = base_url
        self.endpoint = endpoint
        self.api_url = self._build_api_url(base_url, endpoint)
        self.model_name = model_name
        self.language = self._normalize_language(language)
        self.voice = self._normalize_voice(voice)
        self.timeout = timeout
        self.max_retries = max(1, max_retries)
        self.fallback_model = fallback_model_name or fallback_model
        self.output_format = output_format
        self.file_extension = file_extension.lower()
        self.style_intensity = max(1.0, style_intensity)
        self.base_instruct = (
            base_instruct.strip()
            if base_instruct.strip()
            else "Deliver with strongly amplified emotional contrast, bold pitch movement, and dramatic rhythmic variation while staying natural and clear."
        )

    _EMO_TO_INSTRUCT: dict[str, str] = {
        "joy": "Speak with strong bright joy, lively pace, and clearly smiling resonance. Use higher pitch peaks and warm energetic emphasis.",
        "happy": "Speak with strong bright joy, lively pace, and clearly smiling resonance. Use higher pitch peaks and warm energetic emphasis.",
        "surprise": "Speak with obvious surprise, widened intonation range, and quick expressive accents, while keeping articulation clear.",
        "sadness": "Speak with deep sadness, noticeably slower tempo, softer volume, and heavier emotional weight in the tone.",
        "sad": "Speak with deep sadness, noticeably slower tempo, softer volume, and heavier emotional weight in the tone.",
        "anger": "Speak with clear controlled anger, stronger stress on key words, sharper attacks, and firm assertive rhythm.",
        "fear": "Speak with audible tension and cautious pacing, including subtle trembling uncertainty and tighter breath.",
        "disgust": "Speak with distinct aversion, colder tone color, and clipped emphasis to convey clear disapproval.",
        "neutral": "Speak neutrally but still expressive, with natural prosody and mild dynamic variation instead of flat delivery.",
        "smirk": "Speak with a pronounced playful smirk, teasing confidence, and slightly sarcastic melodic contour.",
    }

    _STYLE_TO_INSTRUCT: dict[str, str] = {
        "comfort": "Use a gentle, comforting tone with warm softness and steady reassuring pacing.",
        "apology": "Use a sincere apologetic tone with softened stress and careful pacing.",
        "celebration": "Use festive excitement with lively rhythm, brighter pitch movement, and crisp energy.",
        "gratitude": "Use heartfelt gratitude with warm resonance and tender emphasis.",
        "teasing": "Use playful teasing with light sarcasm, rhythmic bounce, and smiling delivery.",
        "romantic": "Use an intimate affectionate tone, soft breath, and smooth flowing cadence.",
        "whisper": "Use a whisper-like intimate delivery with reduced intensity and close-mic warmth.",
        "serious": "Use a serious focused tone with lower pitch center, stable tempo, and firm clarity.",
        "authority": "Use assertive authority with strong stress on key words and decisive rhythm.",
        "urgency": "Use urgent pacing with faster tempo, tighter phrase breaks, and heightened emphasis.",
        "curious": "Use curious inquisitive intonation with upward contours and engaged pacing.",
        "storytelling": "Use narrative storytelling cadence with expressive pauses and vivid scene coloring.",
        "instructional": "Use clear instructional delivery with measured pace and precise articulation.",
        "humor": "Use light comedic timing with playful rhythm and expressive punchlines.",
        "calm": "Use calm grounded delivery with smooth transitions and stable breath.",
    }

    _STYLE_RULES: list[tuple[str, str]] = [
        ("apology", r"\b(sorry|apolog|my bad|forgive me)\b|미안|죄송|잘못했"),
        ("gratitude", r"\b(thanks|thank you|appreciate)\b|고마워|감사"),
        (
            "celebration",
            r"\b(congrats|congratulations|awesome|amazing|yay)\b|축하|대박|최고|와{2,}",
        ),
        ("comfort", r"괜찮아|걱정\s*마|힘내|위로|it's ok|you are okay|you'll be okay"),
        ("teasing", r"장난|놀리|약올|hehe|haha|lol|😏|😉"),
        ("romantic", r"사랑|보고싶|좋아해|sweetheart|darling|dear"),
        ("whisper", r"속삭|쉿|작게 말|whisper|quietly|hush"),
        ("authority", r"반드시|당장|지금\s*해|must|need to|do it now"),
        ("urgency", r"긴급|빨리|서둘|urgent|hurry|immediately|asap"),
        ("curious", r"궁금|왜\?|어떻게\?|정말\?|\?$|\b(why|how|really\?)\b"),
        ("storytelling", r"옛날|그때|이야기|once upon a time|suddenly|meanwhile"),
        ("instructional", r"단계|방법|먼저|다음|주의|step|first|next|instructions?"),
        ("humor", r"농담|웃기|ㅋㅋ+|ㅎㅎ+|joke|funny|lmao"),
    ]

    def _normalize_language(self, language: str) -> str:
        language_key = (language or "").strip().lower()
        if not language_key:
            return "Auto"
        return self._CANONICAL_LANGUAGE.get(language_key, language)

    def _normalize_voice(self, voice: str | None) -> str | None:
        if not voice:
            return None
        voice_key = voice.strip().lower()
        return self._CANONICAL_VOICE.get(voice_key, voice)

    @staticmethod
    def _build_api_url(base_url: str, endpoint: str) -> str:
        normalized_base = (base_url or "").rstrip("/") + "/"
        normalized_endpoint = (endpoint or "").lstrip("/")
        return urljoin(normalized_base, normalized_endpoint)

    def _extract_emotion_markers(self, text: str) -> tuple[str, list[str]]:
        markers = re.findall(r"<<emo:([A-Za-z_][A-Za-z0-9_]*)>>", text)
        cleaned = re.sub(r"\s*<<emo:[A-Za-z_][A-Za-z0-9_]*>>\s*", " ", text)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned, [m.lower() for m in markers]

    def _infer_styles(self, text: str) -> list[str]:
        styles: list[str] = []
        lowered = text.lower()

        for style_name, pattern in self._STYLE_RULES:
            if re.search(pattern, lowered, flags=re.IGNORECASE):
                styles.append(style_name)

        exclamation_count = text.count("!") + text.count("！")
        question_count = text.count("?") + text.count("？")
        if exclamation_count >= 2 and "urgency" not in styles:
            styles.append("urgency")
        if question_count >= 1 and "curious" not in styles:
            styles.append("curious")
        if not styles:
            styles.append("calm")

        return styles[:3]

    def _intensity_directive(self) -> str:
        if self.style_intensity >= 2.0:
            return "Intensity mode MAX: make emotion unmistakable with very high contrast, dramatic pitch arcs, and strongly varied rhythm."
        if self.style_intensity >= 1.6:
            return "Intensity mode HIGH: make emotion clearly audible with high contrast, wider pitch range, and strong rhythmic variation."
        if self.style_intensity >= 1.3:
            return "Intensity mode MEDIUM-HIGH: keep emotion prominent with noticeable pitch and rhythm variation."
        return "Intensity mode NORMAL: maintain expressive but controlled emotional coloring."

    def _amplify_instruction(self, instruction: str) -> str:
        if self.style_intensity >= 1.8:
            return f"{instruction} Push the emotional coloration further and avoid flat delivery."
        if self.style_intensity >= 1.4:
            return f"{instruction} Keep emotional emphasis clearly audible."
        return instruction

    def _build_instruct(self, cleaned_text: str, emotions: list[str]) -> str:
        parts: list[str] = []
        if self.base_instruct:
            parts.append(self.base_instruct)
        parts.append(self._intensity_directive())
        selected_styles = self._infer_styles(cleaned_text)
        for style_name in selected_styles:
            style_instruction = self._STYLE_TO_INSTRUCT.get(style_name)
            if style_instruction and style_instruction not in parts:
                parts.append(self._amplify_instruction(style_instruction))
        for emotion in emotions:
            instruction = self._EMO_TO_INSTRUCT.get(emotion)
            if instruction and instruction not in parts:
                parts.append(
                    self._amplify_instruction(
                        f"Secondary cue from facial expression tag '{emotion}': {instruction}"
                    )
                )
        logger.debug(
            f"Qwen3 TTS style routing styles={selected_styles} emotions={emotions} text='{cleaned_text[:80]}'"
        )
        return " ".join(parts)

    def _build_payload(self, text: str, model_name: str) -> dict[str, str]:
        cleaned_text, emotions = self._extract_emotion_markers(text)
        payload = {
            "model": model_name,
            "language": self.language,
            "text": cleaned_text,
            "output_format": self.output_format,
        }
        if self.voice:
            payload["voice"] = self.voice
        instruct = self._build_instruct(cleaned_text, emotions)
        if instruct:
            payload["instruct"] = instruct
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
