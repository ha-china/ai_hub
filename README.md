<h1 align="center">AI Hub · 一站式免费AI服务</h1>
<p align="center">
  为了让你体验各种免费的AI服务，本集成不支持任何收费模型及服务，当然你可能会需要申请账号或创建 API Key。<br>
  <strong>开篇致谢：</strong>前人栽树，后人乘凉。没有 <a href="https://github.com/knoop7" target="_blank">knoop7</a> 和 <a href="https://github.com/hasscc/hass-edge-tts" target="_blank">hasscc/hass-edge-tts</a> 这两个项目，就没有本集成，特此感谢！
  
</p>

<p align="center">
  <a href="https://github.com/ha-china/ai_hub/releases"><img src="https://img.shields.io/github/v/release/ha-china/ai_hub" alt="GitHub Version"></a>
  <a href="https://github.com/ha-china/ai_hub/issues"><img src="https://img.shields.io/github/issues/ha-china/ai_hub" alt="GitHub Issues"></a>
  <img src="https://img.shields.io/github/forks/ha-china/ai_hub?style=social" alt="GitHub Forks">
  <img src="https://img.shields.io/github/stars/ha-china/ai_hub?style=social" alt="GitHub Stars"> <a href="README_EN.md">English</a>
</p>

---

## 📋 目录

- [🔧 前置条件](#🔧-前置条件)
- [🌟 功能介绍](#🌟-功能介绍)
- [📦 安装方法](#📦-安装方法)
- [🚀 快速开始](#🚀-快速开始)
- [🔑 账号注册与Token获取](#🔑-账号注册与token获取)
- [📖 使用指南](#📖-使用指南)
- [🔧 服务调用详解](#🔧-服务调用详解)
- [⚙️ 参数配置](#⚙️-参数配置)
- [⚠️ 注意事项](#⚠️-注意事项)
- [🛠️ 故障排除](#🛠️-故障排除)
- [🤝 参与贡献](#🤝-参与贡献)
- [📄 许可协议](#📄-许可协议)
- [📱 关注我](#📱-关注我)
- [☕ 赞助支持](#☕-赞助支持)

---

## 🔧 前置条件

- **Home Assistant**: 2025.8.0 或更高版本
- **网络要求**: 本集成完全依赖互联网服务，稳定的网络连接是必需的

## 🌟 功能介绍

AI Hub 是 Home Assistant 的自定义集成，提供与智谱AI、硅基流动、巴法云的原生对接

如果有些条目你不需要，只需要不填api key即可，或者也可以直接删除就行，后续有需要可以再次添加

### 核心功能

#### 🗣️ 对话助手（Conversation）
- **流式输出**: 实时显示模型回复，提供流畅的对话体验
- **家居控制**: 对接 Home Assistant LLM API，支持控制/查询设备
- **图片理解**: 消息携带图片时自动切换到视觉模型（GLM-4.1V-Thinking）
- **上下文记忆**: 可配置历史消息条数，平衡效果与性能

#### 🤖 AI 任务（AI Task）
- **结构化数据生成**: 指定 JSON 结构，失败提供错误提示
- **图片生成**: 使用 CogView 系列模型生成图片，支持 URL 或 base64 返回
- **多模态支持**: 复用对话消息格式，便于复杂任务处理

#### 🔊 语音合成（TTS，Edge TTS）
- **高质量语音**: 集成微软 Edge TTS，支持多语言、多风格
- **丰富语音库**: 支持晓晓、云健、Aria、Jenny 等多种语音模型
- **参数调节**: 支持语速/音量/音调/风格等参数调整
- **多种格式**: 支持 WAV/MP3/OGG 等音频格式输出

#### 🎤 语音识别（STT，SiliconFlow）
- **高精度识别**: 集成硅基流动性语音识别服务
- **多语言支持**: 支持普通话、英文等多种语言自动检测
- **格式兼容**: 支持 WAV/MP3/FLAC 等多种音频格式
- **实时处理**: 适合语音控制、自动化等场景

#### 🌐 HACS 集成汉化
- **自动翻译**: 使用智谱AI自动翻译自定义组件的英文翻译文件为中文
- **批量处理**: 支持批量处理多个组件的汉化工作
- **智能识别**: 自动识别需要翻译的组件，跳过已存在中文翻译的文件

#### 📱 微信消息推送（Bemfa）
- **实时通知**: 集成巴法云服务，通过微信发送设备状态通知


---

## 📦 安装方法

### 方法一：HACS 安装（推荐）

1. **打开 HACS**: 在 Home Assistant 中进入 HACS → 集成
2. **搜索集成**: 点击右上角的"探索与下载 repositories"，搜索"ai_hub"
3. **安装集成**: 找到"AI 合集(AI HUB)"并点击下载
4. **重启系统**: 重启 Home Assistant 使集成生效

### 方法二：手动安装

1. **下载文件**: 从 [GitHub Releases](https://github.com/ha-china/ai_hub/releases) 下载最新版本的 `ai_hub.zip`
2. **解压文件**: 将 zip 文件解压到 `<HA_CONFIG>/custom_components/ai_hub/` 目录
3. **重启系统**: 重启 Home Assistant

> **提示**: 本集成依赖新版的 Conversation/AI Task/子条目框架，建议使用较新的 Home Assistant 版本（>2025.8.0）。

---

## 🚀 快速开始

### 配置向导

1. **添加集成**: 进入 设置 → 设备与服务 → 集成 → 添加集成，搜索"AI HUB（ai_hub）"
2. **配置 API Keys**: 按照向导提示依次配置以下服务：
   - 智谱 API Key（用于对话、AI任务、HACS集成汉化）
   - 硅基流动性 API Key（用于STT，免费版不支持流式，所以速度略慢）
   - 巴法云API Key（用于微信消息推送）
3. **验证配置**: 系统会自动验证 API Keys 的有效性
4. **完成设置**: 配置完成后，集成会自动创建相应的服务和实体

### 子条目配置

AI Hub 支持子条目配置，可以为不同功能创建独立的配置：

- **AI Hub对话助手**: 用于 Assist 对话代理
- **AI Hub AI任务**: 用于图片生成和结构化数据
- **AI Hub TTS语音**: 用于文本转语音
- **AI Hub STT语音**: 用于语音转文本
- **AI Hub 微信通知**: 用于微信消息推送
- **AI Hub 集成汉化**: 用于集成汉化

---

## 🔑 账号注册与Token获取

### 智谱AI（Zhipu AI）
- **用途**: 对话助手、AI任务、语音合成、语音识别
- **注册地址**: [点击注册](https://www.bigmodel.cn/claude-code?ic=19ZL5KZU1F)
- **获取API Key**:
  1. 完成注册并登录
  2. 进入 [控制台](https://open.bigmodel.cn/usercenter/apikeys)
  3. 点击"创建API Key"
  4. 复制生成的 API Key

### 硅基流动性（SiliconFlow）
- **用途**: 语音识别服务
- **注册地址**: [点击注册](https://cloud.siliconflow.cn/i/U3e0rmsr)
- **获取API Key**:
  1. 完成注册并登录
  2. 进入控制台
  3. 在API管理页面创建新的 API Key
  4. 复制生成的 API Key

### 巴法云（Bemfa）
- **用途**: 微信消息推送
- **注册地址**: [点击注册](http://www.cloud.bemfa.com/u_register.php)
- **获取设备主题**:
  1. 完成注册并登录
  2. 进入 [TCP设备管理](https://cloud.bemfa.com/tcp/index.html)
  3. 创建新的设备或使用现有设备
  4. 复制设备的主题（Topic）

> **注意**: Edge TTS 使用微软官方免费接口，不需要单独的 API Key。

---

## 📖 使用指南

### A. 对话助手使用

#### 基础对话
1. **切换代理**: 在 Assist 对话页面，将当前代理切换为"AI Hub对话助手"
2. **开始对话**: 直接输入或说出问题，如：
   - "打开客厅灯到 60%"
   - "帮我总结今天日程"
   - "设置一个明早8点的闹钟"

#### 图片理解
1. **上传图片**: 在支持的前端上传图片或引用摄像头图片
2. **描述问题**: 输入对图片的描述或问题
3. **获取分析**: 模型会自动进行视觉分析并回答

#### 工具调用
- **启用工具**: 在对话助手子条目中启用"LLM Hass API"
- **控制设备**: 模型可以调用 Home Assistant 工具来控制设备或查询状态

### B. AI 任务使用

#### 图片生成
通过自动化或服务调用生成图片：

```yaml
automation:
  - alias: "生成每日图片"
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - service: ai_hub.generate_image
        data:
          prompt: "美丽的日出风景"
          size: "1024x1024"
          model: "cogview-3-flash"
```

#### 结构化数据生成
生成指定格式的结构化数据：

```yaml
# 调用AI任务生成JSON数据
service: ai_hub.ai_task
data:
  input: "帮我生成一个包含姓名、年龄、职业的JSON格式数据"
  model: "GLM-4-Flash-250414"
  temperature: 0.3
```

### C. TTS 语音合成

#### 实体方式
1. **选择TTS**: 在媒体播放器中选择"AI Hub TTS语音"作为语音服务
2. **输入文本**: 输入要合成的文本内容
3. **播放语音**: 系统会自动播放合成的语音

#### 服务调用
```yaml
service: ai_hub.tts_speech
data:
  text: "欢迎使用AI Hub语音合成服务"
  voice: "zh-CN-XiaoxiaoNeural"
  rate: "+0%"
  volume: "+0%"
  media_player_entity: media_player.living_room_speaker
```

### D. STT 语音识别

#### 实体方式
1. **选择STT**: 在麦克风设置中选择"AI Hub STT语音"
2. **开始录音**: 点击录音按钮开始语音输入
3. **获取文本**: 系统会自动将语音转换为文本

#### 服务调用
```yaml
service: ai_hub.stt_transcribe
data:
  file: "/config/tmp/recording.wav"
  model: "FunAudioLLM/SenseVoiceSmall"
```

### E. 微信消息推送

#### 自动化推送
```yaml
automation:
  - alias: "门窗打开通知"
    trigger:
      - platform: state
        entity_id: binary_sensor.front_door
        to: "on"
    action:
      - service: ai_hub.send_wechat_message
        data:
          device_entity: binary_sensor.front_door
          message: "前门已打开，请注意安全！"
```

### F. 集成汉化

#### 手动汉化
```yaml
service: ai_hub.translate_components
data:
  custom_components_path: "custom_components"  # 可选，默认路径
  force_translation: false  # 是否强制重新翻译
```

---

## 🔧 服务调用详解

AI Hub 提供了丰富的服务接口，可以通过开发者工具的服务面板调用：

### 图片生成服务
```yaml
service: ai_hub.generate_image
data:
  prompt: "图片描述"  # 必填：图像描述
  size: "1024x1024"  # 可选：图像尺寸
  model: "cogview-3-flash"  # 可选：模型选择
```

### 图片分析服务
```yaml
service: ai_hub.analyze_image
data:
  image_file: "/path/to/image.jpg"  # 可选：图像文件路径
  image_entity: "camera.front_door"  # 可选：摄像头实体ID
  message: "分析指令"  # 必填：分析说明
  model: "glm-4.1v-thinking-flash"  # 可选：模型选择
  temperature: 0.3  # 可选：温度参数
  max_tokens: 1000  # 可选：最大令牌数
```

### 文本转语音服务
```yaml
service: ai_hub.tts_speech
data:
  text: "要转换的文本"  # 必填：文本内容
  voice: "zh-CN-XiaoxiaoNeural"  # 可选：语音类型
  speed: 1.0  # 可选：语速
  volume: 1.0  # 可选：音量
  media_player_entity: "media_player.speaker"  # 可选：播放器实体
```

### 语音转文本服务
```yaml
service: ai_hub.stt_transcribe
data:
  file: "/path/to/audio.wav"  # 必填：音频文件路径
  model: "FunAudioLLM/SenseVoiceSmall"  # 可选：STT模型
```

### 创建自动化服务
```yaml
service: ai_hub.create_automation
data:
  description: "自动化描述"  # 必填：自然语言描述
  name: "自动化名称"  # 可选：自动化名称
  area_id: "living_room"  # 可选：区域ID
```

### 发送微信消息服务
```yaml
service: ai_hub.send_wechat_message
data:
  device_entity: "sensor.door_sensor"  # 必填：要监控的实体
  message: "消息内容"  # 必填：消息内容
  group: "通知分组"  # 可选：消息分组
  url: "https://example.com"  # 可选：链接地址
```

### 翻译组件服务
```yaml
service: ai_hub.translate_components
data:
  custom_components_path: "custom_components"  # 可选：自定义组件路径
  force_translation: false  # 可选：是否强制翻译
  target_component: "custom_component_name"  # 可选：指定组件
  list_components: false  # 可选：仅列出组件
```

---

## ⚙️ 参数配置

### 推荐配置（默认值）

#### 对话助手配置
- **模型**: GLM-4-Flash-250414
- **温度**: 0.3（控制回答的随机性）
- **Top P**: 0.5（控制候选词的选择范围）
- **Top K**: 1（限制候选词数量）
- **最大令牌数**: 250
- **历史消息数**: 30（保持上下文的连续性）

#### AI任务配置
- **文本模型**: GLM-4-Flash-250414
- **图片模型**: cogview-3-flash
- **温度**: 0.95（提高创造性）
- **Top P**: 0.7
- **最大令牌数**: 2000

#### TTS配置
- **默认语音**: zh-CN-XiaoxiaoNeural（晓晓）
- **默认格式**: audio-16khz-32kbitrate-mono-mp3
- **语速**: 1.0（正常速度）
- **音量**: 1.0（正常音量）
- **流式输出**: 启用

#### STT配置
- **默认模型**: FunAudioLLM/SenseVoiceSmall
- **支持语言**: 中文（简体）、英文、日文、韩文等15种语言
- **音频格式**: WAV、MP3、FLAC、M4A、OGG、WebM
- **最大文件大小**: 25MB



## ⚠️ 注意事项

### 系统要求
1. **网络依赖**: 本集成完全依赖互联网服务，请确保网络连接稳定
2. **性能要求**: 建议使用性能较好的设备以获得更好的语音处理体验
3. **存储空间**: 语音文件可能需要临时存储空间

### 使用限制
1. **免费模型**:
   - 不支持流式输出，响应速度可能较慢
   - 有调用频率限制
   - 免费额度有限制

2. **API Keys**:
   - 请妥善保管 API Keys，不要泄露
   - 定期检查 API 使用量，避免超额
   - 如遇到 API 错误，请检查 Keys 是否有效

3. **功能限制**:
   - 部分高级功能可能需要较新的 Home Assistant 版本
   - 图片生成和识别需要稳定的网络连接
   - 微信推送需要关注巴法云公众号

### 隐私安全
1. **数据传输**: 所有数据都会通过互联网传输到相应的AI服务
2. **本地存储**: 语音文件可能会临时存储在本地
3. **API安全**: 请确保 API Keys 的安全性

---

## 🛠️ 故障排除

### 常见问题

#### 1. 集成无法添加
**可能原因**:
- Home Assistant 版本过低（需要 2025.8.0+）
- 网络连接问题
- API Keys 无效

**解决方法**:
- 检查 Home Assistant 版本
- 确认网络连接正常
- 验证 API Keys 是否正确

#### 2. 对话助手无响应
**可能原因**:
- 智谱 AI API Key 无效或过期
- 网络连接问题
- 模型选择错误

**解决方法**:
- 检查智谱 AI API Key
- 测试网络连接
- 确认使用的是免费模型

#### 3. TTS 无法播放
**可能原因**:
- Edge TTS 服务不可用
- 媒体播放器选择错误
- 网络连接问题

**解决方法**:
- 检查网络连接到微软服务
- 确认媒体播放器状态正常
- 尝试不同的语音模型

#### 4. STT 识别失败
**可能原因**:
- 硅基流动性 API Key 无效
- 音频文件格式不支持
- 文件过大

**解决方法**:
- 检查硅基流动性 API Key
- 确认音频格式为支持的类型
- 压缩音频文件大小

#### 5. 微信推送不工作
**可能原因**:
- 巴法云设备主题配置错误
- 未关注巴法云公众号
- 网络连接问题

**解决方法**:
- 检查设备主题是否正确
- 确认已关注巴法云公众号
- 测试网络连接

### 日志调试
如果遇到问题，可以查看 Home Assistant 日志：

1. **查看集成日志**:
   ```
   设置 → 系统 → 日志
   ```

2. **启用调试模式**:
   在 `configuration.yaml` 中添加：
   ```yaml
   logger:
     default: info
     logs:
       custom_components.ai_hub: debug
   ```

3. **重启 Home Assistant** 并重新测试功能

### 获取帮助
如果以上方法无法解决问题：
1. **查看 [Issues 页面](https://github.com/ha-china/ai_hub/issues)** 查看是否有类似问题
2. **创建新的 Issue**，请提供：
   - Home Assistant 版本
   - AI Hub 版本
   - 详细的错误描述
   - 相关的日志信息
   - 重现步骤

---

## 🤝 参与贡献

欢迎参与项目贡献，帮助完善功能与文档：

### 贡献方式
1. **报告问题**: 在 [Issues](https://github.com/ha-china/ai_hub/issues) 中报告 bug 或提出功能建议
2. **提交代码**: Fork 项目，修改代码后提交 Pull Request
3. **完善文档**: 帮助改进文档内容，增加使用示例
4. **测试反馈**: 测试新功能并提供反馈



## 📄 许可协议

本项目遵循仓库内 [LICENSE](LICENSE) 协议发布。

### 项目链接
- **项目主页**: [https://github.com/ha-china/ai_hub](https://github.com/ha-china/ai_hub)
- **问题反馈**: [https://github.com/ha-china/ai_hub/issues](https://github.com/ha-china/ai_hub/issues)
- **发布版本**: [https://github.com/ha-china/ai_hub/releases](https://github.com/ha-china/ai_hub/releases)
- **HACS 页面**: [HACS 集成商店](https://hacs.xyz/docs/integration/setup)

### 致谢
- 感谢 [knoop7](https://github.com/knoop7) 项目的基础架构
- 感谢 [hasscc/hass-edge-tts](https://github.com/hasscc/hass-edge-tts) 项目的 Edge TTS 集成
- 感谢所有贡献者和用户的支持与反馈

## 📱 关注我

📲 扫描下面二维码，关注我。有需要可以随时给我留言：

<img src="https://gitee.com/desmond_GT/hassio-addons/raw/main/WeChat_QRCode.png" width="50%" /> 

## ☕ 赞助支持

如果您觉得我花费大量时间维护这个库对您有帮助，欢迎请我喝杯奶茶，您的支持将是我持续改进的动力！

<div style="display: flex; justify-content: space-between;">
  <img src="https://gitee.com/desmond_GT/hassio-addons/raw/main/1_readme/Ali_Pay.jpg" height="350px" />
  <img src="https://gitee.com/desmond_GT/hassio-addons/raw/main/1_readme/WeChat_Pay.jpg" height="350px" />
</div> 💖

感谢您的支持与鼓励！
