<h1 align="center">AI Hub · One-Stop Free AI Services</h1>
<p align="center">
  To let you enjoy various free AI services, this integration does not support any paid models or services. You may need to register an account or create an API Key.<br>
  <strong>Special Thanks:</strong> We stand on the shoulders of giants. Without the projects <a href="https://github.com/knoop7" target="_blank">knoop7</a> and <a href="https://github.com/hasscc/hass-edge-tts" target="_blank">hasscc/hass-edge-tts</a>, this integration would not exist. Thank you!
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
- [Account Registration and Token Acquisition](#account-registration-and-token-acquisition)
- [User Guide](#user-guide)
- [Service API Reference](#service-api-reference)
- [Configuration](#configuration)
- [Notes](#notes)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## 🔧 Prerequisites

- **Home Assistant**: Version 2025.8.0 or above
- **Network Requirement**: This integration fully depends on Internet services, a stable network connection is required

## 🌟 Features

AI Hub is a custom integration for Home Assistant, providing native integration with Zhipu AI, SiliconFlow, and Bemfa:

### Core Functions

#### 🗣️ Conversation Assistant
- **Streaming Output**: Real-time model responses for a smooth conversational experience
- **Home Control**: Connects to Home Assistant LLM API, supports controlling/querying devices
- **Image Understanding**: Automatically switches to a visual model (GLM-4.1V-Thinking) when a message contains an image
- **Context Memory**: Configurable number of history messages to balance effect and performance
- **Web Search**: Enable web_search tool in advanced mode

#### 🤖 AI Tasks
- **Structured Data Generation**: Specify JSON structure, error feedback if failed
- **Image Generation**: Use CogView series models, supports URL or base64 result
- **Multimodal Support**: Reuses conversation format, making complex tasks easier

#### 🔊 Text-to-Speech (TTS, Edge TTS)
- **High-Quality Speech**: Integrates Microsoft Edge TTS, supports multiple languages and styles
- **Rich Voice Library**: Supports voices like Xiaoxiao, YunJian, Aria, Jenny, etc.
- **Parameter Tuning**: Supports speed/volume/pitch/style adjustments
- **Multiple Formats**: Outputs audio in WAV/MP3/OGG and more

#### 🎤 Speech-to-Text (STT, SiliconFlow)
- **High-Accuracy Recognition**: Integrates SiliconFlow speech recognition services
- **Multi-language Support**: Automatically detects Chinese, English, and more
- **Format Compatibility**: Supports WAV/MP3/FLAC and other audio formats
- **Real-Time Processing**: Suitable for voice control and automations

#### 🌐 HACS Integration Translation
- **Auto Translate**: Uses ZhipuAI to translate custom component English translation files to Chinese
- **Batch Processing**: Supports batch translation for multiple components
- **Smart Recognition**: Automatically identifies components that need translation and skips those with existing Chinese translations

#### 📱 WeChat Message Push (Bemfa)
- **Real-Time Notification**: Integrates Bemfa service to send device state notifications via WeChat
- **Multimedia Support**: Supports sending text and image messages
- **Simple Configuration**: Just acquire the Bemfa device topic to use

---

## 📦 Installation

### Method 1: HACS Installation (Recommended)

1. **Open HACS**: In Home Assistant, go to HACS → Integrations
2. **Search Integration**: Click "Explore & Download repositories" at the top right, search for "ai_hub"
3. **Install Integration**: Find "AI Hub" and click download
4. **Restart HA**: Restart Home Assistant for the integration to take effect

### Method 2: Manual Installation

1. **Download Files**: Download the latest `ai_hub.zip` from [GitHub Releases](https://github.com/ha-china/ai_hub/releases)
2. **Extract Files**: Extract the zip to `<HA_CONFIG>/custom_components/ai_hub/`
3. **Restart HA**: Restart Home Assistant

> **Note**: This integration relies on the new Conversation/AI Task/Child Item framework. We recommend using a new version of Home Assistant (2025.8.0 or newer).

---

## 🚀 Quick Start

### Configuration Wizard

1. **Add Integration**: Go to Settings → Devices & Services → Integrations → Add Integration, search "AI HUB"
2. **Configure API Keys**: Setup the following services as prompted by the wizard:
   - Zhipu API Key (for Conversation, AI Task, TTS, STT)
   - SiliconFlow API Key (for Speech Recognition)
   - Bemfa API Key (for WeChat notifications)
3. **Validate Configuration**: The system will automatically validate the API Keys
4. **Finish Setup**: After configuration, relevant services and entities will be created automatically

### Child Entry Configuration

AI Hub supports multiple "child entries" for independent function configurations:

- **AI Hub Conversation Assistant**: For Assist conversation agent
- **AI Hub AI Tasks**: For image generation and structured data
- **AI Hub TTS Voice**: For text-to-speech
- **AI Hub STT Voice**: For speech-to-text
- **AI Hub WeChat Notification**: For WeChat message push
- **AI Hub Integration Translation**: For component translation

---

## 🔑 Account Registration and Token Acquisition

### Zhipu AI
- **Purpose**: Conversation assistant, AI tasks, TTS, STT
- **Registration Link**: [https://www.bigmodel.cn/claude-code?ic=19ZL5KZU1F](https://www.bigmodel.cn/claude-code?ic=19ZL5KZU1F)
- **Getting API Key**:
  1. Register and log in
  2. Go to the [Console](https://open.bigmodel.cn/usercenter/apikeys)
  3. Click "Create API Key"
  4. Copy the generated API Key

### SiliconFlow
- **Purpose**: Speech recognition
- **Registration Link**: [https://cloud.siliconflow.cn/i/U3e0rmsr](https://cloud.siliconflow.cn/i/U3e0rmsr)
- **Getting API Key**:
  1. Register and log in
  2. Go to the console
  3. Create a new API Key in the API Management page
  4. Copy the generated API Key

### Bemfa
- **Purpose**: WeChat message push
- **Registration Link**: [http://www.cloud.bemfa.com/u_register.php](http://www.cloud.bemfa.com/u_register.php)
- **Getting Device Topic**:
  1. Register and log in
  2. Go to [TCP Device Management](https://cloud.bemfa.com/tcp/index.html)
  3. Add a new device or use an existing one
  4. Copy the device topic

> **Note**: Edge TTS uses Microsoft's free official API and does not require a separate API Key.

---

## 📖 User Guide

### A. Conversation Assistant

#### Basic Conversation
1. **Switch Agent**: In the Assist conversation page, set the agent to "AI Hub Conversation Assistant"
2. **Start Chatting**: Enter or say what you need, such as:
   - "Turn on the living room light to 60%"
   - "Summarize my schedule for today"
   - "Set an alarm for 8am tomorrow"

#### Image Understanding
1. **Upload Image**: Upload an image or use a camera image in the supported frontend
2. **Describe Issue**: Enter your question or description related to the image
3. **Get Analysis**: The model will analyze and respond automatically

#### Tool Usage
- **Enable Tools**: In conversation assistant child entry, enable "LLM Hass API"
- **Control Device**: Model can call Home Assistant's tools to control/query devices

### B. AI Tasks

#### Image Generation
Generate an image via automation or service call:

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
Generate structured data in a specified format:

```yaml
# Call AI task to generate JSON data
service: ai_hub.ai_task
data:
  input: "Generate a JSON with name, age, and profession"
  model: "GLM-4-Flash-250414"
  temperature: 0.3
```

### C. TTS (Text-to-Speech)

#### Entity Method
1. **Select TTS**: Select "AI Hub TTS Voice" in the media player
2. **Enter Text**: Enter text to synthesize
3. **Play Voice**: The system will play the synthesized voice automatically

#### Service Call Method
```yaml
service: ai_hub.tts_speech
data:
  text: "Welcome to using AI Hub text-to-speech service"
  voice: "zh-CN-XiaoxiaoNeural"
  rate: "+0%"
  volume: "+0%"
  media_player_entity: media_player.living_room_speaker
```

### D. STT (Speech-to-Text)

#### Entity Method
1. **Select STT**: Choose "AI Hub STT Voice" in microphone settings
2. **Start Recording**: Tap the record button to start speech input
3. **Get Text**: System will convert speech to text automatically

#### Service Call Method
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
  - alias: "Door Open Notification"
    trigger:
      - platform: state
        entity_id: binary_sensor.front_door
        to: "on"
    action:
      - service: ai_hub.send_wechat_message
        data:
          device_entity: binary_sensor.front_door
          message: "The front door is open. Please pay attention!"
```

### F. Integration Translation

#### Manual Translation
```yaml
service: ai_hub.translate_components
data:
  custom_components_path: "custom_components"  # Optional, default path
  force_translation: false  # Whether to force re-translation
```

---

## 🔧 Service API Reference

AI Hub provides a rich set of service interfaces, available via the developer tools services panel:

### Image Generation Service
```yaml
service: ai_hub.generate_image
data:
  prompt: "Image Description"  # Required: image description
  size: "1024x1024"  # Optional: image size
  model: "cogview-3-flash"  # Optional: model name
```

### Image Analysis Service
```yaml
service: ai_hub.analyze_image
data:
  image_file: "/path/to/image.jpg"  # Optional: image file path
  image_entity: "camera.front_door"  # Optional: camera entity ID
  message: "Analysis instruction"  # Required: analysis description
  model: "glm-4.1v-thinking-flash"  # Optional: model name
  temperature: 0.3  # Optional: temperature parameter
  max_tokens: 1000  # Optional: max tokens
```

### Text-to-Speech Service
```yaml
service: ai_hub.tts_speech
data:
  text: "Text to convert"  # Required: text content
  voice: "zh-CN-XiaoxiaoNeural"  # Optional: voice type
  speed: 1.0  # Optional: speech speed
  volume: 1.0  # Optional: volume
  media_player_entity: "media_player.speaker"  # Optional: player entity
```

### Speech-to-Text Service
```yaml
service: ai_hub.stt_transcribe
data:
  file: "/path/to/audio.wav"  # Required: audio file path
  model: "FunAudioLLM/SenseVoiceSmall"  # Optional: STT model
```

### Create Automation Service
```yaml
service: ai_hub.create_automation
data:
  description: "Automation description"  # Required: natural language description
  name: "Automation name"  # Optional: automation name
  area_id: "living_room"  # Optional: area id
```

### WeChat Message Sending Service
```yaml
service: ai_hub.send_wechat_message
data:
  device_entity: "sensor.door_sensor"  # Required: entity to monitor
  message: "Message content"  # Required: message
  group: "Notification group"  # Optional: message group
  url: "https://example.com"  # Optional: link
```

### Component Translation Service
```yaml
service: ai_hub.translate_components
data:
  custom_components_path: "custom_components"  # Optional: custom component path
  force_translation: false  # Optional: force translation
  target_component: "custom_component_name"  # Optional: target component
  list_components: false  # Optional: just list components
```

---

## ⚙️ Configuration

### Recommended Settings (Defaults)

#### Conversation Assistant
- **Model**: GLM-4-Flash-250414
- **Temperature**: 0.3 (controls answer randomness)
- **Top P**: 0.5 (controls candidate word range)
- **Top K**: 1 (candidate count limit)
- **Max Tokens**: 250
- **Message History**: 30 (for context continuity)

#### AI Task
- **Text Model**: GLM-4-Flash-250414
- **Image Model**: cogview-3-flash
- **Temperature**: 0.95 (higher creativity)
- **Top P**: 0.7
- **Max Tokens**: 2000

#### TTS Settings
- **Default Voice**: zh-CN-XiaoxiaoNeural (Xiaoxiao)
- **Default Format**: audio-16khz-32kbitrate-mono-mp3
- **Speed**: 1.0 (normal)
- **Volume**: 1.0 (normal)
- **Streaming Output**: enabled

#### STT Settings
- **Default Model**: FunAudioLLM/SenseVoiceSmall
- **Supported Languages**: Simplified Chinese, English, Japanese, Korean, and 15+ languages
- **Audio Formats**: WAV, MP3, FLAC, M4A, OGG, WebM
- **Max File Size**: 25MB

### Advanced Configuration Options

#### Web Search
- **Enable Condition**: Enable in conversation assistant advanced mode
- **Function**: Allows the model to search the web for more accurate answers
- **Note**: May increase response time

#### Multi-language Voice Support
AI Hub supports 400+ voices in 60+ languages, including:
- **Chinese**: Xiaoxiao, Xiaoyi, YunJian, YunXi, YunXia, YunYang (Simplified), Xiaojia, Xiaowen, Yunlong (Traditional), etc.
- **English**: Jenny, Guy, Aria, Davis, Jane, Jason, etc. (US, UK, AU, etc.)
- **Others**: Japanese, Korean, French, German, Spanish, Italian, etc.

---

## ⚠️ Notes

### System Requirements
1. **Network Dependency**: This integration fully depends on Internet services; ensure your network is stable
2. **Performance**: High-performance devices are recommended for better voice processing experience
3. **Storage**: Voice files may require temporary storage space

### Usage Limitations
1. **Free Models**:
   - No streaming output, responses may be slower
   - Call frequency limits apply
   - Free quota is limited

2. **API Keys**:
   - Keep API Keys safe, do not expose them
   - Regularly check API usage to avoid overuse
   - In case of API errors, check if Keys are valid

3. **Function Limitations**:
   - Some advanced features require newer Home Assistant versions
   - Image generation/recognition requires a stable network
   - WeChat push requires following Bemfa's WeChat public account

### Privacy & Security
1. **Data Transfer**: All data is transmitted to relevant AI services via the Internet
2. **Local Storage**: Voice files may be temporarily stored locally
3. **API Security**: Always keep your API Keys safe

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. Cannot Add Integration
**Possible Causes**:
- Home Assistant version is too low (requires 2025.8.0+)
- Network issues
- Invalid API Keys

**Solutions**:
- Check your Home Assistant version
- Ensure network connection
- Verify API Keys

#### 2. Conversation Assistant Not Responding
**Possible Causes**:
- Zhipu AI API Key invalid or expired
- Network issues
- Wrong model selected

**Solutions**:
- Check your Zhipu AI API Key
- Test network connection
- Make sure to use free models

#### 3. TTS Not Playing
**Possible Causes**:
- Edge TTS service unavailable
- Incorrect media player chosen
- Network issues

**Solutions**:
- Check connectivity to Microsoft services
- Confirm media player is working
- Try a different voice model

#### 4. STT Recognition Fails
**Possible Causes**:
- SiliconFlow API Key invalid
- Unsupported audio file format
- File is too large

**Solutions**:
- Check SiliconFlow API Key
- Use a supported audio format
- Compress audio file size

#### 5. WeChat Push Not Working
**Possible Causes**:
- Bemfa device topic misconfigured
- Not following Bemfa's WeChat account
- Network issues

**Solutions**:
- Check if the device topic is correct
- Make sure you follow Bemfa's official WeChat account
- Test your network connection

### Log Debugging
If you encounter problems, check Home Assistant logs:

1. **View Integration Logs**:
   ```
   Settings → System → Logs
   ```

2. **Enable Debug Mode**:
   Add the following to `configuration.yaml`:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.ai_hub: debug
   ```

3. **Restart Home Assistant** and retest functionality

### Getting Help
If problems persist:
1. **Check [Issues page](https://github.com/ha-china/ai_hub/issues)** to see if there are similar issues
2. **Create a new Issue** with:
   - Home Assistant version
   - AI Hub version
   - Detailed error description
   - Relevant logs
   - Reproduction steps

---

## 🤝 Contributing

You're welcome to contribute and help improve features and documentation:

### How to Contribute
1. **Report Issues**: Report bugs or feature requests via [Issues](https://github.com/ha-china/ai_hub/issues)
2. **Submit Code**: Fork the project, make changes, and submit a Pull Request
3. **Improve Docs**: Help improve documentation and add usage examples
4. **Testing & Feedback**: Test new features and give feedback

### Development Environment
1. **Clone the Project**:
   ```bash
   git clone https://github.com/ha-china/ai_hub.git
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Tests**:
   ```bash
   python -m pytest
   ```

### Code Standards
- Follow PEP 8 style guide
- Add appropriate comments and docstrings
- Ensure all code passes existing tests
- Run a code formatter before submitting

---

## 📄 License

This project is released under the [LICENSE](LICENSE) in the repository.

### Project Links
- **Project Home**: [https://github.com/ha-china/ai_hub](https://github.com/ha-china/ai_hub)
- **Issues**: [https://github.com/ha-china/ai_hub/issues](https://github.com/ha-china/ai_hub/issues)
- **Releases**: [https://github.com/ha-china/ai_hub/releases](https://github.com/ha-china/ai_hub/releases)
- **HACS Page**: [HACS Integration Store](https://hacs.xyz/docs/integration/setup)

### Special Thanks
- Thanks to [knoop7](https://github.com/knoop7) for the base architecture
- Thanks to [hasscc/hass-edge-tts](https://github.com/hasscc/hass-edge-tts) for Edge TTS integration
- Thanks to all contributors and users for your support and feedback

---

<p align="center">
  <strong>If this project helps you, please consider giving it a ⭐ star!</strong>
</p>