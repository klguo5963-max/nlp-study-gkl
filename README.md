# 意图分类服务（多模型）

## 项目一句话

构建一个中文意图分类 API 服务，对用户指令进行 12 类意图识别，支持正则匹配、TF-IDF、BERT、LLM 四种算法，提供统一 REST API 和 Web 测试界面。

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动后端
uvicorn main_cors:app --reload --host 0.0.0.0 --port 8000

# 3. 启动前端（另一个终端）
python -m http.server 8001
```

- API 文档：http://localhost:8000/docs
- Web 界面：http://localhost:8001/frontend/

## 核心功能

1. 四种分类模型：正则匹配、TF-IDF+SVM、BERT、LLM（动态 Few-shot）
2. 统一 REST API，每种模型对应独立 endpoint
3. Web 前端界面，支持模型对比测试

## 项目结构

```
01-intent-classify/
├── main_cors.py           # FastAPI 应用入口（带 CORS）
├── config.py              # 集中配置（规则/路径/参数）
├── data_schema.py         # 请求/响应 Pydantic 模型
├── logger.py              # 日志配置
├── requirements.txt       # Python 依赖
│
├── model/                 # 四种分类模型实现
│   ├── regex_rule.py      #   正则匹配
│   ├── tfidf_ml.py        #   TF-IDF + SVM
│   ├── bert.py            #   BERT
│   └── prompt.py          #   LLM 动态 Few-shot
│
├── training_code/         # 模型训练脚本
│   ├── train_tfidf.py
│   └── train_bert.py
│
├── assets/                # 数据与模型权重
│   ├── dataset/           #   训练数据 + 停用词
│   ├── weights/           #   训练后的模型文件
│   └── models/            #   预训练模型
│
├── frontend/              # Web 前端（纯静态）
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── test/                  # 测试文件
│   └── data.json          #   压测请求样例
│
└── doc/                   # 项目文档
    ├── SPEC.md            #   项目规格说明书
    ├── API.md             #   API 接口设计
    └── AGENTS.md          #   AI 协作上下文
```

## 分类 API

| 接口 | 模型 | 速度 | 精度 | 依赖 |
|---|---|---|---|---|
| POST /v1/text-cls/regex | 正则匹配 | <10ms | 低 | 无 |
| POST /v1/text-cls/tfidf | TF-IDF+SVM | <50ms | 中 | scikit-learn, jieba |
| POST /v1/text-cls/bert | BERT | ~200ms | 高 | transformers, torch |
| POST /v1/text-cls/gpt | LLM | ~1-2s | 高 | OpenAI 兼容接口 |

## 技术栈

- **后端框架**：FastAPI + Uvicorn
- **传统 ML**：scikit-learn, jieba, joblib
- **深度学习**：PyTorch, HuggingFace Transformers
- **LLM**：OpenAI 兼容 SDK（本地 Ollama 或云端 API）
- **前端**：纯 HTML + CSS + JavaScript（无构建工具）
- **配置管理**：单文件 `config.py` 集中管理
