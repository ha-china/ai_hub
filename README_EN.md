<h1 align="center">AI Hub · One-Stop Free AI Service</h1>
<p align="center">
  To let you experience a variety of free AI services, this integration does not support any paid models or services. However, you may need to register for an account or create an API Key.<br>
  <strong>Acknowledgements:</strong> "Standing on the shoulders of giants." Without the projects <a href="https://github.com/knoop7" target="_blank">knoop7</a> and <a href="https://github.com/hasscc/hass-edge-tts" target="_blank">hasscc/hass-edge-tts</a>, this integration would not exist. Sincere thanks!
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
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Account Registration & Token Acquisition](#account-registration--token-acquisition)
- [User Guide](#user-guide)
- [Service Usage](#service-usage)
- [Configuration](#configuration)
- [Notes](#notes)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## 🔧 Prerequisites

- **Home Assistant**: 2025.8.0 or later
- **Network Requirements**: This integration fully relies on internet services; a stable connection is required.

## 🌟 Features

AI Hub is a Home Assistant custom integration providing native connection to Zhipu AI, SiliconFlow, and Bemfa cloud.

If you do not need certain items, just leave the API key blank or delete the entry. You can add it again whenever needed.

### Core Features

#### 🗣️ Conversation Assistant

- **Streaming Output**: Real-time display of model responses, a smooth conversational experience
- **Home Control**: Connects to Home Assistant LLM API, supports device control/queries
- **Visual Understanding**: Auto-switches to the vision model (GLM-4.1V-Thinking) when a message contains an image
- **Context Memory**: Configurable history message count to balance effectiveness and performance

#### 🤖 AI Tasks

- **Structured Data Generation**: Specify JSON structure, error hints when failure occurs
- **Image Generation**: Use CogView models to generate images; supports URL or base64 outputs
- **Multimodal Support**: Reuses conversation message formats for complex tasks

#### 🔊 Text-to-Speech (TTS, Edge TTS)

- **High-Quality Speech**: Integrates Microsoft Edge TTS, supports multiple languages and styles
- **Rich Voice Library**: Supports voices like Xiaoxiao, Yunjian, Aria, Jenny, etc.
- **Parameter Tuning**: Speech rate/volume/pitch/style adjustable
- **Various Formats**: Output in WAV/MP3/OGG audio formats

#### 🎤 Speech-to-Text (STT, SiliconFlow)

- **High Accuracy**: Integrates SiliconFlow’s speech recognition service
- **Multi-language Support**: Detects Mandarin, English, and more automatically
- **Format Compatibility**: Supports WAV/MP3/FLAC audio files
- **Real-Time Processing**: Ideal for voice control and automation scenarios

#### 🌐 HACS Integration Localization

- **Auto Translation**: Uses Zhipu AI to translate custom component English translation files to Chinese
- **Batch Processing**: Supports batch localization for multiple components
- **Smart Recognition**: Automatically identifies components needing translation; skips ones already localized

#### 📱 WeChat Push Notifications (Bemfa)

- **Real-time Notification**: Integrates Bemfa cloud to send device status via WeChat

---

## 📦 Installation

### Method 1: Install via HACS (Recommended)

1. **Open HACS**: Go to HACS → Integrations in Home Assistant
2. **Search for Integration**: Tap "Explore & Download repositories" at top-right; search for "ai_hub"
3. **Install Integration**: Find "AI Hub" and click Download
4. **Restart System**: Restart Home Assistant to activate

### Method 2: Manual Installation

1. **Download Files**: Download the latest `ai_hub.zip` from [GitHub Releases](https://github.com/ha-china/ai_hub/releases)
2. **Extract Files**: Extract the zip into `<HA_CONFIG>/custom_components/ai_hub/`
3. **Restart System**: Restart Home Assistant

> **Note**: This integration depends on the new Conversation/AI Task/sub-entry framework. Use a newer Home Assistant version (>2025.8.0).

---

## 🚀 Quick Start

### Setup Wizard

1. **Add Integration**: Go to Settings → Devices & Services → Integrations → Add Integration, search "AI HUB (ai_hub)"
2. **Configure API Keys**: Follow the wizard to enter for these services:
   - Zhipu API Key (for Conversation, AI Tasks, TTS, STT)
   - SiliconFlow API Key (for Speech Recognition)
   - Bemfa API Key (for WeChat Push Notification)
3. **Validate Config**: System validates API Keys automatically
4. **Finish Setup**: Instantly creates corresponding services and entities

### Sub-entry Configuration

AI Hub supports sub-entry configurations to create separate setups for different functions:

- **AI Hub Conversation Assistant**: For Assist conversation proxy
- **AI Hub AI Task**: For image generation & structured data
- **AI Hub TTS Voice**: For text-to-speech
- **AI Hub STT Voice**: For speech-to-text
- **AI Hub WeChat Notification**: For WeChat push notification
- **AI Hub Integration Localization**: For component localization

---

## 🔑 Account Registration & Token Acquisition

### Zhipu AI
- **Use**: Conversation assistant, AI tasks, TTS, STT
- **Register**: [Click to register](https://www.bigmodel.cn/claude-code?ic=19ZL5KZU1F)
- **Get API Key**:
  1. Register and login
  2. Enter [Console](https://open.bigmodel.cn/usercenter/apikeys)
  3. Click "Create API Key"
  4. Copy the generated API Key

### SiliconFlow
- **Use**: Speech recognition services
- **Register**: [Click to register](https://cloud.siliconflow.cn/i/U3e0rmsr)
- **Get API Key**:
  1. Register and login
  2. Enter console
  3. Go to API Management, create a new key
  4. Copy the generated API Key

### Bemfa
- **Use**: WeChat push notification
- **Register**: [Click to register](http://www.cloud.bemfa.com/u_register.php)
- **Get Device Topic**:
  1. Register and login
  2. Go to [TCP Device Management](https://cloud.bemfa.com/tcp/index.html)
  3. Create a new device or use an existing one
  4. Copy the device's topic

> **Note**: Edge TTS uses Microsoft's free official API; no API Key needed.

---

## 📖 User Guide

### A. Conversation Assistant

#### Basic Conversation
1. **Switch Proxy**: On the Assist conversation page, switch current proxy to "AI Hub Conversation Assistant"
2. **Start Conversation**: Directly type or speak your question, e.g.:
   - "Turn on the living room light to 60%"
   - "Summarize today's schedule"
   - "Set an alarm for 8am tomorrow"

#### Visual Understanding
1. **Upload Image**: Upload or reference a camera image on supported frontend
2. **Describe Query**: Type your question or description about the image
3. **Get Analysis**: Model will auto-analyze and reply

#### Tool Calling
- **Enable Tools**: Enable "LLM Hass API" in the conversation assistant’s sub-entry
- **Control Devices**: Model can call Home Assistant tools to control/query devices

### B. AI Task Usage

#### Image Generation
Generate images through automations or service calls:

```yaml
automation:
  - alias: "Generate Daily Image"
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
Generate structured data with specified format:

```yaml
# Call AI task to generate JSON data
service: ai_hub.ai_task
data:
  input: "Generate a JSON data including name, age, occupation"
  model: "GLM-4-Flash-250414"
  temperature: 0.3
```

### C. TTS Speech Synthesis

#### Entity Method
1. **Select TTS**: In the media player, choose "AI Hub TTS Voice" as the voice service
2. **Input Text**: Enter text to be synthesized
3. **Play Voice**: The system will play the generated speech automatically

#### Service Call
```yaml
service: ai_hub.tts_speech
data:
  text: "Welcome to AI Hub TTS service"
  voice: "zh-CN-XiaoxiaoNeural"
  rate: "+0%"
  volume: "+0%"
  media_player_entity: media_player.living_room_speaker
```

### D. STT Speech Recognition

#### Entity Method
1. **Select STT**: In microphone settings, select "AI Hub STT Voice"
2. **Start Recording**: Click record to start
3. **Get Text**: System will transcribe speech to text automatically

#### Service Call
```yaml
service: ai_hub.stt_transcribe
data:
  file: "/config/tmp/recording.wav"
  model: "FunAudioLLM/SenseVoiceSmall"
```

### E. WeChat Message Push

#### Automation Push
```yaml
automation:
  - alias: "Door/Window Open Notification"
    trigger:
      - platform: state
        entity_id: binary_sensor.front_door
        to: "on"
    action:
      - service: ai_hub.send_wechat_message
        data:
          device_entity: binary_sensor.front_door
          message: "Front door opened, please pay attention!"
```

### F. Integration Localization

#### Manual Localization
```yaml
service: ai_hub.translate_components
data:
  custom_components_path: "custom_components"  # optional, default path
  force_translation: false  # whether to forcibly re-translate
```

---

## 🔧 Service Usage Details

AI Hub provides a range of service APIs, callable in Developer Tools > Services:

### Image Generation Service
```yaml
service: ai_hub.generate_image
data:
  prompt: "Image description"  # required
  size: "1024x1024"  # optional
  model: "cogview-3-flash"  # optional
```

### Image Analysis Service
```yaml
service: ai_hub.analyze_image
data:
  image_file: "/path/to/image.jpg"  # optional file path
  image_entity: "camera.front_door"  # optional entity ID
  message: "Analysis instructions"  # required
  model: "glm-4.1v-thinking-flash"  # optional model
  temperature: 0.3  # optional temperature param
  max_tokens: 1000  # optional max tokens
```

### Text-to-Speech Service
```yaml
service: ai_hub.tts_speech
data:
  text: "Text to convert"  # required
  voice: "zh-CN-XiaoxiaoNeural"  # optional
  speed: 1.0  # optional
  volume: 1.0  # optional
  media_player_entity: "media_player.speaker"  # optional
```

### Speech-to-Text Service
```yaml
service: ai_hub.stt_transcribe
data:
  file: "/path/to/audio.wav"  # required
  model: "FunAudioLLM/SenseVoiceSmall"  # optional STT model
```

### Create Automation Service
```yaml
service: ai_hub.create_automation
data:
  description: "Automation description"  # required
  name: "Automation Name"  # optional
  area_id: "living_room"  # optional
```

### Send WeChat Message Service
```yaml
service: ai_hub.send_wechat_message
data:
  device_entity: "sensor.door_sensor"  # required entity to monitor
  message: "Message content"  # required
  group: "Notification group"  # optional
  url: "https://example.com"  # optional link
```

### Translate Components Service
```yaml
service: ai_hub.translate_components
data:
  custom_components_path: "custom_components"  # optional
  force_translation: false  # optional
  target_component: "custom_component_name"  # optional specific component
  list_components: false  # optional list only
```

---

## ⚙️ Configuration

### Recommended Config (Default Values)

#### Conversation Assistant
- **Model**: GLM-4-Flash-250414
- **Temperature**: 0.3 (controls randomness)
- **Top P**: 0.5 (limits candidate tokens)
- **Top K**: 1 (limits candidate count)
- **Max Tokens**: 250
- **History Count**: 30 (keeps conversation continuity)

#### AI Tasks
- **Text Model**: GLM-4-Flash-250414
- **Image Model**: cogview-3-flash
- **Temperature**: 0.95 (higher creativity)
- **Top P**: 0.7
- **Max Tokens**: 2000

#### TTS
- **Default Voice**: zh-CN-XiaoxiaoNeural (Xiaoxiao)
- **Default Format**: audio-16khz-32kbitrate-mono-mp3
- **Speed**: 1.0 (normal)
- **Volume**: 1.0 (normal)
- **Streaming Output**: enabled

#### STT
- **Default Model**: FunAudioLLM/SenseVoiceSmall
- **Supported Languages**: Chinese (Simplified), English, Japanese, Korean, and 15+ languages
- **Audio Formats**: WAV, MP3, FLAC, M4A, OGG, WebM
- **Max File Size**: 25MB

### Advanced Config Options

#### Internet Search
- **Enable**: In Advanced mode of Conversation Assistant
- **Function**: Allows web search for more accurate answers
- **Note**: May slow response

#### Multi-language TTS
AI Hub supports 400+ voices across 60+ languages including:
- **Chinese**: Xiaoxiao, Xiaoyi, Yunjian, Yunxi, Yunxia, Yunyang (Simplified), Xiaojia, Xiaowen, Yunlong (Traditional), etc.
- **English**: Jenny, Guy, Aria, Davis, Jane, Jason, etc. (US/UK/AU accents)
- **Others**: Japanese, Korean, French, German, Spanish, Italian, etc.

---

## ⚠️ Notes

### System Requirements
1. **Network Dependent**: Fully relies on internet services – ensure stable connection
2. **Performance**: Better device recommended for audio features
3. **Storage**: Temporary storage may be required for audio files

### Usage Limitations
1. **Free Models**:
   - No streaming output; might have slower responses
   - Limited call frequency
   - Limited free quota

2. **API Keys**:
   - Keep your API keys safe; do not leak them
   - Regularly check API usage to avoid overage
   - If errors occur, check key validity

3. **Feature Limitations**:
   - Some advanced features require newer Home Assistant versions
   - Image generation/recognition needs stable network
   - WeChat notification requires attention to follow the Bemfa account

### Privacy and Security
1. **Data Transmission**: All data is transmitted to corresponding AI services via the Internet
2. **Local Storage**: Audio files may be stored locally for a while
3. **API Security**: Ensure your API keys are safe

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. Integration cannot be added
**Possible Causes**:
- Home Assistant version too low (requires 2025.8.0+)
- Network issues
- Invalid API Keys

**Solutions**:
- Check Home Assistant version
- Ensure stable network connection
- Validate API Key correctness

#### 2. Conversation Assistant Not Responding
**Possible Causes**:
- Invalid/expired Zhipu AI API Key
- Network issues
- Wrong model chosen

**Solutions**:
- Check Zhipu AI API Key
- Test network
- Ensure using free models

#### 3. TTS Not Working
**Possible Causes**:
- Edge TTS service unavailable
- Wrong media player selected
- Network issues

**Solutions**:
- Check network to Microsoft Service
- Verify media player
- Try different TTS voice

#### 4. STT Recognition Fails
**Possible Causes**:
- Invalid SiliconFlow API Key
- Unsupported audio format
- File too large

**Solutions**:
- Check SiliconFlow API Key
- Ensure audio format is supported
- Compress file size

#### 5. WeChat Push Not Working
**Possible Causes**:
- Wrong Bemfa device topic
- Bemfa public account not followed
- Network issue

**Solutions**:
- Check device topic
- Ensure Bemfa public account followed
- Test network

### Debug Logs
If you encounter issues, check Home Assistant logs:

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
1. **Check [Issues page](https://github.com/ha-china/ai_hub/issues)** for similar problems
2. **Open a new Issue** with:
   - Home Assistant version
   - AI Hub version
   - Detailed error description
   - Relevant logs
   - Steps to reproduce

---

## 🤝 Contributing

You're welcome to contribute to the project and help improve features and documentation:

### How to Contribute
1. **Report Issues**: [Issues](https://github.com/ha-china/ai_hub/issues) for bug reports and suggestions
2. **Submit Code**: Fork the repo, submit Pull Requests after changes
3. **Improve Docs**: Help to improve documentation and add examples
4. **Test & Feedback**: Test new features and give feedback

## 📄 License

This project is released under the [LICENSE](LICENSE) in this repository.

### Project Links
- **Homepage**: [https://github.com/ha-china/ai_hub](https://github.com/ha-china/ai_hub)
- **Issue Tracker**: [https://github.com/ha-china/ai_hub/issues](https://github.com/ha-china/ai_hub/issues)
- **Releases**: [https://github.com/ha-china/ai_hub/releases](https://github.com/ha-china/ai_hub/releases)
- **HACS Page**: [HACS Integration Store](https://hacs.xyz/docs/integration/setup)

### Acknowledgements
- Thanks to [knoop7](https://github.com/knoop7) for the foundational architecture
- Thanks to [hasscc/hass-edge-tts](https://github.com/hasscc/hass-edge-tts) for Edge TTS integration
- Thanks to all contributors and users for your support and feedback

