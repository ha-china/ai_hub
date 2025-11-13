<h1 align="center">AI Hub · One-stop Free AI Services</h1>
<p align="center">
  To enable you to experience a variety of free AI services, this integration does not support any paid models or services. You may need to sign up for accounts or create API Keys.<br>
  <strong>Acknowledgements:</strong> We stand on the shoulders of giants. Without the projects <a href="https://github.com/knoop7" target="_blank">knoop7</a> and <a href="https://github.com/hasscc/hass-edge-tts" target="_blank">hasscc/hass-edge-tts</a>, this integration would not exist. Our sincere thanks!
</p>

<p align="center">
  <a href="https://github.com/ha-china/ai_hub/releases"><img src="https://img.shields.io/github/v/release/ha-china/ai_hub" alt="GitHub Version"></a>
  <a href="https://github.com/ha-china/ai_hub/issues"><img src="https://img.shields.io/github/issues/ha-china/ai_hub" alt="GitHub Issues"></a>
  <img src="https://img.shields.io/github/forks/ha-china/ai_hub?style=social" alt="GitHub Forks">
  <img src="https://img.shields.io/github/stars/ha-china/ai_hub?style=social" alt="GitHub Stars"> <a href="README_EN.md">English</a>
</p>

---

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Features Overview](#features-overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Account Registration & Token Retrieval](#account-registration--token-retrieval)
- [User Guide](#user-guide)
- [Service API Details](#service-api-details)
- [Configuration Parameters](#configuration-parameters)
- [Notes](#notes)
- [Troubleshooting](#troubleshooting)
- [Contribution](#contribution)
- [License](#license)

---

## 🔧 Prerequisites

- **Home Assistant**: 2025.8.0 or later
- **Network Requirement**: This integration relies entirely on online services; a stable internet connection is required.

## 🌟 Features Overview

AI Hub is a custom integration for Home Assistant, offering native support for Zhipu AI, SiliconFlow, and Bemfa services.

If you do not need certain entries, simply leave the API key blank or remove them; you can add them again if needed in the future.

### Core Features

#### 🗣️ Conversation Assistant
- **Streaming Output**: Instantly displays model responses for a smooth chat experience.
- **Home Control**: Integrates with Home Assistant LLM API to control/query devices.
- **Image Understanding**: Automatically switches to vision model (GLM-4.1V-Thinking) when a message contains an image.
- **Context Memory**: Configurable history length to balance effectiveness and performance.

#### 🤖 AI Tasks
- **Structured Data Generation**: Outputs JSON structures as specified; provides error tips on failure.
- **Image Generation**: Uses CogView series for image generation; supports URL or base64 output.
- **Multimodal Support**: Reuses conversation message format for complex task processing.

#### 🔊 Text-to-Speech (TTS, Edge TTS)
- **High-Quality Speech**: Integrates Microsoft Edge TTS, supporting multiple languages and styles.
- **Rich Voice Library**: Supports Xiaoxiao, Yunjian, Aria, Jenny, and many other voices.
- **Adjustable Parameters**: Tune speech rate, volume, pitch, style, etc.
- **Multiple Formats**: Outputs audio in WAV/MP3/OGG formats.

#### 🎤 Speech-to-Text (STT, SiliconFlow)
- **High Accuracy Recognition**: Integrates SiliconFlow STT services.
- **Multilingual Support**: Supports automatic detection of Mandarin, English, and more.
- **Format Compatibility**: Supports WAV/MP3/FLAC and other audio formats.
- **Real-Time Processing**: Ideal for voice control and automation.

#### 🌐 HACS Component Localization
- **Auto Translation**: Uses Zhipu AI to translate custom component English translation files to Chinese.
- **Batch Processing**: Batch localization of multiple components supported.
- **Smart Detection**: Automatically detects components that need translation, skipping those already localized.

#### 📱 WeChat Push Notifications (Bemfa)
- **Real-Time Alerts**: Integrates Bemfa cloud, sends device status notifications via WeChat.


---

## 📦 Installation

### Option 1: HACS Installation (Recommended)

1. **Open HACS**: In Home Assistant, go to HACS → Integrations.
2. **Search for Integration**: Click "Explore & Download Repositories" (top right), search for "ai_hub".
3. **Install Integration**: Find "AI Hub" and click download.
4. **Restart System**: Restart Home Assistant for the integration to take effect.

### Option 2: Manual Installation

1. **Download Files**: Download the latest `ai_hub.zip` from [GitHub Releases](https://github.com/ha-china/ai_hub/releases).
2. **Extract Files**: Extract to `<HA_CONFIG>/custom_components/ai_hub/`.
3. **Restart System**: Restart Home Assistant.

> **Note**: This integration relies on the new Conversation/AI Task/sub-entry framework. Newer Home Assistant versions (after 2025.8.0) are recommended.

---

## 🚀 Quick Start

### Setup Wizard

1. **Add Integration**: Settings → Devices & Services → Integrations → Add Integration. Search for "AI HUB (ai_hub)".
2. **Configure API Keys**: Follow the wizard to set up:
   - Zhipu API Key (for conversation, AI tasks, and HACS translation)
   - SiliconFlow API Key (for STT; free version does not support streaming, so it is a bit slower)
   - Bemfa API Key (for WeChat notifications)
3. **Validate Configuration**: The system will automatically verify the API key validity.
4. **Complete Setup**: The integration will automatically create relevant services and entities.

### Sub-Entry Configuration

AI Hub supports sub-entry configuration for splitting different functionalities:

- **AI Hub Conversation Assistant**: For Assist conversation agent
- **AI Hub AI Tasks**: For image generation and structured data
- **AI Hub TTS**: For text-to-speech
- **AI Hub STT**: For speech-to-text
- **AI Hub WeChat Notification**: For WeChat message push
- **AI Hub Localization**: For component localization

---

## 🔑 Account Registration & Token Retrieval

### Zhipu AI
- **Use**: Conversation, AI tasks, TTS, STT
- **Register**: [Click to Register](https://www.bigmodel.cn/claude-code?ic=19ZL5KZU1F)
- **Get API Key**:
  1. Register and log in
  2. Go to [Console](https://open.bigmodel.cn/usercenter/apikeys)
  3. Click "Create API Key"
  4. Copy the generated API Key

### SiliconFlow
- **Use**: Speech-to-text (STT)
- **Register**: [Click to Register](https://cloud.siliconflow.cn/i/U3e0rmsr)
- **Get API Key**:
  1. Register and log in
  2. Go to the console
  3. Create a new API Key in API Management
  4. Copy the generated API Key

### Bemfa
- **Use**: WeChat message push
- **Register**: [Click to Register](http://www.cloud.bemfa.com/u_register.php)
- **Get Device Topic**:
  1. Register and log in
  2. Go to [TCP Device Management](https://cloud.bemfa.com/tcp/index.html)
  3. Create a new device or use an existing one
  4. Copy the device topic

> **Note**: Edge TTS uses Microsoft's official free API and does not require a separate API Key.

---

## 📖 User Guide

### A. Conversation Assistant Usage

#### Basic Conversation
1. **Switch Agent**: On the Assist conversation page, set agent to "AI Hub Conversation Assistant"
2. **Start Conversation**: Type or say questions, e.g.:
   - "Turn on the living room light to 60%"
   - "Summarize today’s schedule"
   - "Set an alarm for tomorrow at 8 AM"

#### Image Understanding
1. **Upload Image**: Upload an image via supported frontend or select a camera image
2. **Describe the Question**: Enter your question or description regarding the image
3. **Get Analysis**: The model will analyze and reply

#### Tool Usage
- **Enable Tools**: Enable "LLM Hass API" in the assistant sub-entry
- **Device Control**: The model can control and query device status via Home Assistant tools

### B. AI Task Usage

#### Image Generation
Generate images via automation or service call:

```yaml
automation:
  - alias: "Generate Daily Picture"
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - service: ai_hub.generate_image
        data:
          prompt: "Beautiful sunrise landscape"
          size: "1024x1024"
          model: "cogview-3-flash"
```

#### Structured Data Generation
Generate structured data in specified format:

```yaml
# Call AI Task to generate JSON data
service: ai_hub.ai_task
data:
  input: "Generate a JSON with name, age, and occupation"
  model: "GLM-4-Flash-250414"
  temperature: 0.3
```

### C. TTS (Text-to-Speech)

#### Entity Method
1. **Select TTS**: Choose "AI Hub TTS" as the voice service in the media player
2. **Enter Text**: Input text to synthesize
3. **Play Speech**: The system plays the synthesized speech automatically

#### Service Call
```yaml
service: ai_hub.tts_speech
data:
  text: "Welcome to AI Hub voice synthesis"
  voice: "zh-CN-XiaoxiaoNeural"
  rate: "+0%"
  volume: "+0%"
  media_player_entity: media_player.living_room_speaker
```

### D. STT (Speech-to-Text)

#### Entity Method
1. **Select STT**: Choose "AI Hub STT" in microphone settings
2. **Start Recording**: Click record to input speech
3. **Get Text**: The system automatically converts speech to text

#### Service Call
```yaml
service: ai_hub.stt_transcribe
data:
  file: "/config/tmp/recording.wav"
  model: "FunAudioLLM/SenseVoiceSmall"
```

### E. WeChat Message Push

#### Automation
```yaml
automation:
  - alias: "Door Open Notification"
    trigger:
      - platform: state
        entity_id: binary_sensor.front_door
        to: "on"
    action:
      - service: ai_hub.send_wechat_message
        data:
          device_entity: binary_sensor.front_door
          message: "Front door opened, please be aware!"
```

### F. Component Localization

#### Manual Localization
```yaml
service: ai_hub.translate_components
data:
  custom_components_path: "custom_components"  # Optional, default path
  force_translation: false  # Whether to force re-translation
```

---

## 🔧 Service API Details

AI Hub provides various service APIs accessible via the Developer Tools - Services panel:

### Image Generation Service
```yaml
service: ai_hub.generate_image
data:
  prompt: "Image description"  # Required: image prompt
  size: "1024x1024"  # Optional: image size
  model: "cogview-3-flash"  # Optional: model selection
```

### Image Analysis Service
```yaml
service: ai_hub.analyze_image
data:
  image_file: "/path/to/image.jpg"  # Optional: image file path
  image_entity: "camera.front_door"  # Optional: camera entity ID
  message: "Analysis prompt"  # Required: analysis instructions
  model: "glm-4.1v-thinking-flash"  # Optional: model selection
  temperature: 0.3  # Optional: temperature
  max_tokens: 1000  # Optional: max tokens
```

### Text-to-Speech Service
```yaml
service: ai_hub.tts_speech
data:
  text: "Text to convert"  # Required: content
  voice: "zh-CN-XiaoxiaoNeural"  # Optional: voice type
  speed: 1.0  # Optional: rate
  volume: 1.0  # Optional: volume
  media_player_entity: "media_player.speaker"  # Optional: media player entity
```

### Speech-to-Text Service
```yaml
service: ai_hub.stt_transcribe
data:
  file: "/path/to/audio.wav"  # Required: audio file path
  model: "FunAudioLLM/SenseVoiceSmall"  # Optional: model
```

### Create Automation Service
```yaml
service: ai_hub.create_automation
data:
  description: "Describe the automation"  # Required: natural language description
  name: "Automation name"  # Optional: automation name
  area_id: "living_room"  # Optional: area ID
```

### Send WeChat Message Service
```yaml
service: ai_hub.send_wechat_message
data:
  device_entity: "sensor.door_sensor"  # Required: target entity
  message: "Message content"  # Required: content
  group: "Notification group"  # Optional: group
  url: "https://example.com"  # Optional: link
```

### Component Translation Service
```yaml
service: ai_hub.translate_components
data:
  custom_components_path: "custom_components"  # Optional: custom component path
  force_translation: false  # Optional: force translation
  target_component: "custom_component_name"  # Optional: specify component
  list_components: false  # Optional: list components only
```

---

## ⚙️ Configuration Parameters

### Recommended Configuration (Default)

#### Conversation Assistant
- **Model**: GLM-4-Flash-250414
- **Temperature**: 0.3 (controls randomness)
- **Top P**: 0.5 (controls candidate pool)
- **Top K**: 1 (limits candidates)
- **Max Tokens**: 250
- **History Length**: 30 (keeps context consistency)

#### AI Task
- **Text Model**: GLM-4-Flash-250414
- **Image Model**: cogview-3-flash
- **Temperature**: 0.95 (for creativity)
- **Top P**: 0.7
- **Max Tokens**: 2000

#### TTS
- **Default Voice**: zh-CN-XiaoxiaoNeural (Xiaoxiao)
- **Default Format**: audio-16khz-32kbitrate-mono-mp3
- **Rate**: 1.0 (normal)
- **Volume**: 1.0 (normal)
- **Streaming Output**: Enabled

#### STT
- **Default Model**: FunAudioLLM/SenseVoiceSmall
- **Supported Languages**: Chinese (Simplified), English, Japanese, Korean, and 15+ other languages
- **Audio Formats**: WAV, MP3, FLAC, M4A, OGG, WebM
- **Max File Size**: 25MB


---

## ⚠️ Notes

### System Requirements
1. **Network Dependency**: Internet connection is required for this integration.
2. **Performance**: Use a performant device for best speech experience.
3. **Storage**: Temporary storage may be required for speech files.

### Usage Limitations
1. **Free Models**:
   - No streaming output; response speed may be slower.
   - Rate limits apply.
   - Free quotas may be limited.

2. **API Keys**:
   - Please keep your API keys safe and do not expose them.
   - Regularly check API usage to prevent overages.
   - If API errors occur, check if the keys are valid.

3. **Functionality Limits**:
   - Certain advanced features may require newer Home Assistant versions.
   - Image generation and analysis need a reliable network.
   - WeChat push requires following the Bemfa official account.

### Privacy & Security
1. **Data Transmission**: All data is transmitted online to the AI services.
2. **Local Storage**: Speech files may be temporarily stored locally.
3. **API Security**: Please ensure the safety of your API keys.

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. Integration Cannot Be Added
**Possible Causes**:
- Home Assistant version is too low (2025.8.0+ required)
- Network connection problem
- API Keys invalid

**Solutions**:
- Check Home Assistant version
- Make sure the network is working
- Check API keys

#### 2. Conversation Assistant Not Responding
**Possible Causes**:
- Zhipu AI API Key invalid or expired
- Network issues
- Incorrect model selection

**Solutions**:
- Check Zhipu AI API Key
- Test network connectivity
- Ensure a free model is selected

#### 3. TTS Not Playing
**Possible Causes**:
- Edge TTS service unavailable
- Wrong media player selected
- Network issues

**Solutions**:
- Check connection to Microsoft services
- Check status of media player
- Try a different voice model

#### 4. STT Recognition Fails
**Possible Causes**:
- SiliconFlow API Key invalid
- Unsupported audio file format
- File too large

**Solutions**:
- Check SiliconFlow API Key
- Ensure audio format is supported
- Compress audio file

#### 5. WeChat Push Not Working
**Possible Causes**:
- Bemfa device topic configured incorrectly
- Did not follow Bemfa public account
- Network issues

**Solutions**:
- Check if device topic is correct
- Ensure Bemfa official account is followed
- Test network connectivity

### Log Debugging
Refer to Home Assistant logs if you encounter problems:

1. **View Integration Logs**:
   ```
   Settings → System → Logs
   ```

2. **Enable Debug Mode**:
   Add to `configuration.yaml`:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.ai_hub: debug
   ```

3. **Restart Home Assistant** and re-test

### Getting Help
If the above does not solve your problem:
1. **Check the [Issues Page](https://github.com/ha-china/ai_hub/issues)** for similar issues
2. **Open a New Issue**. Please provide:
   - Home Assistant version
   - AI Hub version
   - Detailed error description
   - Relevant log information
   - Steps to reproduce

---

## 🤝 Contribution

Everyone is welcome to contribute and help improve features and documentation:

### How to Contribute
1. **Report Issues**: Submit bug reports or feature requests on [Issues](https://github.com/ha-china/ai_hub/issues)
2. **Submit Code**: Fork the project, make changes, and submit a Pull Request
3. **Improve Docs**: Help enhance the documentation and provide usage examples
4. **Test & Feedback**: Try out new features and share your feedback

## 📄 License

This project is released under the [LICENSE](LICENSE) as found in this repository.

### Project Links
- **Homepage**: [https://github.com/ha-china/ai_hub](https://github.com/ha-china/ai_hub)
- **Issue Tracker**: [https://github.com/ha-china/ai_hub/issues](https://github.com/ha-china/ai_hub/issues)
- **Releases**: [https://github.com/ha-china/ai_hub/releases](https://github.com/ha-china/ai_hub/releases)
- **HACS Page**: [HACS Integration Store](https://hacs.xyz/docs/integration/setup)

### Credits
- Thanks to [knoop7](https://github.com/knoop7) for project infrastructure
- Thanks to [hasscc/hass-edge-tts](https://github.com/hasscc/hass-edge-tts) for the Edge TTS integration
- Thanks to all contributors and users for your support and feedback

