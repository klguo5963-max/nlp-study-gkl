# 修复与优化计划 · v0.9 ~ v0.12

> 基于代码审查（结构/边界/风险）和需求满足度分析，
> 将修复项按优先级拆为多个独立子版本，每版只做一件事。

---

## 总原则

1. **每版一件事**：一个版本只解决一个问题，完成后验证通过才能进下一版
2. **不改现有接口**：后端 endpoint 签名、前端 id/函数名不动
3. **回归测试**：每个版本完成后必须跑回归测试（4 个 endpoint + 全部对比 + 清空 + 边界保护）
4. **先修后增**：修复类版本（v0.9 ~ v0.11）做完之后，才考虑功能新增类版本（v0.12）

---

## 版本规划

| 版本 | 类型 | 问题 | 改动量 | 风险等级 |
|---|---|---|---|---|
| v0.9 | 修复 | LLM 模块级 import 导致服务启动时必须加载 LLM 依赖 | 1 个文件 | **高** |
| v0.10 | 修复 | endpoint 异常处理 4 处重复 + traceback 泄漏到前端 | 1 个文件 | 高 |
| v0.11 | 修复 | `fillCard` 从 DOM 反读占位卡片 / LLM 检索缓存 | 2 个文件 | 中 |
| v0.12 | 优化 | BERT 全量重训 / 置信度分数展示 / 混淆矩阵 | 多个 | 低 |

---

## 版本详情

### v0.9 — LLM 惰性初始化

#### 问题

`model/prompt.py` 中有 20 多行代码在**模块加载时**执行：
- `load_dotenv()`
- `OpenAI()` 客户端初始化
- `load(TFIDF_MODEL_PKL_PATH)` 加载模型权重
- `pd.read_csv(DATASET_PATH)` 读取 12100 条训练数据
- jieba 分词 + TF-IDF 变换

后果：用户不用 LLM 也必须在 `requirements.txt` 中安装 openai、pandas 等依赖，
且启动服务时若 TF-IDF 模型或 `.env` 文件缺失，整个服务 crash。

#### 改动范围

只改 `model/prompt.py`，不动其他文件。

#### 具体做法

1. 把模块顶层的所有初始化代码（`_client`、`_tfidf`、`_df`、`_train_texts`、`_train_labels`、`_train_vecs`）移到全局变量声明处，初始值设为 `None`
2. 新增一个 `_lazy_init()` 函数，用 `nonlocal` 或模块级 `if xxx is None:` 惰性初始化所有资源
3. 在 `model_for_llm()` 和 `_classify_single()` 的入口处，先调用 `_lazy_init()`
4. 如果 `.env` 文件缺失，`_lazy_init()` 内部 catch 异常，`model_for_llm` 返回 `["Other"]` 并记录 error 日志（不崩溃）

#### 不动的内容

- `model_for_llm` 的函数签名（`request_text: Union[str, list[str]]`）
- `_classify_single` 的内部逻辑
- `_retrieve_similar` 的逻辑
- Prompt 模板

#### 验证清单

| # | 操作 | 预期结果 |
|---|---|---|
| 1 | 正常启动后端 | 服务正常，`GET /` 返回 200 |
| 2 | 调用 regex/tfidf/bert 三个 endpoint | 均正常返回 |
| 3 | 调用 gpt endpoint（.env 存在） | 正常返回分类结果 |
| 4 | 临时备份 `.env`，启动服务，调 gpt | `error_msg` 非 "ok"，不崩溃 |
| 5 | 恢复 `.env`，调 gpt | 恢复正常 |

---

### v0.10 — endpoint 异常处理提取 + traceback 截断

#### 问题

`main_cors.py` 中 4 个 endpoint 都有完全相同的 try/except 块：
```python
except Exception as e:
    resp.classify_result = "" if isinstance(req.request_text, str) else []
    resp.error_msg = traceback.format_exc()
```
复制了 4 次。同时 `traceback.format_exc()` 会把完整 Python 堆栈传给前端。

#### 改动范围

只改 `main_cors.py`。

#### 具体做法

1. 在 `main_cors.py` 中新增一个工具函数 `_build_error_response(resp, req)`：
   ```python
   def _build_error_response(resp: TextClassifyResponse, req: TextClassifyRequest) -> None:
       resp.classify_result = "" if isinstance(req.request_text, str) else []
       resp.error_msg = "模型分类异常，请查看服务端日志"
       logger.error(traceback.format_exc())  # 完整堆栈只写日志
   ```
2. 4 个 endpoint 的 except 块统一改为：
   ```python
   except Exception:
       _build_error_response(resp, req)
   ```
3. 删除重复的 `import traceback`（保留一份即可）

#### 不动的内容

- endpoint 路由 `/v1/text-cls/{regex|tfidf|bert|gpt}`
- `TextClassifyRequest` / `TextClassifyResponse` schema
- 函数名 `regex_classify` / `tfidf_classify` / `bert_classify` / `llm_classify`
- 正常路径的返回逻辑

#### 验证清单

| # | 操作 | 预期结果 |
|---|---|---|
| 1 | 正常调用所有 4 个 endpoint | 全部返回正常结果，error_msg="ok" |
| 2 | 模拟异常（如删除 bert 模型文件），调 bert endpoint | HTTP 200，error_msg 不包含 Python 堆栈，而是中文提示 |
| 3 | 检查服务端日志 | 完整堆栈记录在日志中 |

---

### v0.11 — fillCard 重构 + LLM 缓存

#### 问题 A：fillCard 从 DOM 反读

`fillCard` 中 `document.querySelector('[data-key="${k}"]')?.outerHTML` 读取当前 DOM 中的占位卡片，
如果 DOM 被提前清空，会回退到硬编码字符串。
占位卡片的 HTML 模板在 `renderPlaceholderCards` 和 `fillCard` 两处维护。

#### 问题 B：LLM 检索结果未缓存

`_retrieve_similar` 每次调用都做 12100 条余弦相似度计算，
对相同输入重复计算。

#### 改动范围

- `frontend/script.js`：提取占位卡片 HTML 生成函数，`fillCard` 改为调用它
- `model/prompt.py`：为 `_retrieve_similar` 加 `lru_cache`

#### 具体做法

**A — 提取占位卡片函数**：
1. 当前 `renderPlaceholderCards` 的 innerHTML 逻辑提取为 `buildPlaceholderHtml(key)`
2. `fillCard` 中的回退字符串改为调用 `buildPlaceholderHtml(k)`
3. `renderPlaceholderCards()` 内部也调用 `buildPlaceholderHtml`

**B — 加缓存**：
1. 在 `_retrieve_similar` 上加 `@functools.lru_cache(maxsize=500)` 装饰器
2. 注意：`_tfidf` 和 `_train_vecs` 在 v0.9 后变为惰性初始化，确保它们在缓存生效前已初始化

#### 不动的内容

- 外部函数签名
- 全部对比、单模型分类、清空等业务流程
- 缓存大小（500 条足够，高频输入如"天气"、"播放歌曲"基本命中）

#### 验证清单

| # | 操作 | 预期结果 |
|---|---|---|
| 1 | 单模型分类（reg/tfidf/bert/gpt） | 选中模型卡片变亮，其余 3 张保持占位 |
| 2 | 清空后重新分类 | 占位卡片显示正常，无重复/错位 |
| 3 | 连续两次输入相同文本调 LLM | 第二次比第一次快（缓存命中） |
| 4 | 输入不同文本 | 第一次慢，第二次相同文本快 |
| 5 | 全部对比 | 4 张卡片同时渲染 |

---

### v0.12 — 全量 BERT 训练 + 置信度展示（候选，待讨论）

#### 问题
- BERT 只用 500 条/类训练，准确率 83%，低于 TF-IDF 的 99%，不合理
- 所有模型只返回分类名，不展示模型对这个分类的"信心"

#### 这个版本是否执行，取决于 v0.9~v0.11 完成后的讨论决策。

---

## 已记录的其他待修复项

### 全部对比结果渲染时机

**问题**：当前 `compareAllModels` 使用 `Promise.allSettled`，等 4 个请求全部完成后才一次性调用 `fillAllCards` 渲染。
当 GPT 模型耗时 10s 时，用户看到 4 张骨架屏一直不动，体验差。

**期望**：快的结果先展示，逐个刷新。先到的 request 直接在 `.then()` 里独立更新对应卡片。

**优先级**：中（不影响功能，影响体验）

---

## 执行顺序

```
v0.9  LLM 惰性初始化        → 2026-05-07 ✅
v0.10 endpoint 异常处理提取  → 2026-05-07 ✅
v0.11 fillCard 重构 + 缓存   → 2026-05-07 ✅
     ↓
讨论是否进入 v0.12（功能新增）
```

---

## 勾选框

- [x] v0.9 — LLM 惰性初始化
- [x] v0.10 — endpoint 异常处理提取 + traceback 截断
- [x] v0.11 — fillCard 重构 + LLM 检索缓存
- [ ] v0.12 — BERT 全量训练 + 置信度展示（待定）
