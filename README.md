<h1 align="center">AI Hub · 一站式免费AI服务</h1>
<h1 align="center">AI Hub · One-stop Free AI Services</h1>
<p align="center">
  为了让你体验各种免费的AI服务，本集成默认使用免费模型及服务，当然你可能会需要申请账号或创建 API Key。<br>
  <strong>开篇致谢：</strong>前人栽树，后人乘凉。没有 <a href="https://github.com/knoop7" target="_blank">knoop7</a> 和 <a href="https://github.com/rany2/edge-tts" target="_blank">edge-tts</a> 这两个项目，就没有本集成，特此感谢！<br><br>
  To experience various free AI services, this integration uses free models and services by default. You may need to register an account or create an API Key.<br>
  <strong>Special Thanks:</strong> We stand on the shoulders of giants. Without <a href="https://github.com/knoop7" target="_blank">knoop7</a> and <a href="https://github.com/rany2/edge-tts" target="_blank">edge-tts</a>, this project would not exist!
</p>

<p align="center">
  <a href="https://github.com/ha-china/ai_hub/releases"><img src="https://img.shields.io/github/v/release/ha-china/ai_hub" alt="GitHub Version"></a>
  <a href="https://github.com/ha-china/ai_hub/issues"><img src="https://img.shields.io/github/issues/ha-china/ai_hub" alt="GitHub Issues"></a>
  <img src="https://img.shields.io/github/forks/ha-china/ai_hub?style=social" alt="GitHub Forks">
  <img src="https://img.shields.io/github/stars/ha-china/ai_hub?style=social" alt="GitHub Stars">
</p>

---

## 📋 目录 / Table of Contents

- [🔧 前置条件 / Prerequisites](#-前置条件--prerequisites)
- [🌟 功能介绍 / Features](#-功能介绍--features)
- [📦 安装方法 / Installation](#-安装方法--installation)
- [🚀 快速开始 / Quick Start](#-快速开始--quick-start)
- [🔑 账号注册与Token获取 / Account Registration & Token](#-账号注册与token获取--account-registration--token)
- [📖 使用指南 / Usage Guide](#-使用指南--usage-guide)
- [🤝 参与贡献 / Contributing](#-参与贡献--contributing)
- [📄 许可协议 / License](#-许可协议--license)
- [📱 关注我 / Follow Me](#-关注我--follow-me)
- [☕ 赞助支持 / Support](#-赞助支持--support)

---

## 🔧 前置条件 / Prerequisites

- **Home Assistant**: 2025.8.0 或更高版本 / 2025.8.0 or higher
- **网络要求 / Network**: 本集成完全依赖互联网服务，稳定的网络连接是必需的 / This integration relies entirely on internet services; a stable network connection is required

---

## 🌟 功能介绍 / Features

AI Hub 是 Home Assistant 的自定义集成，提供对话助手、AI任务、TTS、STT，以及组件/蓝图汉化能力。

AI Hub is a custom integration for Home Assistant that provides conversation, AI tasks, TTS, STT, and component/blueprint localization.

> **说明**: 微信等即时消息功能已从本项目移除，统一由 [cn_im_hub](https://github.com/ha-china/cn_im_hub) 提供。
>
> **Note**: Instant messaging features such as WeChat have been removed from this project and are now handled by [cn_im_hub](https://github.com/ha-china/cn_im_hub).

> **提示**: 如果有些条目你不需要，只需不填 API Key 即可，或者直接删除，后续有需要可以再次添加。
> 
> **Tip**: If you don't need some entries, just leave the API key blank or delete it. You can add it back later when needed.

### 核心功能 / Core Features

#### 🗣️ 对话助手 / Conversation Assistant

| 中文 | English |
|------|---------|
| **回复自然**: 支持日常问答、设备控制和状态查询 | **Natural Replies**: Supports daily conversations, device control, and state queries |
| **家居控制**: 对接 Home Assistant LLM API，支持控制和查询设备状态 | **Home Control**: Integrates with Home Assistant LLM API to control devices and query states |
| **图片理解**: 消息携带图片时自动切换到视觉模型（GLM-4.1V-9B-Thinking） | **Image Understanding**: Automatically switches to vision model (GLM-4.1V-9B-Thinking) when message contains an image |
| **连续对话**: 支持多轮对话，适合日常家居语音场景 | **Multi-turn Conversation**: Supports follow-up conversations for daily smart home use |

#### 🤖 AI 任务 / AI Tasks

| 中文 | English |
|------|---------|
| **任务生成**: 可用于生成文本内容、整理信息和处理复杂指令 | **Task Assistance**: Useful for content generation, organizing information, and handling more complex prompts |
| **图片生成**: 使用 Kolors 等模型生成图片，支持 URL 或 base64 返回 | **Image Generation**: Generate images using Kolors and other models, supporting URL or base64 result |
| **多模态支持**: 复用对话消息格式，便于复杂任务处理 | **Multimodal Support**: Reuses conversation message format for complex tasks |

#### 🔊 语音合成 / TTS (Edge TTS)

| 中文 | English |
|------|---------|
| **高质量语音**: 集成微软 Edge TTS，支持多语言、多风格 | **High-Quality Voice**: Integrates Microsoft Edge TTS, supporting multiple languages and styles |
| **丰富语音库**: 支持晓晓、云健、Aria、Jenny 等 400+ 种语音模型 | **Rich Voice Library**: Supports 400+ voices including Xiaoxiao, Yun Jian, Aria, Jenny, and more |
| **Prosody 参数**: 支持语速(rate)、音量(volume)、音调(pitch)调节 | **Prosody Parameters**: Supports rate, volume, and pitch adjustments |
| **对话播报**: 适合搭配语音助手和日常播报场景 | **Conversation Playback**: Suitable for voice assistants and everyday announcement scenarios |
| **多种格式**: 输出 MP3 格式音频 | **Audio Format**: Outputs MP3 format audio |

#### 🎤 语音识别 / STT (SiliconFlow)

| 中文 | English |
|------|---------|
| **高精度识别**: 集成硅基流动语音识别服务，支持 SenseVoice、TeleSpeechASR 等模型 | **High Accuracy Recognition**: Integrates SiliconFlow speech recognition service, supporting SenseVoice, TeleSpeechASR and more models |
| **自动语言检测**: 自动识别中文、英文、日文、韩文等多种语言，无需手动指定 | **Auto Language Detection**: Automatically detects Chinese, English, Japanese, Korean, and other languages without manual specification |
| **格式兼容**: 支持常见音频格式，便于接入不同来源的录音 | **Format Compatibility**: Supports common audio formats for different recording sources |
| **实时处理**: 适合语音控制、Voice Assistant 等场景 | **Real-Time Processing**: Suitable for voice control, Voice Assistant, and other scenarios |

#### 🌐 HACS 集成汉化 / HACS Integration Localization

| 中文 | English |
|------|---------|
| **自动翻译**: 使用AI自动翻译自定义组件的英文翻译文件为中文 | **Auto Translation**: Use AI to automatically translate custom component English translation files to Chinese |
| **批量处理**: 支持批量处理多个组件的汉化工作 | **Batch Processing**: Supports batch localization for multiple components |
| **智能识别**: 自动识别需要翻译的组件，跳过已存在中文翻译的文件 | **Intelligent Recognition**: Automatically detects components needing translation, skipping already localized ones |

#### 🏗️ Blueprint 蓝图汉化 / Blueprint Localization

| 中文 | English |
|------|---------|
| **一键汉化**: 在集成界面中添加"蓝图汉化"按钮，一键完成所有blueprints的汉化 | **One-Click Localization**: Add "Blueprint Localization" button in the integration interface for one-click translation of all blueprints |
| **原位翻译**: 直接修改原始blueprint文件，不产生额外翻译文件 | **In-Place Translation**: Directly modify original blueprint files without creating additional translation files |
| **智能保护**: 自动保护技术参数和变量，只翻译用户界面文本 | **Smart Protection**: Automatically protect technical parameters and variables, only translating user interface text |
| **递归扫描**: 自动扫描blueprints目录及其子目录中的所有YAML文件 | **Recursive Scanning**: Automatically scan blueprints directory and its subdirectories for all YAML files |
| **状态检测**: 智能检测已汉化文件，避免重复翻译 | **Status Detection**: Intelligently detect already localized files to avoid duplicate processing |
| **完整支持**: 支持复杂的嵌套结构和Home Assistant特殊语法 | **Complete Support**: Support complex nested structures and Home Assistant special syntax |

---

## 📦 安装方法 / Installation

### 方法一：HACS 安装（推荐） / Method 1: HACS Installation (Recommended)

1. **打开 HACS**: 在 Home Assistant 中进入 HACS → 集成 / In Home Assistant, go to HACS → Integrations
2. **搜索集成**: 点击右上角的"探索与下载 repositories"，搜索"ai_hub" / Click "Explore & Download Repositories" in the upper right, search for "ai_hub"
3. **安装集成**: 找到"AI Hub"并点击下载 / Find "AI Hub" and click Download
4. **重启系统**: 重启 Home Assistant 使集成生效 / Restart Home Assistant to activate

### 方法二：手动安装 / Method 2: Manual Installation

1. **下载文件**: 从 [GitHub Releases](https://github.com/ha-china/ai_hub/releases) 下载最新版本的 `ai_hub.zip` / Download the latest `ai_hub.zip` from GitHub Releases
2. **解压文件**: 将 zip 文件解压到 `<HA_CONFIG>/custom_components/ai_hub/` 目录 / Unzip to `<HA_CONFIG>/custom_components/ai_hub/`
3. **重启系统**: 重启 Home Assistant / Restart Home Assistant

> **提示**: 本集成依赖新版的 Conversation/AI Task/子条目框架，建议使用较新的 Home Assistant 版本（>2025.8.0）。
> 
> **Tip**: This integration depends on the new Conversation/AI Task/Entry framework; a newer Home Assistant version (>2025.8.0) is recommended.

---

## 🚀 快速开始 / Quick Start

### 配置向导 / Configuration Wizard

1. **添加集成**: 进入 设置 → 设备与服务 → 集成 → 添加集成，搜索"AI HUB（ai_hub）" / Go to Settings → Devices & Services → Integrations → Add Integration, search "AI HUB (ai_hub)"
2. **配置 API Keys**: 按照向导提示依次配置以下服务 / Follow the wizard to configure:
   - 硅基流动 API Key（用于对话、AI任务、STT）/ SiliconFlow API Key (for Conversation, AI Task, and STT)
3. **验证配置**: 系统会自动验证 API Keys 的有效性 / System will verify your API Keys
4. **完成设置**: 配置完成后，集成会自动创建相应的服务和实体 / Integration will auto-create relevant services and entities

### 子条目配置 / Sub-Entry Configuration

AI Hub 支持子条目配置，可以为不同功能创建独立的配置：

AI Hub supports sub-entry configuration for independent functionality:

| 中文 | English |
|------|---------|
| **AI Hub对话助手**: 用于 Assist 对话代理 | **AI Hub Conversation**: For Assist agents |
| **AI Hub AI任务**: 用于图片生成和结构化数据 | **AI Hub AI Task**: For image generation and structured data |
| **AI Hub TTS语音**: 用于文本转语音 | **AI Hub TTS**: For text-to-speech |
| **AI Hub STT语音**: 用于语音转文本 | **AI Hub STT**: For speech-to-text |
| **AI Hub 集成汉化**: 用于集成汉化 | **AI Hub Localization**: For component translation |
| **AI Hub 蓝图汉化**: 用于蓝图汉化 | **AI Hub Blueprint Localization**: For blueprint translation |

---

## 🔑 账号注册与Token获取 / Account Registration & Token

### 硅基流动 / SiliconFlow

| 项目 | 内容 |
|------|------|
| **用途 / Usage** | 对话助手、AI任务、语音识别 / Conversation, AI Tasks, STT |
| **注册地址 / Register** | [点击注册 / Sign Up Here](https://cloud.siliconflow.cn/i/U3e0rmsr) |

**获取 API Key / Get API Key:**
1. 完成注册并登录 / Register and login
2. 进入控制台 / Go to the dashboard
3. 在 [API密钥管理](https://cloud.siliconflow.cn/account/ak) 页面创建新的 API Key / Create new API Key in the API Key Management page
4. 复制生成的 API Key / Copy your new API Key

> **注意**: Edge TTS 使用微软官方免费接口，不需要单独的 API Key。
> 
> **Note**: Edge TTS uses the official Microsoft free API; no API Key is required.

---

## 📖 使用指南 / Usage Guide

### A. 对话助手使用 / Conversation Assistant

#### 基础对话 / Basic Conversation

1. **切换代理**: 在 Assist 对话页面，将当前代理切换为"AI Hub对话助手" / In Assist, set agent to "AI Hub Conversation"
2. **开始对话**: 直接输入或说出问题，如 / Input/speak questions such as:
   - "打开客厅灯到 60%" / "Turn on the living room light to 60%"
   - "帮我总结今天日程" / "Summarize my schedule for today"
   - "设置一个明早8点的闹钟" / "Set an alarm for 8 AM tomorrow"

#### 图片理解 / Image Understanding

1. **上传图片**: 在支持的前端上传图片或引用摄像头图片 / Upload images or use camera snapshots in a supported frontend
2. **描述问题**: 输入对图片的描述或问题 / Input what you want to ask/analyze about the image
3. **获取分析**: 模型会自动进行视觉分析并回答 / The model analyzes and responds automatically

#### 设备控制 / Device Control

- **启用家居能力**: 在对话助手子条目中启用"LLM Hass API" / Enable "LLM Hass API" in the conversation sub-entry
- **控制与查询**: 可以直接控制设备或查询状态 / Control devices or check their status directly

### B. AI 任务使用 / AI Tasks

#### 图片生成 / Image Generation

通过自动化或服务调用生成图片：

Generate images via automation or service invocation:

```yaml
automation:
  - alias: "生成每日图片 / Generate daily picture"
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - service: ai_hub.generate_image
        data:
          prompt: "美丽的日出风景 / Beautiful sunrise landscape"
          size: "1024x1024"
          model: "Kwai-Kolors/Kolors"
```

#### 任务处理 / Task Assistance

可用于整理信息、生成内容或处理复杂需求：

Useful for organizing information, generating content, or handling more complex requests:

```yaml
# 调用AI任务生成JSON数据 / Call AI task to generate JSON data
service: ai_hub.ai_task
data:
  input: "帮我生成一个包含姓名、年龄、职业的JSON格式数据 / Generate a JSON including name, age, and occupation"
  model: "Qwen/Qwen3-8B"
  temperature: 0.3
```

### C. TTS 语音合成 / Text to Speech

#### 实体方式 / As Entity

1. **选择TTS**: 在媒体播放器中选择"AI Hub TTS语音"作为语音服务 / In a media player, select "AI Hub TTS"
2. **输入文本**: 输入要合成的文本内容 / Enter your text
3. **播放语音**: 系统会自动播放合成的语音 / It will be played automatically

### D. STT 语音识别 / Speech to Text

#### 实体方式 / As Entity

1. **选择STT**: 在麦克风设置中选择"AI Hub STT语音" / In microphone settings, select "AI Hub STT"
2. **开始录音**: 点击录音按钮开始语音输入 / Start recording
3. **获取文本**: 系统会自动将语音转换为文本 / Speech will be converted to text

#### 服务调用 / As Service

```yaml
service: ai_hub.stt_transcribe
data:
  file: "/config/tmp/recording.wav"
  model: "FunAudioLLM/SenseVoiceSmall"
```

### E. 集成汉化 / Localization

```yaml
service: ai_hub.translate_components
data:
  custom_components_path: "custom_components"  # 可选 / Optional, default path
  force_translation: false  # 是否强制重新翻译 / Force re-translate
```

### F. Blueprint 蓝图汉化 / Blueprint Localization

#### 一键汉化（推荐）/ One-Click Localization (Recommended)

1. **添加蓝图汉化子条目**: 在 AI Hub 集成详情页，点击"添加子条目"，选择"AI Hub 蓝图汉化" / In AI Hub integration details page, click "Add Sub-Entry" and select "AI Hub Blueprint Localization"
2. **一键汉化**: 在集成详情页点击"蓝图汉化"按钮 / Click the "Blueprint Localization" button in the integration details page

系统会自动 / The system will automatically:
- 扫描 `/config/blueprints` 目录及其子目录中的所有 YAML 文件
- 智能识别已汉化文件，跳过重复处理
- 保护技术参数、变量名和 Home Assistant 语法
- 直接在原文件上进行汉化，不产生额外文件

#### 服务调用汉化 / Service-Based Localization

```yaml
# 列出所有 Blueprint 文件及其汉化状态 / List all Blueprint files and their status
service: ai_hub.translate_blueprints
data:
  list_blueprints: true  # 仅列出状态，不执行汉化 / Only list status
  target_blueprint: ""  # 留空表示查看所有 / Leave empty to view all
  force_translation: false

# 汉化指定的 Blueprint 文件 / Localize specific Blueprint file
service: ai_hub.translate_blueprints
data:
  list_blueprints: false  # 执行汉化操作 / Perform localization
  target_blueprint: "my_blueprint.yaml"  # 指定文件名（不含路径）
  force_translation: false

# 汉化所有 Blueprint 文件 / Localize all Blueprint files
service: ai_hub.translate_blueprints
data:
  list_blueprints: false
  target_blueprint: ""  # 留空表示汉化所有 / Leave empty to localize all
  force_translation: false
```

## 🤝 参与贡献 / Contributing

欢迎参与项目贡献，帮助完善功能与文档：

You're welcome to contribute — improve features and docs!

### 贡献方式 / How to Contribute

1. **报告问题**: 在 [Issues](https://github.com/ha-china/ai_hub/issues) 中报告 bug 或提出功能建议 / Report Bugs
2. **提交代码**: Fork 项目，修改代码后提交 Pull Request / Fork, modify & PR
3. **完善文档**: 帮助改进文档内容，增加使用示例 / Improve Docs
4. **测试反馈**: 测试新功能并提供反馈 / Feedback

---

## 📄 许可协议 / License

本项目遵循仓库内 [LICENSE](LICENSE) 协议发布。

This project is released under the [LICENSE](LICENSE) in this repository.

### 项目链接 / Project Links

- **项目主页 / Homepage**: [https://github.com/ha-china/ai_hub](https://github.com/ha-china/ai_hub)
- **问题反馈 / Issue Tracker**: [https://github.com/ha-china/ai_hub/issues](https://github.com/ha-china/ai_hub/issues)
- **发布版本 / Releases**: [https://github.com/ha-china/ai_hub/releases](https://github.com/ha-china/ai_hub/releases)
- **HACS 页面 / HACS Page**: [HACS 集成商店 / HACS Integration Shop](https://hacs.xyz/docs/integration/setup)

### 致谢 / Thanks

- 感谢 [knoop7](https://github.com/knoop7) 项目的基础架构 / Thanks to knoop7 for project foundation
- 感谢 [hasscc/hass-edge-tts](https://github.com/hasscc/hass-edge-tts) 项目的 Edge TTS 集成 / Thanks to hass-edge-tts for Edge TTS integration
- 感谢所有贡献者和用户的支持与反馈 / Thanks to all contributors and users for support and feedback

---

## 📱 关注我 / Follow Me

📲 扫描下面二维码，关注我。有需要可以随时给我留言：

Scan the QR code below to follow me! Feel free to leave me a message:

<img src="https://gitee.com/desmond_GT/hassio-addons/raw/main/WeChat_QRCode.png" width="50%" />

---

## ☕ 赞助支持 / Support

如果您觉得我花费大量时间维护这个库对您有帮助，欢迎请我喝杯奶茶，您的支持将是我持续改进的动力！

If you found my work helpful, please buy me a milk tea! Your support motivates continuous improvement!

<div style="display: flex; justify-content: space-between;">
  <img src="https://gitee.com/desmond_GT/hassio-addons/raw/main/1_readme/Ali_Pay.jpg" height="350px" />
</div>

💖 感谢您的支持与鼓励！/ Thank you for your support! 💖
