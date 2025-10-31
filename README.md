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
- 支持流式/非流式识别，实时拼接文本，低延迟返回。
- 适合实时语音控制、自动化等场景。

### 配置与管理
- 推荐/高级双模式：默认推荐参数即用即走；高级模式开放模型与调参。
- 子条目（Subentry）：在一个集成下，分别管理 Conversation / AI Task / TTS / STT 的参数。

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
3. 配置 Edge TTS 不需要单独 API Key，Edge TTS 使用微软官方免费接口（有每日配额限制）。
4. 成功后会自动创建四个“子条目”：
   - 对话助手 conversation
   - AI 任务 ai_task_data
   - 文本转语音 tts（Edge TTS）
   - 语音转文本 stt（SiliconFlow）
5. 若需调整参数，在对应子条目点击“配置”进入推荐/高级模式配置。


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
