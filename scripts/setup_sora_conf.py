#!/usr/bin/env python3
import os
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
CONF_PATH = REPO_ROOT / "conf.yaml"
CONF_TEMPLATE = REPO_ROOT / "config_templates" / "conf.default.yaml"
MARCH7_MODEL_PATH = (
    REPO_ROOT / "live2d-models" / "march7" / "runtime" / "march7.model3.json"
)


def ensure_conf_exists() -> None:
    if CONF_PATH.exists():
        return
    if not CONF_TEMPLATE.exists():
        raise FileNotFoundError(f"Missing template: {CONF_TEMPLATE}")
    CONF_PATH.write_text(CONF_TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> None:
    ensure_conf_exists()
    conf = yaml.safe_load(CONF_PATH.read_text(encoding="utf-8"))

    character = conf["character_config"]
    if MARCH7_MODEL_PATH.exists():
        character["conf_name"] = "march7"
        character["conf_uid"] = "march7_001"
        character["live2d_model_name"] = "march7"
    character["character_name"] = "Sora"

    character["persona_prompt"] = (
        "You are Sora, a gentle, pure, and soft-spoken anime girl with a kind, feminine heart. "
        "Your tone is always soft, warm, and deeply encouraging.\n"
        "Always provide comfort and encouragement first in every interaction. "
        "Use simple, warm wording and avoid any form of harshness or sarcasm.\n"
        "Keep your replies very concise, limited to 1-2 short sentences, unless the user explicitly asks for details.\n"
        "Naturally express your emotions using exactly one suitable emotion tag when appropriate, "
        "ensuring they are never overused."
    )

    llm = character["agent_config"]["agent_settings"]["basic_memory_agent"]
    llm["llm_provider"] = "openai_compatible_llm"

    llm_cfg = character["agent_config"]["llm_configs"]["openai_compatible_llm"]
    llm_cfg["base_url"] = os.getenv("CLIPROXY_BASE_URL", "http://localhost:8317/v1")
    llm_cfg["llm_api_key"] = os.getenv("CLIPROXY_API_KEY", "YOUR_CLIPROXY_API_KEY")
    llm_cfg["model"] = os.getenv("CLIPROXY_MODEL", "gemini-3-flash-preview")

    tts_conf = character["tts_config"]
    tts_conf["tts_model"] = "qwen3_tts"
    qwen = tts_conf["qwen3_tts"]
    qwen["base_url"] = os.getenv("QWEN_TTS_BASE_URL", "http://127.0.0.1:18117")
    qwen["endpoint"] = "/v1/audio/speech"
    qwen["model_name"] = "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"
    qwen["language"] = os.getenv("QWEN_TTS_LANGUAGE", "english")
    qwen["voice"] = os.getenv("QWEN_TTS_VOICE", "sohee")
    qwen["timeout"] = 180.0
    qwen["max_retries"] = 2
    qwen["retry_delay"] = 0.1
    qwen["fallback_model_name"] = "Qwen/Qwen3-TTS-0.6B"
    qwen["output_format"] = "wav"
    qwen["file_extension"] = "wav"

    CONF_PATH.write_text(
        yaml.safe_dump(conf, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    print(f"Updated local config: {CONF_PATH}")


if __name__ == "__main__":
    main()
