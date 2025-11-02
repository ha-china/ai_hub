<h1 align="center">AI Hub · 一站式免费AI服务</h1>
<p align="center">
  为了让你体验各种免费的AI服务，本集成不支持任何收费模型及服务，当然你可能会需要申请账号或创建 API Key。<br>
  <strong>开篇致谢：</strong>前人栽树，后人乘凉。没有 <a href="https://github.com/knoop7" target="_blank">knoop7</a> 和 <a href="https://github.com/hasscc/hass-edge-tts" target="_blank">hasscc/hass-edge-tts</a> 这两个项目，就没有本集成，特此感谢！
</p>

</p>
<p align="center">
  <a href="https://github.com/ha-china/ai_hub/releases"><img src="https://img.shields.io/github/v/release/ha-china/ai_hub" alt="GitHub Version"></a>
  <a href="https://github.com/ha-china/ai_hub/issues"><img src="https://img.shields.io/github/issues/ha-china/ai_hub" alt="GitHub Issues"></a>
  <img src="https://img.shields.io/github/forks/ha-china/ai_hub?style=social" alt="GitHub Forks">
  <img src="https://img.shields.io/github/stars/ha-china/ai_hub?style=social" alt="GitHub Stars"> <a href="README_EN.md">English</a>
</p>

---

AI Hub 是 Home Assistant 的自定义集成，提供与智谱大模型的原生对接：
- 对话助手（Conversation）：作为 Assist 对话代理，支持流式回答、家居控制工具调用、图片理解。
- AI 任务（AI Task）：生成结构化数据、生成图片（CogView 系列）。
- 语音合成（TTS）：集成 Edge TTS，支持高质量语音合成（包含多语音、多风格、多参数）。
- 语音识别（STT）：集成硅基流动性 SiliconFlow 语音识别，实现快速准确的语音转文本。
- 集成服务：图片分析、图片生成、TTS 播放、STT 转写。
- AI 自动化（实验特性）：用自然语言生成并写入 automations.yaml，自动重载。
- HACS 集成汉化：使用智谱AI自动翻译自定义集成的英文翻译文件为中文。
- 微信消息推送：集成巴法云服务，通过微信发送设备状态通知。
> 注意：本集成全依赖互联网，因此，你的网络与设备性能决定了集成体验。
## 功能特色

### 对话助手（Conversation）
- 流式输出：实时显示模型回复。
- 控制家居：对接 Home Assistant LLM API，模型可调用“控制/查询”等工具。
- 图片理解：消息携带图片时自动切换到视觉模型（优先使用更强的免费 GLM-4.1V-Thinking）。
- 上下文记忆：可配置历史消息条数，平衡效果与性能。
- 可选联网搜索：高级模式可开启 web_search 工具。

### AI 任务（AI Task）
- 结构化数据生成：可指定 JSON 结构（失败有错误提示）。
- 图片生成：对接 images/generations，支持 URL 或 base64 返回，统一转为 PNG。
- 附件支持：复用对话消息格式，便于多模态任务。

### 语音合成（TTS，Edge TTS）
- 集成 Edge TTS，支持多语言、多风格、多类型语音合成。
- 丰富的语音模型资源（如 Xiaoxiao、Yunyang、Yunjian、Aria、Jenny、Guy 等）。
- 支持调整语速/音量/音调/风格等参数。
- 支持流式/非流式：按需分片或完整返回音频。
- 默认输出 WAV（支持 PCM/MP3/OGG 等 Edge TTS 格式）。

### 语音识别（STT，SiliconFlow）
- 集成硅基流动性（SiliconFlow）高兼容性的语音识别服务。
- 支持上传 WAV（推荐 16k/16bit 单声道，自动标准化）。
- 支持普通话/英文等主流语种，自动检测。
- 支持非流式识别。
- 适合实时语音控制、自动化等场景。

### HACS 集成汉化
- 自动翻译自定义集成的英文翻译文件为中文，提升用户体验。
- 使用智谱AI进行高质量翻译，支持批量处理多个组件。
- 可配置自定义组件目录路径，灵活适配不同安装方式。

### 微信消息推送 （Wechat, Bemfa）
- 集成巴法云服务，通过微信发送设备状态通知。
- 支持发送文本消息和图片消息，满足不同通知需求。
- 配置简单，只需获取巴法云设备主题即可使用。


### 配置与管理
- 推荐/高级双模式：默认推荐参数即用即走；高级模式开放模型与调参。
- 子条目（Subentry）：在一个集成下，分别管理 Conversation / AI Task / TTS / STT / 微信消息推送 等服务。

## 安装

### 方式一：HACS（推荐）
1. 在 HACS 中搜索并安装“ai_hub”。
2. 重启 Home Assistant。

### 方式二：手动安装
1. 将仓库中的 `custom_components/ai_hub` 目录复制到 Home Assistant 配置目录下的 `custom_components/`。
2. 重启 Home Assistant。

提示：本集成依赖新版的 Conversation/AI Task/子条目框架，建议使用较新的 Home Assistant 版本（>2025.8.0）。

## 快速开始（配置向导）
1. 进入 设置 → 设备与服务 → 集成 → 添加集成，搜索“智谱清言（ai_hub）”。
2. 按指引输入智谱 API Key（可在 [此处](https://open.bigmodel.cn/usercenter/apikeys) 获取）。
   - 如果还没有智谱的账号，可以先进行[注册](https://www.bigmodel.cn/claude-code?ic=19ZL5KZU1F)。
3. 按指引输入硅基流动性 API Key 
   - 如果还没有硅基的账号，可以先进行[注册](https://cloud.siliconflow.cn/i/U3e0rmsr)，通过邀请链接系统可送你15块余额。
4. 按指引输入巴法云设备主题（可在 [此处](https://bemfa.com) 获取）。
   - 如果还没有巴法的账号，可以先进行[注册](https://bemfa.com/register)。
5. 配置 Edge TTS 不需要单独 API Key，Edge TTS 使用微软官方免费接口。
6. 若需调整参数，在对应子条目点击“配置”进入推荐/高级模式配置。


## 使用指南

### A. 对话助手（Assist 对话代理）
- 在 Assist 对话页面，将当前代理切换为“智谱对话助手”。
- 直接说/输：“打开客厅灯到 60%”、“帮我总结今天日程”。
- 携带图片：在支持的前端上传或引用图片，模型会自动进行视觉分析并回答。
- 工具调用：在子条目启用 LLM Hass API 后，模型可调用 Home Assistant 工具以控制设备/查询状态。

### B. AI 任务（结构化数据）
- 在卡片或自动化中调用 AI Task 生成数据：
  - 文本→结构化 JSON：任务定义结构后，系统会尝试将回复解析为 JSON。
  - 若解析失败，会返回错误，便于调参或重试。

### C. AI 任务（生成图片）
- 使用服务 ai_hub.generate_image 生成图片（CogView）：

### D. 服务调用

AI Hub 提供了多种服务，可以通过开发者工具的服务面板调用：

#### 图片生成 (ai_hub.generate_image)
- **描述**: 使用智谱AI CogView模型生成图像
- **参数**: 
  - `prompt`: 图像描述（必填）
  - `size`: 图像尺寸（可选，默认1024x1024）
  - `model`: 模型选择（可选，默认cogview-3-flash）

#### 图片分析 (ai_hub.analyze_image)
- **描述**: 使用智谱AI分析图像内容
- **参数**:
  - `image_file`: 图像文件路径
  - `image_entity`: 摄像头实体ID
  - `message`: 分析指令（必填）
  - `model`: 模型选择（可选）
  - `temperature`: 温度参数（可选）
  - `max_tokens`: 最大令牌数（可选）

#### 文本转语音 (ai_hub.tts_speech)
- **描述**: 使用智谱AI将文本转换为语音
- **参数**:
  - `text`: 文本内容（必填）
  - `voice`: 语音类型（可选，female/male）
  - `speed`: 语速（可选）
  - `volume`: 音量（可选）
  - `media_player_entity`: 媒体播放器实体ID（可选）

#### 语音转文本 (ai_hub.stt_transcribe)
- **描述**: 使用SiliconFlow将语音文件转换为文本
- **参数**:
  - `file`: 音频文件路径（必填）
  - `model`: STT模型选择（可选）

#### 创建自动化 (ai_hub.create_automation)
- **描述**: 通过自然语言描述创建Home Assistant自动化
- **参数**:
  - `description`: 自动化描述（必填）
  - `name`: 自动化名称（可选）
  - `area_id`: 区域ID（可选）

#### 翻译组件 (ai_hub.translate_components)
- **描述**: 翻译所有自定义组件的英文翻译为中文
- **参数**:
  - `custom_components_path`: 自定义组件目录路径（可选，默认custom_components）

#### 发送微信消息 (ai_hub.send_wechat_message)
- **描述**: 通过巴法云发送微信消息通知
- **参数**:
  - `device_entity`: 要监控状态的实体ID（必填）
  - `message`: 消息内容（必填）
  - `group`: 消息分组（可选）
  - `url`: 链接地址（可选）
  - 参数：prompt（必填）、size（默认 1024x1024）、model（默认 cogview-3-flash）。
  - 返回：image_url 或 image_base64（内部自动转为 PNG 以便前端/卡片使用）。

### D. 图片分析服务（图像理解）
- 使用服务 ai_hub.analyze_image：
  - 参数：image_file 或 image_entity 二选一、message（分析说明）、model（默认 glm-4v-flash）。
  - 支持 stream（流式）返回增量内容。

### E. 文本转语音（TTS 实体与服务，Edge TTS）
- 作为 TTS 实体在前端选择“Edge TTS”，输入文本播放。
- 或调用服务 ai_hub.tts_speech：
  - 参数：text、voice（例如 zh-CN-XiaoxiaoNeural，详细请见 Edge 在线语音列表）、rate（语速）、volume（音量）、pitch（音调）、style（表达风格）、format（音频格式，例如 audio-16khz-32kbitrate-mono-mp3）、stream（流式）。
  - 非流式：直接返回完整音频；流式：分片返回音频块并自动拼接为完整音频。

### F. 语音转文本（STT 实体与服务，SiliconFlow）
- 作为 STT 实体使用：前端/麦克风采集的音频将被标准化为 WAV 后上传到 SiliconFlow STT。
- 或调用服务 ai_hub.stt_transcribe：
  - 参数：audio_file（WAV）、language（默认 zh）、stream。
  - 返回：识别到的文本（流式会持续拼接，直至 [DONE]）。

## 参数与模型（默认与推荐）
- 对话（Conversation）默认：
  - 模型：GLM-4-Flash-250414
  - temperature: 0.3，top_p: 0.5，top_k: 1，max_tokens: 250，history: 30
- AI 任务默认：
  - 文本模型：GLM-4-Flash-250414（temperature 0.95 / top_p 0.7 / max_tokens 2000）
  - 图片模型：cogview-3-flash（size 默认 1024x1024）
- 视觉模型：GLM-4.1V-Thinking（更强的免费模型）
- TTS 默认：集成 Edge TTS，推荐 voice zh-CN-XiaoxiaoNeural，格式 audio-16khz-32kbitrate-mono-mp3，rate 1.0，volume 1.0，stream true
- STT 默认：采用 SiliconFlow，language zh，stream true


## 参与贡献
欢迎提交 Issue 与 PR，帮助完善功能与文档：
- 代码与文档：https://github.com/ha-china/ai_hub
- 问题反馈：https://github.com/ha-china/ai_hub/issues

## 许可协议
本项目遵循仓库内 LICENSE 协议发布。