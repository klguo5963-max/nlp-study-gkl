# AGENTS.md — AI 协作上下文

> 本文件是 AI 代理在编码时的说明书。每次会话开始前，AI 应首先读取本文件，
> 理解项目定位、技术栈、当前阶段目标和协作规则。

---

## 1. 项目定位

**一句话**：构建一个中文意图分类 API 服务，对用户指令进行 12 类意图识别。

**用户**：学习 NLP 意图分类的开发者，需在本地跑通并对比不同模型效果。

**核心交付**：在浏览器输入文字 → 点击按钮 → 看到分类结果 + 响应耗时。

---

## 2. 技术栈

| 层 | 技术 | 版本约束 |
|---|---|---|
| 后端 | FastAPI + Uvicorn | Python 3.10+ |
| 传统 ML | scikit-learn, jieba, joblib | 最新稳定版 |
| 深度学习 | PyTorch, HuggingFace transformers | 支持 CPU 推理 |
| LLM | OpenAI 兼容 SDK | 可配置 base_url 指向 Ollama 或云端 |
| 前端 | 纯 HTML + CSS + JS | 无构建工具，无 npm |
| 配置 | `config.py` 单文件 | 所有可调参数集中管理 |
| 数据 | CSV 文件（tab 分隔） | 12 类，12100 条样本 |

**关键设计约束**：
- 全部本地可运行，不依赖外部云服务（LLM 除外，但可通过 Ollama 本地化）
- 前端不可引入 Node.js / npm / 构建工具
- 异常捕获在模型层完成，不泄漏到 FastAPI 顶层
- 配置项统一在 `config.py`，各模块通过 `from config import ...` 引用

---

## 3. 项目结构（最终目标）

```
01-intent-classify/
├── main_cors.py           # 入口（带 CORS）
├── config.py              # 配置
├── data_schema.py         # Schema
├── logger.py              # 日志
├── requirements.txt
├── model/
│   ├── regex_rule.py
│   ├── tfidf_ml.py
│   ├── bert.py
│   └── prompt.py
├── training_code/
│   ├── train_tfidf.py
│   └── train_bert.py
├── assets/dataset/
├── frontend/
├── test/
├── doc/
│   ├── SPEC.md
│   ├── API.md
│   └── AGENTS.md (本文件)
└── README.md
```

---

## 4. 版本规划

| 版本 | 名字 | 核心任务 | 验证标准 |
|---|---|---|---|
| v0.1 | 项目骨架 | 目录、config、data_schema、logger、空白 FastAPI+健康检查 | `curl localhost:8000` 返回 JSON |
| v0.2 | 正则模型 | regex_rule.py + POST /v1/text-cls/regex | 输入"播放歌曲"返回 `Music-Play` |
| v0.3 | 前端联调 | 前端模型选择 + 调用接口 + 展示结果 | 浏览器输入文本看到分类结果 |
| v0.4 | TF-IDF | train_tfidf.py + 推理 endpoint | TF-IDF endpoint 可用 |
| v0.5 | BERT | train_bert.py + 推理 endpoint | BERT endpoint 可用 |
| v0.6 | LLM | prompt.py + LLM endpoint | LLM endpoint 可用 |
| v0.7 | 前端完整版 | 四模型选择 + 对比展示 + 性能指标 | 像旧项目一样完整可用 |

---

## 5. 协作规则

1. **先文档，后代码**：每个版本开始前，先确认该版本的文档（做什么/不做什么/怎么验证），得到确认后再编码
2. **单轮次单任务**：一轮对话只做一个子任务，完成后停下来等确认
3. **不改现有接口**：新增改动不得影响已有功能。新增文件只能新增代码；修改已有文件时必须确保已有功能不受干扰（例如新增 import 后不能引发 ModuleNotFoundError，新增 endpoint 不能覆盖已有路由等）。
4. **验证驱动**：每个任务必须有明确的验证方法（curl / 浏览器 / 测试脚本）。验证范围应包括增量改动涉及的端到端链路。
5. **文档同步**：每完成一个版本，更新本文件中的勾选框状态

## 6. 服务管理规范

每次重启服务时，注意以下事项：

1. **后端（Uvicorn）**和**前端（http.server）**是两个独立的 Python 进程。
   - 后端：`python -m uvicorn main_cors:app --host 0.0.0.0 --port 8000`
   - 前端：`python -m http.server 8001 --directory frontend/`
2. **不要无差别杀 Python 进程**。`Get-Process -Name "python" | Stop-Process -Force` 会把前端 HTTP server 也杀掉。
   - 应指定 PID 杀进程，或分别管理前后端进程。
3. 启动命令中使用 `Start-Process -NoNewWindow` 在后台运行。
4. 访问前端 URL 为 `http://localhost:8001/`，前端 JS 中 API 请求指向 `http://localhost:8000`。

---

## 6. 当前进度

- [x] 项目启动卡
- [x] doc/SPEC.md
- [x] doc/API.md
- [x] doc/AGENTS.md（本文件）
- [x] README.md
- [ ] **v0.1 项目骨架** — 待开启
- [ ] v0.2 正则模型
- [ ] v0.3 前端联调
- [ ] v0.4 TF-IDF
- [ ] v0.5 BERT
- [ ] v0.6 LLM
- [ ] v0.7 前端完整版
