<h1 align="center">AI Hub · One-stop Free AI Services</h1>
<p align="center">
  To allow you to experience various free AI services, this integration does not support any paid models or services. You may need to apply for an account or create an API Key.<br>
  <strong>Special Thanks:</strong> We stand on the shoulders of giants. Without <a href="https://github.com/knoop7" target="_blank">knoop7</a> and <a href="https://github.com/hasscc/hass-edge-tts" target="_blank">hasscc/hass-edge-tts</a>, this project would not exist!
</p>

<p align="center">
  <a href="https://github.com/ha-china/ai_hub/releases"><img src="https://img.shields.io/github/v/release/ha-china/ai_hub" alt="GitHub Version"></a>
  <a href="https://github.com/ha-china/ai_hub/issues"><img src="https://img.shields.io/github/issues/ha-china/ai_hub" alt="GitHub Issues"></a>
  <img src="https://img.shields.io/github/forks/ha-china/ai_hub?style=social" alt="GitHub Forks">
  <img src="https://img.shields.io/github/stars/ha-china/ai_hub?style=social" alt="GitHub Stars"> <a href="README.md">中文</a>
</p>

---

## 📋 Table of Contents

- [🔧 Prerequisites](#🔧-prerequisites)
- [🌟 Features](#🌟-features)
- [📦 Installation](#📦-installation)
- [🚀 Quick Start](#🚀-quick-start)
- [🔑 Account Registration & Token Acquisition](#🔑-account-registration--token-acquisition)
- [📖 Usage Guide](#📖-usage-guide)
- [🔧 Service Details](#🔧-service-details)
- [⚙️ Configuration Parameters](#⚙️-configuration-parameters)
- [⚠️ Notes](#⚠️-notes)
- [🛠️ Troubleshooting](#🛠️-troubleshooting)
- [🤝 Contributing](#🤝-contributing)
- [📄 License](#📄-license)
- [📱 Follow Me](#📱-follow-me)
- [☕ Support](#☕-support)

---

## 🔧 Prerequisites

- **Home Assistant**: 2025.8.0 or higher
- **Network Requirement**: This integration relies entirely on internet services; a stable network connection is required.

## 🌟 Features

AI Hub is a custom integration for Home Assistant, providing native connections to Zhipu AI, SiliconFlow, and Bemfa.

If you don't need some entries, just leave the api key blank or delete it. You can add it back later when needed.

### Core Features

#### 🗣️ Conversation Assistant
- **Streaming Output**: Real-time display of model replies for a smooth conversational experience.
- **Home Control**: Integrates with Home Assistant LLM API to control/query devices.
- **Image Understanding**: Automatically switches to vision model (GLM-4.1V-Thinking) if a message contains an image.
- **Context Memory**: Configurable number of history messages to balance effect and performance.

#### 🤖 AI Tasks
- **Structured Data Generation**: Specify JSON structure, with error prompts on failure.
- **Image Generation**: Generate images using CogView series models, supporting URL or base64 result.
- **Multimodal Support**: Reuses conversation message format for complex tasks.

#### 🔊 TTS (Text to Speech, Edge TTS)
- **High-Quality Voice**: Integrates Microsoft Edge TTS, supporting multiple languages and styles.
- **Rich Voice Library**: Supports voices like Xiaoxiao, Yun Jian, Aria, Jenny, and more.
- **Parameter Adjustment**: Supports speed/volume/pitch/style adjustments.
- **Various Formats**: Supports output in WAV/MP3/OGG and other formats.

#### 🎤 STT (Speech to Text, SiliconFlow)
- **High Accuracy Recognition**: Integrates SiliconFlow speech recognition service.
- **Multiple Language Support**: Supports Mandarin, English, and other languages with auto-detection.
- **Format Compatibility**: Supports WAV/MP3/FLAC and other audio formats.
- **Real-Time Processing**: Suitable for voice control, automation, etc.

#### 🌐 HACS Integration Localization
- **Auto Translation**: Use Zhipu AI to automatically translate custom component English translation files to Chinese.
- **Batch Processing**: Supports batch localization for multiple components.
- **Intelligent Recognition**: Automatically detects components needing translation, skipping already localized ones.

#### 📱 WeChat Notification (Bemfa)
- **Real-Time Notifications**: Integrate Bemfa service to send device status notifications via WeChat.

---

## 📦 Installation

### Method 1: HACS Installation (Recommended)

1. **Open HACS**: In Home Assistant, go to HACS → Integrations.
2. **Search for Integration**: Click the upper right "Explore & Download Repositories", search for "ai_hub".
3. **Install Integration**: Find "AI Hub" and click Download.
4. **Restart**: Restart Home Assistant to activate.

### Method 2: Manual Installation

1. **Download Files**: Download the latest `ai_hub.zip` from [GitHub Releases](https://github.com/ha-china/ai_hub/releases).
2. **Extract Files**: Unzip to `<HA_CONFIG>/custom_components/ai_hub/`.
3. **Restart**: Restart Home Assistant.

> **Tip**: This integration depends on the new Conversation/AI Task/Entry framework; a newer Home Assistant version (>2025.8.0) is recommended.

---

## 🚀 Quick Start

### Configuration Wizard

1. **Add Integration**: Go to Settings → Devices & Services → Integrations → Add Integration, search "AI HUB (ai_hub)".
2. **Configure API Keys**: Follow the wizard to configure:
   - Zhipu API Key (for Conversation, AI Task, and HACS Localization).
   - SiliconFlow API Key (for STT, free version does not support streaming).
   - Bemfa API Key (for WeChat messages).
3. **Verify**: System will verify your API Keys.
4. **Finish**: Integration will auto-create relevant services and entities.

### Sub-Entry Configuration

AI Hub supports sub-entry configuration for independent functionality:

- **AI Hub Conversation**: For Assist agents.
- **AI Hub AI Task**: For image generation and structured data.
- **AI Hub TTS**: For text-to-speech.
- **AI Hub STT**: For speech-to-text.
- **AI Hub WeChat Notification**: For WeChat messages.
- **AI Hub Localization**: For component translation.

---

## 🔑 Account Registration & Token Acquisition

### Zhipu AI
- **Usage**: Conversation, AI Tasks, TTS, STT
- **Register**: [Sign Up Here](https://www.bigmodel.cn/claude-code?ic=19ZL5KZU1F)
- **Get API Key**:
  1. Register and login.
  2. Go to [Dashboard](https://open.bigmodel.cn/usercenter/apikeys).
  3. Click "Create API Key".
  4. Copy your new API Key.

### SiliconFlow
- **Usage**: Speech Recognition (STT)
- **Register**: [Sign Up Here](https://cloud.siliconflow.cn/i/U3e0rmsr)
- **Get API Key**:
  1. Register and login.
  2. Go to the dashboard.
  3. Create new API Key in the API management page.
  4. Copy your new API Key.

### Bemfa
- **Usage**: WeChat Notification
- **Register**: [Sign Up Here](http://www.cloud.bemfa.com/u_register.php)
- **Get Device Topic**:
  1. Register and login.
  2. Go to [TCP Device Management](https://cloud.bemfa.com/tcp/index.html)
  3. Create or use an existing device.
  4. Copy the device topic.

> **Note**: Edge TTS uses the official Microsoft free API; no API Key is required.

---

## 📖 Usage Guide

### A. Conversation Assistant

#### Basic Conversation
1. **Switch Agent**: In Assist, set agent to "AI Hub Conversation".
2. **Start Chat**: Input/speak questions such as:
   - "Turn on the living room light to 60%"
   - "Summarize my schedule for today"
   - "Set an alarm for 8 AM tomorrow"

#### Image Understanding
1. **Upload Image**: Upload images or use camera snapshots in a supported frontend.
2. **Describe Issue**: Input what you want to ask/analyze about the image.
3. **Get Analysis**: The model analyzes and responds automatically.

#### Tool Invocation
- **Enable Tools**: Enable "LLM Hass API" in the conversation sub-entry.
- **Control Devices**: The model can call Home Assistant APIs to control/query devices.

### B. AI Tasks

#### Image Generation
Generate images via automation or service invocation:

```yaml
automation:
  - alias: "Generate daily picture"
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
Generate formatted JSON data:

```yaml
# Call AI task to generate JSON data
service: ai_hub.ai_task
data:
  input: "Generate a JSON including name, age, and occupation"
  model: "GLM-4-Flash-250414"
  temperature: 0.3
```

### C. TTS (Text to Speech)

#### As Entity
1. **Select TTS**: In a media player, select "AI Hub TTS".
2. **Input Text**: Enter your text.
3. **Play Voice**: It will be played automatically.

#### As Service
```yaml
service: ai_hub.tts_speech
data:
  text: "Welcome to AI Hub voice synthesis"
  voice: "zh-CN-XiaoxiaoNeural"
  rate: "+0%"
  volume: "+0%"
  media_player_entity: media_player.living_room_speaker
```

### D. STT (Speech to Text)

#### As Entity
1. **Select STT**: In microphone settings, select "AI Hub STT".
2. **Record**: Start recording.
3. **Get Text**: Speech will be converted to text.

#### As Service
```yaml
service: ai_hub.stt_transcribe
data:
  file: "/config/tmp/recording.wav"
  model: "FunAudioLLM/SenseVoiceSmall"
```

### E. WeChat Notification

#### Push via Automation
```yaml
automation:
  - alias: "Notify if door/window opens"
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

### F. Localization

#### Manual Translation
```yaml
service: ai_hub.translate_components
data:
  custom_components_path: "custom_components"  # Optional, default path
  force_translation: false  # Force re-translate
```

---

## 🔧 Service Details

AI Hub provides rich service APIs, which can be accessed via Developer Tools.

### Image Generation
```yaml
service: ai_hub.generate_image
data:
  prompt: "Image description"  # required
  size: "1024x1024"  # optional
  model: "cogview-3-flash"  # optional
```

### Image Analysis
```yaml
service: ai_hub.analyze_image
data:
  image_file: "/path/to/image.jpg"  # optional
  image_entity: "camera.front_door"  # optional
  message: "Analysis instruction"  # required
  model: "glm-4.1v-thinking-flash"  # optional
  temperature: 0.3  # optional
  max_tokens: 1000  # optional
```

### Text to Speech
```yaml
service: ai_hub.tts_speech
data:
  text: "Text to convert"  # required
  voice: "zh-CN-XiaoxiaoNeural"  # optional
  speed: 1.0  # optional
  volume: 1.0  # optional
  media_player_entity: "media_player.speaker"  # optional
```

### Speech to Text
```yaml
service: ai_hub.stt_transcribe
data:
  file: "/path/to/audio.wav"  # required
  model: "FunAudioLLM/SenseVoiceSmall"  # optional
```

### Create Automation
```yaml
service: ai_hub.create_automation
data:
  description: "Automation description"  # required
  name: "Automation name"  # optional
  area_id: "living_room"  # optional
```

### WeChat Message
```yaml
service: ai_hub.send_wechat_message
data:
  device_entity: "sensor.door_sensor"  # required
  message: "Message content"  # required
  group: "Notification group"  # optional
  url: "https://example.com"  # optional
```

### Translate Components
```yaml
service: ai_hub.translate_components
data:
  custom_components_path: "custom_components"  # optional
  force_translation: false  # optional
  target_component: "custom_component_name"  # optional
  list_components: false  # optional
```

---

## ⚙️ Configuration Parameters

### Recommended Configuration (Defaults)

#### Conversation
- **Model**: GLM-4-Flash-250414
- **Temperature**: 0.3 (for randomness)
- **Top P**: 0.5 (controls candidate range)
- **Top K**: 1 (limits candidate count)
- **Max Tokens**: 250
- **History Messages**: 30 (context continuity)

#### AI Tasks
- **Text Model**: GLM-4-Flash-250414
- **Image Model**: cogview-3-flash
- **Temperature**: 0.95 (creativity)
- **Top P**: 0.7
- **Max Tokens**: 2000

#### TTS
- **Default Voice**: zh-CN-XiaoxiaoNeural
- **Default Format**: audio-16khz-32kbitrate-mono-mp3
- **Speed**: 1.0
- **Volume**: 1.0
- **Stream Output**: Enabled

#### STT
- **Default Model**: FunAudioLLM/SenseVoiceSmall
- **Support Languages**: Chinese (Simplified), English, Japanese, Korean, etc. (15 languages)
- **Audio Formats**: WAV, MP3, FLAC, M4A, OGG, WebM
- **Max File Size**: 25MB

---

## ⚠️ Notes

### System Requirements
1. **Network**: This integration depends on the internet. Ensure stable connectivity.
2. **Performance**: Higher device performance provides better voice experience.
3. **Storage**: Voice files may require temporary local storage.

### Usage Limits
1. **Free Models**:
   - No streaming output, may be slower
   - Call frequency limits
   - Free quotas have limitations

2. **API Keys**:
   - Keep your keys safe; do not leak them
   - Check usage periodically
   - Verify keys if errors occur

3. **Feature Limits**:
   - Some features require newer Home Assistant
   - Image generation/recognition needs stable network
   - WeChat push requires following Bemfa public account

### Privacy & Security
1. **Data Transfer**: All data is sent over the internet to AI services.
2. **Local Storage**: Voice files may be temporarily stored locally.
3. **API Security**: Protect your API Keys.

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. Integration cannot be added
**Possible reasons**:
- Home Assistant version too low (needs 2025.8.0+)
- Network issues
- Invalid API Keys

**Solutions**:
- Check Home Assistant version
- Ensure the network is up
- Verify API Keys

#### 2. Conversation Assistant unresponsive
**Possible reasons**:
- Zhipu AI API Key invalid or expired
- Network issues
- Incorrect model selection

**Solutions**:
- Check API Key
- Test network
- Make sure a free model is selected

#### 3. TTS not playing
**Possible reasons**:
- Edge TTS unavailable
- Wrong media player
- Network issues

**Solutions**:
- Check network access to Microsoft
- Confirm media player status
- Try another voice model

#### 4. STT recognition failure
**Possible reasons**:
- SiliconFlow API Key invalid
- Unsupported audio format
- File too large

**Solutions**:
- Check SiliconFlow Key
- Confirm audio format is supported
- Compress audio file

#### 5. WeChat push not working
**Possible reasons**:
- Bemfa device topic config error
- Not following Bemfa official account
- Network issues

**Solutions**:
- Check topic value
- Follow Bemfa public account
- Test network

### Log Debugging
If needed, check Home Assistant log:

1. **Check integration log**:
   ```
   Settings → System → Logs
   ```

2. **Enable Debug**
   Add in `configuration.yaml`:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.ai_hub: debug
   ```

3. **Restart Home Assistant** and test again.

### Get Help
If above doesn't solve your issue:
1. **Check [Issues Page](https://github.com/ha-china/ai_hub/issues)** for known issues
2. **Open new Issue**, please provide:
   - Home Assistant version
   - AI Hub version
   - Detailed description
   - Related logs
   - Reproduce steps

---

## 🤝 Contributing

You're welcome to contribute — improve features and docs!

### How to Contribute
1. **Report Bugs**: [Issues](https://github.com/ha-china/ai_hub/issues)
2. **Submit Code**: Fork, modify & PR
3. **Improve Docs**: Add/expand documentation and usage examples
4. **Feedback**: Test new features and feedback

## 📄 License

This project is released under the [LICENSE](LICENSE) in this repository.

### Project Links
- **Homepage**: [https://github.com/ha-china/ai_hub](https://github.com/ha-china/ai_hub)
- **Issue Tracker**: [https://github.com/ha-china/ai_hub/issues](https://github.com/ha-china/ai_hub/issues)
- **Releases**: [https://github.com/ha-china/ai_hub/releases](https://github.com/ha-china/ai_hub/releases)
- **HACS Page**: [HACS Integration Shop](https://hacs.xyz/docs/integration/setup)

### Thanks
- Thanks to [knoop7](https://github.com/knoop7) for project foundation
- Thanks to [hasscc/hass-edge-tts](https://github.com/hasscc/hass-edge-tts) for Edge TTS integration
- Thanks to all contributors and users for support and feedback

## 📱 Follow Me

📲 Scan the QR code below to follow me! Feel free to leave me a message:

<img src="https://gitee.com/desmond_GT/hassio-addons/raw/main/WeChat_QRCode.png" width="50%" /> 

## ☕ Support

If you found my work helpful, please buy me a milk tea! Your support motivates continuous improvement!

<div style="display: flex; justify-content: space-between;">
  <img src="https://gitee.com/desmond_GT/hassio-addons/raw/main/1_readme/Ali_Pay.jpg" height="350px" />
  <img src="https://gitee.com/desmond_GT/hassio-addons/raw/main/1_readme/WeChat_Pay.jpg" height="350px" />
</div> 💖

Thank you for your support!
