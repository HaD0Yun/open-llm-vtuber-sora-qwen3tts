# Sora + Qwen3-TTS Quickstart

⚠️ **중요: AI (LLM)은 직접 준비하세요**

이 가이드는 Qwen3-TTS 음성 엔진 설정만 다룹니다. **LLM (AI 대화 엔진)은 사용자가 직접 준비해야 합니다.**
- OpenAI API, Ollama, vLLM, Claude 등 자신의 AI 백엔드를 준비하세요
- OpenAI-compatible API endpoint가 있어야 합니다

설정할 스택:
- Open-LLM-VTuber web server
- **당신의 LLM 백엔드** (직접 준비 required)
- Qwen3-TTS bridge (0.6B, GPU bf16)

## 1) Clone and install

```bash
git clone https://github.com/HaD0Yun/open-llm-vtuber-sora-qwen3tts.git
cd open-llm-vtuber-sora-qwen3tts
uv sync
```

## 2) (Optional) Import March7 Live2D model

The repository does not include third-party Live2D assets.

If you have an extracted March7 model folder, import it:

```bash
python3 scripts/import_march7_model.py "/absolute/path/to/March 7th"
```

If March7 is not imported, the setup still works with available model defaults.

## 3) Set runtime environment values

```bash
# 🔴 REQUIRED: Set your own LLM backend (AI는 알아서 준비하세요)
export LLM_BASE_URL="YOUR_LLM_ENDPOINT"      # e.g., https://api.openai.com/v1
export LLM_API_KEY="YOUR_API_KEY"            # Your API key
export LLM_MODEL="gpt-4o-mini"               # Model name

# Qwen3-TTS settings (로컬에서 실행됨)
export QWEN_TTS_BASE_URL="http://127.0.0.1:18117"
export QWEN_TTS_LANGUAGE="korean"
export QWEN_TTS_VOICE="sohee"
```

## 4) Start everything

```bash
bash scripts/start_sora_stack.sh
```

`start_sora_stack.sh` will automatically:
- install a persistent `qwen-tts` runtime via `uv tool install qwen-tts` (first run only)
- install `flash-attn` into that runtime
- start Qwen3-TTS bridge with `--enable-flash-attn`
- start Open-LLM-VTuber server

Open:

`http://127.0.0.1:12393`

## 5) Stop everything

```bash
bash scripts/stop_sora_stack.sh
```

## Notes

- `conf.yaml` is local-only and ignored by git in this project.
- TTS bridge default model: `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice`.
- Recommended GPU mode in this setup is bf16 for stability.
- If no audio is heard, first check:
  - `logs/olv_server.log`
  - `logs/qwen3tts_bridge.log`
