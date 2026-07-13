# Speech-to-Speech 实时语音对话系统

基于 Hugging Face [speech-to-speech](https://github.com/huggingface/speech-to-speech) 后端构建的实时语音对话系统。

## 功能特性

- **实时语音交互**：通过麦克风与 AI 进行自然对话
- **完整处理管道**：VAD → STT → LLM → TTS
- **本地运行**：支持完全离线的本地推理
- **Web 界面**：基于浏览器的现代化 UI

## 技术栈

| 组件 | 技术 |
|------|------|
| 语音活动检测 | Silero-VAD |
| 语音转文字 | Whisper Large V3 / Faster-Whisper |
| 语言模型 | Qwen3-4B (via LM Studio) |
| 文字转语音 | Qwen3-TTS-12Hz-1.7B-CustomVoice |
| 后端框架 | Python, FastAPI, WebSocket |
| 前端 | 原生 JavaScript, Web Audio API |

## 项目结构

```
speach2speach/
├── backend/                    # 后端语音处理核心
│   ├── run_s2s.py             # 后端启动入口
│   └── s2s_runtime/           # 运行时补丁模块
├── hf-realtime-voice/         # 前端 Web UI
│   ├── server.py              # FastAPI 服务器
│   ├── main.js                # 前端逻辑
│   └── index.html             # 单页面 UI
├── models/                    # 本地 AI 模型 (不包含在仓库中)
├── voice-config.json          # 项目配置
└── start-voice-*.ps1/cmd      # 启动脚本
```

## 安装与使用

### 前置要求

- Python 3.11+
- [LM Studio](https://lmstudio.ai/) (用于本地 LLM 推理)
- 麦克风和扬声器

### 安装步骤

1. 克隆仓库
   ```bash
   git clone <repository-url>
   cd speach2speach
   ```

2. 创建虚拟环境并安装依赖
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   pip install -r hf-realtime-voice/requirements.txt
   ```

3. 下载所需模型到 `models/` 目录

4. 启动 LM Studio 并加载 `qwen/qwen3-4b-2507` 模型

### 启动系统

**Windows PowerShell:**
```powershell
# 启动后端
.\start-voice-backend.ps1

# 启动前端 (新终端)
.\start-voice-frontend.ps1
```

**Windows CMD:**
```cmd
start-voice-backend-menu.cmd
start-voice-frontend.cmd
```

访问 `http://localhost:7860` 开始对话。

## 配置说明

编辑 `voice-config.json` 修改配置：

```json
{
  "lmStudio": {
    "baseUrl": "http://127.0.0.1:1234/v1",
    "model": "qwen/qwen3-4b-2507"
  },
  "backend": {
    "port": 8765
  },
  "frontend": {
    "port": 7860
  }
}
```

## 许可证

本项目采用 [Apache License 2.0](LICENSE) 许可证。
