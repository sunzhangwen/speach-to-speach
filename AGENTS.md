# Speech-to-Speech 项目摘要 (Agent 参考)

> **一句话说明**：实时语音对话系统 —— 用户说话 → VAD → STT → LLM → TTS → AI 语音回复，支持完全本地离线推理。

---

## 目录结构

```
speach2speach/
├── backend/                         # 后端语音处理核心
│   ├── run_s2s.py                   # 后端入口点
│   ├── s2s_runtime/                 # 运行时补丁
│   │   ├── local_silero.py         # Silero-VAD 本地缓存重定向
│   │   ├── qwen3_cpu_backend.py    # Qwen3-TTS CPU 适配器
│   │   └── whisper_short_output.py # Whisper 短输出修复
│   └── tests/                       # 单元测试
├── hf-realtime-voice/               # 前端 Web UI
│   ├── server.py                    # FastAPI 服务器
│   ├── index.html                   # 单页面应用
│   ├── main.js                      # 前端状态机与逻辑
│   ├── style.css                    # 样式与动画
│   ├── auth.py                      # HF OAuth 认证
│   ├── limiter.py                   # 使用量限制 (SQLite)
│   ├── requirements.txt             # 前端依赖
│   ├── ui/                          # UI 模块 (account, chat, dom)
│   ├── ws/                          # WebSocket 客户端 (codec, orb-visualizer)
│   └── worklets/                    # AudioWorklet 处理器 (mic-capture, audio-playback)
├── models/                          # 本地 AI 模型 (不在 git 中)
├── voice-config.json                # 项目统一配置
├── start-voice-backend.ps1         # 后端启动脚本 (PowerShell)
├── start-voice-backend-menu.cmd    # 后端启动菜单 (CMD)
├── start-voice-frontend.ps1        # 前端启动脚本 (PowerShell)
└── start-voice-frontend.cmd        # 前端启动脚本 (CMD)
```

---

## 快速上手

### 环境要求

- Python 3.11+
- LM Studio（本地 LLM 推理）
- 麦克风 + 扬声器

### 首次配置

```bash
# 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 安装前端依赖
pip install -r hf-realtime-voice/requirements.txt
```

### 启动命令

```powershell
# 终端 1: 启动后端
.\start-voice-backend.ps1

# 终端 2: 启动前端
.\start-voice-frontend.ps1
```

**CMD 启动：**
```cmd
start-voice-backend-menu.cmd    # 带模式选择菜单
start-voice-frontend.cmd
```

### 后端模式选择

| 模式 | 说明 |
|------|------|
| `-Device cpu -CpuProfile fast` | Faster-Whisper (int8)，速度快 |
| `-Device cpu -CpuProfile quality` | Whisper Large V3 (float32)，质量高 |
| `-Device gpu` | GPU (CUDA) 加速 |
| `-Online` | 允许从 HuggingFace Hub 下载模型 |

### 运行测试

```bash
cd backend
python -m pytest tests/
```

### 访问地址

- 前端 UI：`http://localhost:7860`
- 后端 WebSocket：`ws://localhost:8765`

---

## 关键配置

### voice-config.json

```json
{
  "lmStudio": {
    "baseUrl": "http://127.0.0.1:1234/v1",  // LM Studio API 地址
    "model": "qwen/qwen3-4b-2507"           // LLM 模型名称
  },
  "backend": {
    "port": 8765                             // 后端 WebSocket 端口
  },
  "frontend": {
    "port": 7860                             // 前端 HTTP 端口
  }
}
```

### 环境变量（启动脚本自动设置）

| 变量 | 说明 |
|------|------|
| `PYTHONPATH` | 指向 backend 目录 |
| `VOICE_CONFIG_PATH` | 指向 voice-config.json |
| `HF_HUB_OFFLINE=1` | 离线模式（默认启用） |

---

## 技术栈速查

| 组件 | 技术 |
|------|------|
| VAD | Silero-VAD (torch.hub) |
| STT | Whisper Large V3 / Faster-Whisper (CTranslate2) |
| LLM | Qwen3-4B (via LM Studio OpenAI 兼容 API) |
| TTS | Qwen3-TTS-12Hz-1.7B-CustomVoice (qwen-tts) |
| 后端框架 | FastAPI + Uvicorn + WebSocket |
| 前端 | Vanilla JS + Web Audio API + AudioWorklet |
| 认证 | Hugging Face OAuth (huggingface_hub[oauth]) |
| 存储 | SQLite (使用量统计) |
| 传输协议 | WebSocket (OpenAI Realtime GA 协议) |
| 音频格式 | PCM16, 16kHz 输入 / 24kHz 输出 |

---

## 架构详解

### 后端 (backend/)

后端基于 Hugging Face 的 `speech-to-speech` 开源框架，通过三个运行时补丁定制：

- **`local_silero.py`**：拦截 `torch.hub.load("snakers4/silero-vad", ...)` 调用，重定向到项目本地缓存 `.cache/torch/hub/`，实现离线加载 VAD 模型。
- **`qwen3_cpu_backend.py`**：为 Qwen3-TTS 提供 CPU 后端适配器 (`NativeQwen3TTSAdapter`)，在 CPU 模式下使用原生 `qwen-tts` 库替代默认的 CUDA 实现。
- **`whisper_short_output.py`**：修复 Whisper 短输出/空输出时的索引错误，安全处理单 token 或无文本的生成结果。

### 前端 (hf-realtime-voice/)

前端是纯原生 JavaScript 单页应用，核心组件：

- **`main.js`**：应用状态机（idle → connecting → listening → user-speaking → processing → ai-speaking），管理设置、工具、队列、音量门等。
- **`ws/s2s-ws-client.js`**：WebSocket 客户端，实现 OpenAI Realtime GA 协议，处理音频收发、会话管理、工具调用。
- **`worklets/mic-capture.js`**：AudioWorklet 麦克风采集处理器。
- **`worklets/audio-playback.js`**：AudioWorklet 音频播放处理器。
- **`ui/chat.js`**：对话历史面板和气泡消息。
- **`ui/account.js`**：HF 登录芯片和每日限额弹窗。
- **`ui/dom.js`**：DOM 工具函数。
- **`server.py`**：FastAPI 服务器，提供静态文件、搜索代理（`/api/search`）、会话代理（`/api/session`）、队列管理、使用量计量。
- **`auth.py`**：HF OAuth 认证和用户身份解析（anon/free/pro/org 四个层级）。
- **`limiter.py`**：每日对话时长预算，基于 SQLite 的分块预留机制。

### 通信流程

```
浏览器 ──WebSocket──→ 后端 (ws://localhost:8765/v1/realtime)
  │
  ├── session.update (voice, instructions, tools)
  ├── input_audio_buffer.append (PCM16 16kHz base64)
  │
  ←── session.created
  ←── response.output_audio.delta (PCM16 24kHz base64)
  ←── response.text.delta (转录文本)
  ←── response.function_call (工具调用)
```

---

## 常见修改场景速查

| 需求 | 关键文件 |
|------|----------|
| 修改 LLM 模型/地址 | `voice-config.json` |
| 修改后端端口 | `voice-config.json` → backend.port |
| 修改前端端口 | `voice-config.json` → frontend.port |
| 修改前端 UI 界面 | `hf-realtime-voice/index.html` + `main.js` + `style.css` |
| 修改 WebSocket 通信 | `hf-realtime-voice/ws/s2s-ws-client.js` |
| 修改音频采集/播放 | `hf-realtime-voice/worklets/mic-capture.js` / `audio-playback.js` |
| 修复 Whisper 短输出问题 | `backend/s2s_runtime/whisper_short_output.py` |
| 修改 TTS CPU 后端 | `backend/s2s_runtime/qwen3_cpu_backend.py` |
| 修改 Silero-VAD 缓存路径 | `backend/s2s_runtime/local_silero.py` |
| 添加前端工具/功能 | `hf-realtime-voice/main.js` (tools 部分) |
| 修改认证逻辑 | `hf-realtime-voice/auth.py` |
| 修改使用量限制 | `hf-realtime-voice/limiter.py` |
| 修改搜索代理 | `hf-realtime-voice/server.py` (/api/search) |
| 修改队列/会话逻辑 | `hf-realtime-voice/server.py` (/api/session, /api/queue) |
| 修改音量门控 | `hf-realtime-voice/main.js` (noise gate 部分) |
| 修改摄像头快照工具 | `hf-realtime-voice/main.js` (camera_snapshot) |

---

## 注意事项

- `models/` 目录不在 git 中，需单独下载模型文件
- 后端启动前需先启动 LM Studio 并加载 `qwen/qwen3-4b-2507` 模型
- 启动脚本为 Windows 专用（PowerShell / CMD）
- 默认启用离线模式 (`HF_HUB_OFFLINE=1`)，如需下载模型需加 `-Online` 参数
- 测试目录：`backend/tests/`
- 前端依赖：`hf-realtime-voice/requirements.txt`
- 许可证：Apache License 2.0
- 前端使用 Inter + Geist Mono 字体（Google Fonts CDN）
- 前端支持三种连接模式：LB 代理模式、Deploy 固定 URL 模式、用户直连模式
- 工具系统支持 web_search（需要 Serper API key）和 camera_snapshot
