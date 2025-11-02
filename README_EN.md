<h1 align="center">AI Hub · One-stop Free AI Services</h1>
<p align="center">
  To let you experience a variety of free AI services, this integration does not support any paid models or services. Of course, you may need to create accounts or generate API Keys.<br>
  <strong>Special Thanks:</strong> "We enjoy the shade of trees planted by our predecessors". Without <a href="https://github.com/knoop7" target="_blank">knoop7</a> and <a href="https://github.com/hasscc/hass-edge-tts" target="_blank">hasscc/hass-edge-tts</a>, this integration would not exist. Thank you!
</p>

</p>
<p align="center">
  <a href="https://github.com/ha-china/ai_hub/releases"><img src="https://img.shields.io/github/v/release/ha-china/ai_hub" alt="GitHub Version"></a>
  <a href="https://github.com/ha-china/ai_hub/issues"><img src="https://img.shields.io/github/issues/ha-china/ai_hub" alt="GitHub Issues"></a>
  <img src="https://img.shields.io/github/forks/ha-china/ai_hub?style=social" alt="GitHub Forks">
  <img src="https://img.shields.io/github/stars/ha-china/ai_hub?style=social" alt="GitHub Stars"> <a href="README_EN.md">English</a>
</p>

---
## Prerequisites
- Home Assistant 2025.8.0 or later
- HACS 4.0 or later (recommended)
- You will need the appropriate API Keys to use the respective services; if you don't have them, please register using the following links:
- Zhipu API Key (for Conversation, AI Task, TTS, STT) [Register](https://www.bigmodel.cn/claude-code?ic=19ZL5KZU1F)
- SiliconFlow API Key (for Speech Recognition) [Register](https://cloud.siliconflow.cn/i/U3e0rmsr)
- Bemfa (for WeChat Message Push) [Register](http://www.cloud.bemfa.com/u_register.php)

AI Hub is a custom integration for Home Assistant, offering native connections to Zhipu, SiliconFlow, and Bemfa:
- Conversation: Works as an Assist conversation agent, supports streaming replies, home control tool calling, and image understanding.
- AI Task: Generate structured data and images (CogView series).
- Text-to-Speech (TTS): Integrated with Edge TTS, supporting high-quality speech synthesis (multi-voice, multi-style, multi-parameter).
- Speech-to-Text (STT): Integrated with SiliconFlow speech recognition, providing fast and accurate speech-to-text.
  > Free models do not support streaming, so speed may be average unless your local machine cannot handle it or you do not want to use paid models.
- Integrated Services: Image analysis, image generation, TTS playback, STT transcription.
- HACS Integration Localization: Automatically translates the custom integration's en.json to Chinese using Zhipu AI.
  > If zh-Hans.json already exists in the integration, it will not auto-translate, even if its contents are in English.
- WeChat Message Push: Integrates Bemfa service to send device status notifications via WeChat.
  > Note: This integration fully depends on the internet, so your network and device performance will determine the experience.
## Features

### Conversation
- Streaming output: Real-time display of model responses.
- Home control: Connected to Home Assistant LLM API, allowing models to call tools for control and query.
- Image understanding: When a message contains an image, the visual model is used automatically (priority to free and powerful GLM-4.1V-Thinking).
- Context memory: Number of history messages is configurable to balance effect and performance.
- Optional web search: Advanced mode can enable the web_search tool.

### AI Task
- Structured data generation: Specify a JSON structure (error provided on failure).
- Image generation: Uses images/generations, supports URL or base64 output, standardized as PNG.
- Attachment support: Reuses the conversation message format for multimodal tasks.

### Text-to-Speech (TTS, Edge TTS)
- Integrated Edge TTS, supporting multiple languages, styles, and voice types.
- Rich voice models (Xiaoxiao, Yunyang, Yunjian, Aria, Jenny, Guy, etc.).
- Adjustable speed, volume, pitch, and style.
- Supports streaming and non-streaming: either segmented or full audio returned.
- Default output is WAV (supports PCM/MP3/OGG and other Edge TTS formats).

### Speech-to-Text (STT, SiliconFlow)
- Integrates high-compatibility SiliconFlow speech recognition service.
- Supports uploading WAV files (16k/16bit mono recommended, automatically standardized).
- Supports mainstream languages like Mandarin/English, auto-detected.
- Non-streaming recognition supported.
- Suitable for real-time voice control, automation, and more.

### HACS Integration Localization
- Automatically translates the en.json of custom integrations to Chinese, improving user experience.
- High-quality translation with Zhipu AI, batch processing of multiple components.
- Allows custom component directory path configuration for flexible installations.

### WeChat Message Push (Wechat, Bemfa)
- Integrates Bemfa to send device status notifications via WeChat.
- Supports sending text and image messages for diverse notification needs.
- Easy configuration; just obtain your Bemfa device topic.

### Configuration & Management
- Recommended/Advanced dual modes: Default recommended parameters for plug-and-play; advanced mode exposes model selection and tuning.
- Subentries: Manage Conversation / AI Task / TTS / STT / WeChat Message Push services under one integration.

## Installation

### Method 1: HACS (Recommended)
1. Search and install "ai_hub" in HACS.
2. Restart Home Assistant.

### Method 2: Manual Installation
1. Copy the `custom_components/ai_hub` directory from the repository to your Home Assistant `custom_components/` directory.
2. Restart Home Assistant.

Note: This integration depends on the new Conversation/AI Task/Subentry framework; a newer version of Home Assistant (>2025.8.0) is recommended.

## Quick Start (Configuration Wizard)
1. Go to Settings → Devices & Services → Integrations → Add Integration, and search for "AI HUB (ai_hub)".
2. Enter your Zhipu API Key as guided ([get it here](https://open.bigmodel.cn/usercenter/apikeys)).
3. Enter your SiliconFlow API Key as guided.
4. Enter your Bemfa device topic as guided ([get it here](https://cloud.bemfa.com/tcp/index.html)).
5. Edge TTS does not require a separate API Key; it uses the official Microsoft free interface.
6. To adjust parameters, click "Configure" in the relevant subentry to enter recommended/advanced configuration.

## User Guide

### A. Conversation (Assist Conversation Agent)
- In the Assist conversation page, set the agent to "AI HUB Conversation Assistant".
- Example commands: "Turn on the living room light to 60%", "Summarize today's schedule".
- Attach an image: Upload or reference an image in the supported frontend, and the model will automatically analyze and reply.
- Tool calls: After enabling LLM Hass API in the subentry, models can use Home Assistant tools to control devices/query status.

### B. AI Task (Structured Data)
- In cards or automations, call AI Task to generate data:
  - Text → structured JSON: Define the structure, and the system will attempt to parse the reply as JSON.
  - On failure, errors are returned to help with tuning or retry.

### C. AI Task (Image Generation)
- Use the `ai_hub.generate_image` service to generate images (CogView):

### D. Service Calls

AI Hub provides various services accessible via Developer Tools > Services:

#### Image Generation (`ai_hub.generate_image`)
- **Description**: Use Zhipu AI CogView model to generate an image
- **Parameters**: 
  - `prompt`: image description (required)
  - `size`: image size (optional, default 1024x1024)
  - `model`: model selection (optional, default cogview-3-flash)

#### Image Analysis (`ai_hub.analyze_image`)
- **Description**: Use AI HUB to analyze image content
- **Parameters**:
  - `image_file`: image file path
  - `image_entity`: camera entity ID
  - `message`: analysis instruction (required)
  - `model`: model selection (optional)
  - `temperature`: temperature (optional)
  - `max_tokens`: max tokens (optional)

#### Text-to-Speech (`ai_hub.tts_speech`)
- **Description**: Use Zhipu to convert text to speech
- **Parameters**:
  - `text`: text content (required)
  - `voice`: voice type (optional, female/male)
  - `speed`: speed (optional)
  - `volume`: volume (optional)
  - `media_player_entity`: media player entity ID (optional)

#### Speech-to-Text (`ai_hub.stt_transcribe`)
- **Description**: Use SiliconFlow to convert audio to text
- **Parameters**:
  - `file`: audio file path (required)
  - `model`: STT model selection (optional)

#### Create Automation (`ai_hub.create_automation`)
- **Description**: Create a Home Assistant automation via natural language
- **Parameters**:
  - `description`: automation description (required)
  - `name`: automation name (optional)
  - `area_id`: area ID (optional)

#### Translate Components (`ai_hub.translate_components`)
- **Description**: Translate all custom integration English translations to Chinese
- **Parameters**:
  - `custom_components_path`: custom components directory path (optional, default custom_components)

#### Send WeChat Message (`ai_hub.send_wechat_message`)
- **Description**: Send WeChat notifications via Bemfa
- **Parameters**:
  - `device_entity`: entity ID to monitor (required)
  - `message`: message content (required)
  - `group`: message group (optional)
  - `url`: link address (optional)
  - Parameters: prompt (required), size (default 1024x1024), model (default cogview-3-flash)
  - Returns: image_url or image_base64 (auto-converted internally to PNG for frontend/card use)

### D. Image Analysis Service (Image Understanding)
- Use the `ai_hub.analyze_image` service:
  - Parameters: image_file or image_entity (choose one), message (analysis instructions), model (default glm-4v-flash)
  - Supports `stream` for incremental streaming results.

### E. Text-to-Speech (TTS Entity & Service, Edge TTS)
- As a TTS entity, select "Edge TTS" in the frontend and enter text to play.
- Or call the `ai_hub.tts_speech` service:
  - Parameters: text, voice (e.g. zh-CN-XiaoxiaoNeural, see Edge voice list for details), rate (speed), volume, pitch, style, format (e.g. audio-16khz-32kbitrate-mono-mp3), stream (streaming)
  - Non-streaming: full audio returned; streaming: audio fragments returned and automatically concatenated into complete audio.

### F. Speech-to-Text (STT Entity & Service, SiliconFlow)
- As an STT entity: audio collected via frontend/mic will be standardized to WAV and uploaded to SiliconFlow STT.
- Or call the `ai_hub.stt_transcribe` service:
  - Parameters: audio_file (WAV), language (default zh), stream.
  - Returns: recognized text (streaming will append until [DONE]).

## Parameters and Models (Defaults & Recommendations)
- Conversation (default):
  - Model: GLM-4-Flash-250414
  - temperature: 0.3, top_p: 0.5, top_k: 1, max_tokens: 250, history: 30
- AI Task (default):
  - Text model: GLM-4-Flash-250414 (temperature 0.95 / top_p 0.7 / max_tokens 2000)
  - Image model: cogview-3-flash (size default 1024x1024)
- Visual model: GLM-4.1V-Thinking (more powerful free model)
- TTS default: Integrated Edge TTS, recommended voice zh-CN-XiaoxiaoNeural, format audio-16khz-32kbitrate-mono-mp3, rate 1.0, volume 1.0, stream true
- STT default: SiliconFlow, language zh, stream true

## Contributing
Issues and PRs are welcome to improve features and documentation:
- Code & Docs: https://github.com/ha-china/ai_hub
- Issue Tracker: https://github.com/ha-china/ai_hub/issues

## License
This project is released under the LICENSE file in the repository.