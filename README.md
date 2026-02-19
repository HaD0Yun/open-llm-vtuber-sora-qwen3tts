![](./assets/banner.jpg)

<h1 align="center">🐚 Sora - AI Companion</h1>
<h3 align="center">Voice-Interactive AI Character Powered by Qwen3-TTS</h3>

<p align="center">
  <a href="#-what-is-sora">
    <img src="https://img.shields.io/badge/Character-Sora-pink?style=for-the-badge&logo=openai&logoColor=white" alt="Sora Character"/>
  </a>
  <a href="#-qwen3-tts-integration">
    <img src="https://img.shields.io/badge/TTS-Qwen3--TTS-blue?style=for-the-badge&logo=amazon-aws&logoColor=white" alt="Qwen3-TTS"/>
  </a>
  <a href="#-features">
    <img src="https://img.shields.io/badge/Platform-Cross--Platform-green?style=for-the-badge&logo=linux&logoColor=white" alt="Cross Platform"/>
  </a>
</p>

<p align="center">
  <b>소라</b>는 실시간 음성 대화와 Live2D 아바타를 갖춘 AI 캐릭터입니다.<br/>
  <b>Sora</b> is a voice-interactive AI companion with real-time conversations and Live2D avatar.
</p>

<p align="center">
  <a href="./doc/SORA_QWEN3TTS_QUICKSTART.md">🚀 Quick Start (Sora + Qwen3-TTS)</a> | 
  <a href="#-features">✨ Features</a> | 
  <a href="#-what-is-sora">🐚 About Sora</a>
</p>

---

## 🐚 What is Sora?

**Sora (소라)** is your personal AI companion — a unique character brought to life through advanced voice interaction technology. Unlike generic AI assistants, Sora features:

- 🎭 **Distinctive Persona** — Sora has her own personality, expressions, and way of interacting
- 🎨 **Live2D Avatar** — Beautiful animated character that responds to your touch and voice
- 🗣️ **Natural Voice** — Powered by **Qwen3-TTS** for lifelike, emotionally expressive speech
- 👁️ **Visual Perception** — Sora can see you through camera and observe your screen
- 💝 **Emotional Connection** — Designed for meaningful, ongoing conversations

Whether you want a virtual companion, study partner, or just someone to talk to, Sora is there for you.

### 👀 Demo
| ![](assets/i1.jpg) | ![](assets/i2.jpg) |
|:---:|:---:|
| ![](assets/i3.jpg) | ![](assets/i4.jpg) |

---

## 🔊 Qwen3-TTS Integration

This project features seamless integration with **Qwen3-TTS (Alibaba's state-of-the-art text-to-speech model)**:

- 🎯 **Local GPU Acceleration** — Runs entirely on your hardware with bf16 precision
- 🌍 **Multilingual Support** — Natural speech in multiple languages including Korean, English, Chinese, Japanese
- 🎵 **Voice Cloning** — Customize Sora's voice to your preference
- ⚡ **Real-time Generation** — Low-latency streaming for natural conversations
- 🎛️ **Voice Options** — Multiple voice presets (including "sohee", "xiaoming", etc.)

The Qwen3-TTS bridge runs locally at \`http://127.0.0.1:18117\` with the \`Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice\` model.

---

## ✨ Features & Highlights

### 🎯 Core Experience
- 🖥️ **Cross-platform**: macOS, Linux, Windows — runs on NVIDIA GPU, Apple Silicon, or CPU
- 🔒 **100% Offline**: Complete privacy — no cloud dependencies for core features
- 💻 **Dual Mode**: Web browser or desktop pet mode (transparent background, always on top)
- 🌏 **Korean Optimized**: Enhanced support for Korean language conversations

### 🎤 Advanced Voice Features
- 🎙️ **Real-time Voice Chat** — Natural back-and-forth conversations
- 🎵 **Voice Interruption** — Talk over Sora naturally (no headphone feedback issues)
- 🫱 **Touch Interaction** — Click and drag Sora's avatar to interact
- 😊 **Expression Control** — Sora shows emotions through Live2D animations
- 💭 **Inner Thoughts** — See what Sora is thinking before she speaks
- 🗣️ **Proactive Speaking** — Sora initiates conversation when appropriate

### 🧠 AI & Speech Stack
- 🤖 **LLM Backend**: OpenAI-compatible API support (cliproxy, Ollama, vLLM, etc.)
- 🔊 **TTS**: **Qwen3-TTS** (primary), with fallback to Edge TTS, CosyVoice, GPT-SoVITS
- 🎙️ **ASR**: FunASR, Faster-Whisper, Whisper.cpp, Azure ASR
- 🎛️ **VAD**: Silero VAD for precise voice detection

### 🎨 Customization
- ⚙️ **Character Config**: Modify Sora's personality via prompt editing
- 🎨 **Live2D Models**: Import custom models (includes March 7th support)
- 🎵 **Voice Cloning**: Train custom voices for unique speech patterns
- 🧩 **Modular Design**: Easy to swap LLM, TTS, ASR components

---

## 🚀 Quick Start

### ⚡ Quick Start

> **🤖 AI (LLM) 설정은 직접 하세요**
> 
> 이 프로젝트는 AI 응답을 생성하는 LLM 백엔드를 제공하지 않습니다. OpenAI API, Ollama, vLLM 등 **자신의 AI를 직접 준비하고 연결**해야 합니다.

```bash
# 1. Clone this repository
git clone https://github.com/HaD0Yun/open-llm-vtuber-sora-qwen3tts.git
cd open-llm-vtuber-sora-qwen3tts

# 2. Install dependencies
uv sync

# 3. Set your own AI backend (LLM은 알아서 준비하세요)
export LLM_BASE_URL="YOUR_LLM_URL"        # e.g., https://api.openai.com/v1
export LLM_API_KEY="YOUR_API_KEY"         # Your OpenAI/Ollama/etc API key
export QWEN_TTS_BASE_URL="YOUR_TTS_URL"   # Qwen3-TTS server URL

# 4. Start
bash scripts/start_sora_stack.sh
```

Then open: **http://127.0.0.1:12393**

📖 **Detailed Setup**: [`doc/SORA_QWEN3TTS_QUICKSTART.md`](./doc/SORA_QWEN3TTS_QUICKSTART.md)

---

## 🎭 Character: Sora

Sora is designed to be a warm, engaging companion with her own unique personality:

- 💫 **Cheerful and Curious** — Always eager to learn about you and the world
- 🤗 **Supportive** — Offers encouragement and emotional support
- 🎨 **Expressive** — Shows emotions through Live2D animations and voice tone
- 🌟 **Attentive** — Remembers your conversations and builds rapport over time

### Default Configuration
The default Sora configuration includes:
- Optimized prompts for natural Korean conversation
- Qwen3-TTS voice settings tuned for emotional expression
- Live2D expression mappings for common emotions
- Visual perception enabled for screen/camera awareness

---

## ⚙️ Technical Architecture

Sora is built on a modular, extensible architecture:

\`\`\`
┌─────────────────────────────────────────────────────────────┐
│                      Sora AI Companion                       │
├─────────────────────────────────────────────────────────────┤
│  🎭 Character Layer                                          │
│     • Persona: Sora (소라)                                    │
│     • Avatar: Live2D animated model                          │
│     • Memory: Persistent chat history                        │
├─────────────────────────────────────────────────────────────┤
│  🧠 AI Engine Layer                                          │
│     • LLM: OpenAI-compatible API (cliproxy default)          │
│     • TTS: Qwen3-TTS (local GPU)                             │
│     • ASR: FunASR / Whisper                                  │
│     • VAD: Silero                                            │
├─────────────────────────────────────────────────────────────┤
│  💻 Runtime Layer                                            │
│     • Web Interface (port 12393)                             │
│     • WebSocket server for real-time communication           │
│     • Desktop pet mode (transparent overlay)                 │
└─────────────────────────────────────────────────────────────┘
\`\`\`

---

## 📋 Requirements

### Minimum
- **OS**: Windows 10/11, macOS 12+, Ubuntu 20.04+
- **RAM**: 8GB
- **Storage**: 10GB free space
- **GPU**: Optional (CPU mode available)

### Recommended (for Qwen3-TTS)
- **GPU**: NVIDIA GPU with 8GB+ VRAM
- **RAM**: 16GB
- **CUDA**: 11.8+ or 12.1+

### Software
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager
- (Optional) [cliproxy](https://github.com/foldl/chatllm-cli) for LLM backend

---

## 🔧 Configuration

Main configuration file: \`conf.yaml\` (created on first run)

Key settings for Sora:
\`\`\`yaml
character_config:
  character_name: "sora"
  persona_prompt: "You are Sora, a friendly AI companion..."

tts_config:
  tts_model: "qwen3tts"
  base_url: "http://127.0.0.1:18117"
  language: "korean"
  voice: "sohee"
\`\`\`

See \`config_templates/conf.default.yaml\` for all options.

---

## 🆘 Troubleshooting

### No Audio Output
- Check \`logs/olv_server.log\` and \`logs/qwen3tts_bridge.log\`
- Verify Qwen3-TTS bridge is running: \`curl http://127.0.0.1:18117/health\`
- Ensure GPU drivers are up to date

### High Latency
- Enable flash-attention: Already enabled in \`start_sora_stack.sh\`
- Use GPU mode instead of CPU
- Check system resource usage

### Character Not Loading
- Verify Live2D model files are in \`live2d-models/\`
- Check browser console for JavaScript errors

---

## 🤝 Powered by Open-LLM-VTuber

Sora is built on top of the excellent [Open-LLM-VTuber](https://github.com/Open-LLM-VTuber/Open-LLM-VTuber) framework, which provides:

- 🏗️ Modular architecture for LLM/TTS/ASR components
- 🎨 Live2D rendering and animation system
- 🌐 WebSocket-based real-time communication
- 🖥️ Cross-platform desktop and web interfaces

Huge thanks to the Open-LLM-VTuber team and contributors for creating this foundation!

[![Contributors](https://contrib.rocks/image?repo=Open-LLM-VTuber/Open-LLM-VTuber)](https://github.com/Open-LLM-VTuber/Open-LLM-VTuber/graphs/contributors)

---

## 📜 License

This project inherits the MIT license from Open-LLM-VTuber.

### Third-Party Licenses

#### Live2D Sample Models
This project may include Live2D sample models provided by Live2D Inc. These assets are licensed separately under the [Live2D Free Material License Agreement](https://www.live2d.jp/en/terms/live2d-free-material-license-agreement/) and [Terms of Use](https://www.live2d.com/eula/live2d-sample-model-terms_en.html).

#### Qwen3-TTS
Qwen3-TTS is developed by Alibaba Cloud. Please refer to their license terms when using the TTS model.

---

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=HaD0Yun/open-llm-vtuber-sora-qwen3tts&type=Date)](https://star-history.com/#HaD0Yun/open-llm-vtuber-sora-qwen3tts&Date)

---

<p align="center">
  Made with 💝 for Sora (소라)<br/>
  <sub>Powered by Qwen3-TTS & Open-LLM-VTuber</sub>
</p>
