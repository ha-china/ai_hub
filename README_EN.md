<h1 align="center">AI Hub · One-Stop Free AI Services</h1>
<p align="center">
  To let you experience a variety of free AI services, this integration does not support any paid models or services. However, you may need to register for accounts or create API keys.<br>
  <strong>Acknowledgements:</strong> We stand on the shoulders of giants. Without <a href="https://github.com/knoop7" target="_blank">knoop7</a> and <a href="https://github.com/hasscc/hass-edge-tts" target="_blank">hasscc/hass-edge-tts</a>, this integration would not exist. Sincere thanks!
</p>
<p align="center">
  <a href="https://github.com/ha-china/ai_hub/releases"><img src="https://img.shields.io/github/v/release/ha-china/ai_hub" alt="GitHub Version"></a>
  <a href="https://github.com/ha-china/ai_hub/issues"><img src="https://img.shields.io/github/issues/ha-china/ai_hub" alt="GitHub Issues"></a>
  <img src="https://img.shields.io/github/forks/ha-china/ai_hub?style=social" alt="GitHub Forks">
  <img src="https://img.shields.io/github/stars/ha-china/ai_hub?style=social" alt="GitHub Stars"> <a href="README_EN.md">English</a>
</p>

---

AI Hub is a custom integration for Home Assistant, providing native integration with Zhipu large models:
- Conversation Assistant: Acts as an Assist conversation agent, supporting streaming replies, smart home control tool invocation, and image understanding.
- AI Task: Generates structured data and images (CogView series).
- Text-to-Speech (TTS): Integrates Edge TTS, supporting high-quality voice synthesis (multiple voices, styles, and parameters).
- Speech-to-Text (STT): Integrates SiliconFlow for speech recognition, delivering fast and accurate voice-to-text.
- Integrated Services: Image analysis, image generation, TTS playback, STT transcription.
- AI Automation (experimental): Generate and write automations.yaml using natural language, auto-reload on change.
- HACS Integration Localization: Automatically translate English translation files of custom integrations to Chinese using Zhipu AI.
- WeChat Message Push: Integrate with Bemfa Cloud to send device status notifications via WeChat.
> Note: This integration requires an internet connection, so your network and device performance will affect your experience.

## Features

### Conversation Assistant
- Streaming output: Real-time display of model replies.
- Home control: Connects to Home Assistant LLM API; models can invoke device control/query tools.
- Image understanding: Automatically switch to vision model when messages include images (preferably the free and more powerful GLM-4.1V-Thinking).
- Context memory: Configurable number of history messages to balance performance and effect.
- Optional web search: Advanced mode supports enabling the web_search tool.

### AI Task
- Structured data generation: Specify JSON schema (error prompt on failure).
- Image generation: Connects to images/generations, supports URL or base64 output, and all responses are unified as PNG.
- Attachment support: Reuses the conversation message format to facilitate multimodal tasks.

### Text-to-Speech (TTS, Edge TTS)
- Integrates Edge TTS, supporting multiple languages, styles, and types of voice synthesis.
- Rich voice models (e.g., Xiaoxiao, Yunyang, Yunjian, Aria, Jenny, Guy, etc.).
- Adjustable parameters like speed, volume, pitch, and style.
- Supports both streaming and non-streaming output: chunked on demand or complete audio at once.
- Default output is WAV (also supports PCM/MP3/OGG and other Edge TTS formats).

### Speech-to-Text (STT, SiliconFlow)
- Integrates highly compatible SiliconFlow speech recognition services.
- Supports WAV uploads (recommended 16k/16bit mono; auto-standardized).
- Supports Mandarin/English and other mainstream languages, with automatic detection.
- Supports streaming and non-streaming recognition: real-time text concatenation, low latency.
- Suitable for real-time voice control and automation scenarios.

### Configuration & Management
- Recommended/Advanced modes: Recommended parameters for hassle-free use by default; advanced mode exposes model and tuning options.
- Subentries: Manage Conversation / AI Task / TTS / STT parameters separately under one integration.

## Installation

### Method 1: HACS (Recommended)
1. Search and install "ai_hub" in HACS.
2. Restart Home Assistant.

### Method 2: Manual Installation
1. Copy the `custom_components/ai_hub` directory from the repository to the `custom_components/` directory in your Home Assistant config.
2. Restart Home Assistant.

Note: This integration depends on the new Conversation/AI Task/subentry framework. It is recommended to use a recent version of Home Assistant (>2025.8.0).

## Quick Start (Setup Wizard)
1. Go to Settings → Devices & Services → Integrations → Add Integration, search for "Zhipu Qingyan (ai_hub)".
2. Follow the prompts and input your Zhipu API Key (available [here](https://open.bigmodel.cn/usercenter/apikeys)).
   - If you don’t have a Zhipu account, you can [register here](https://www.bigmodel.cn/claude-code?ic=19ZL5KZU1F).
3. Input your SiliconFlow API Key when prompted.
   - If you don’t have a SiliconFlow account, you can [register here](https://cloud.siliconflow.cn/i/U3e0rmsr); registering via the invite link provides you with a balance bonus.
3. Edge TTS does not require a separate API Key; it uses Microsoft’s official free service (with daily quotas).
4. After setup, four subentries will be automatically created:
   - Conversation Assistant (conversation)
   - AI Task (ai_task_data)
   - Text-to-Speech (tts, Edge TTS)
   - Speech-to-Text (stt, SiliconFlow)
5. To adjust parameters, click "Configure" in the corresponding subentry for recommended/advanced settings.

## User Guide

### A. Conversation Assistant (Assist Conversation Agent)
- In the Assist conversation page, switch the current agent to "Zhipu Conversation Assistant".
- Say/type directly: "Turn on the living room light to 60%" or "Summarize today's schedule for me".
- Attach images: Upload or reference images in supported frontends, and the model will perform visual analysis and respond automatically.
- Tool invocation: Enable LLM Hass API in the subentry to allow the model to control devices or query status via Home Assistant tools.

### B. AI Task (Structured Data)
- Call the AI Task to generate data in a card or automation:
  - Text → Structured JSON: After defining the schema, the system will attempt to parse the reply as JSON.
  - If parsing fails, an error will be returned to facilitate tuning or retrying.

### C. AI Task (Image Generation)
- Use the `ai_hub.generate_image` service to generate images (CogView):
  - Params: prompt (required), size (default 1024x1024), model (default cogview-3-flash).
  - Returns: image_url or image_base64 (internally converted to PNG for frontend/card use).

### D. Image Analysis Service (Image Understanding)
- Use the `ai_hub.analyze_image` service:
  - Params: either image_file or image_entity, message (description), model (default glm-4v-flash).
  - Supports stream (streaming) for incremental output.

### E. Text-to-Speech (TTS Entity & Service, Edge TTS)
- As a TTS entity, select "Edge TTS" in the frontend and enter text to play.
- Or call the `ai_hub.tts_speech` service:
  - Params: text, voice (e.g., zh-CN-XiaoxiaoNeural, see Edge online voice list), rate (speed), volume, pitch, style (expression), format (audio format, e.g. audio-16khz-32kbitrate-mono-mp3), stream (streaming).
  - Non-streaming: Returns complete audio directly; streaming: returns audio chunks which are automatically combined.

### F. Speech-to-Text (STT Entity & Service, SiliconFlow)
- As an STT entity: Audio collected from the frontend/microphone is standardized to WAV and uploaded to SiliconFlow STT.
- Or call the `ai_hub.stt_transcribe` service:
  - Params: audio_file (WAV), language (default zh), stream.
  - Returns: recognized text (for streaming, concatenated until [DONE]).

## Parameters & Models (Defaults & Recommendations)
- Conversation (default):
  - Model: GLM-4-Flash-250414
  - temperature: 0.3, top_p: 0.5, top_k: 1, max_tokens: 250, history: 30
- AI Tasks (default):
  - Text model: GLM-4-Flash-250414 (temperature 0.95 / top_p 0.7 / max_tokens 2000)
  - Image model: cogview-3-flash (size defaults to 1024x1024)
- Vision model: GLM-4.1V-Thinking (stronger free model)
- TTS default: Built-in Edge TTS, recommended voice zh-CN-XiaoxiaoNeural, format audio-16khz-32kbitrate-mono-mp3, rate 1.0, volume 1.0, stream true
- STT default: Uses SiliconFlow, language zh, stream true

## Contributing
You are welcome to submit Issues and PRs to help improve features and documentation:
- Code & Docs: https://github.com/ha-china/ai_hub
- Bug Reports: https://github.com/ha-china/ai_hub/issues

## License
This project is published under the LICENSE in the repository.