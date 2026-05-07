# API 接口设计

---

## 1. 通用规范

### 1.1 基础地址
```
http://localhost:8000
```

### 1.2 请求/响应格式
- Content-Type: `application/json`
- 编码：UTF-8

### 1.3 请求 Schema
```json
{
  "request_id": "string (可选，方便请求追踪)",
  "request_text": "string | string[] (必填，单条或批量)"
}
```

Python 定义（`data_schema.py`）：
```python
class TextClassifyRequest(BaseModel):
    request_id: Optional[str] = None
    request_text: Union[str, list[str]]
```

### 1.4 响应 Schema
```json
{
  "request_id": "string",
  "request_text": "string | string[]",
  "classify_result": "string | string[]",
  "classify_time": 0.123,
  "error_msg": "ok"
}
```

Python 定义（`data_schema.py`）：
```python
class TextClassifyResponse(BaseModel):
    request_id: Optional[str] = None
    request_text: Union[str, list[str]] = ""
    classify_result: Union[str, list[str]] = ""
    classify_time: float = 0.0
    error_msg: str = ""
```

---

## 2. 接口列表

### 2.1 健康检查

```
GET /
```

返回服务信息和可用接口列表。

**响应示例**：
```json
{
  "service": "意图分类服务",
  "version": "0.1.0",
  "status": "running",
  "endpoints": {
    "regex": "/v1/text-cls/regex",
    "tfidf": "/v1/text-cls/tfidf",
    "bert": "/v1/text-cls/bert",
    "gpt": "/v1/text-cls/gpt"
  },
  "docs": "/docs"
}
```

### 2.2 正则匹配分类

```
POST /v1/text-cls/regex
```

- 规则定义在 `config.py` 的 `REGEX_RULE` 中
- 每个类别预编译一个 `re.compile("key1|key2|...")` 的 pattern
- 所有关键词用 `re.escape` 转义
- 匹配到多个规则时返回全部匹配类别（列表）
- 未匹配返回 `["Other"]`
- 批量输入时每一条独立匹配

**实现行为**：
- 输入 str → 返回 str（列表中第一项；若多项取逗号分隔？——原项目返回 list）
- 输入 list → 返回 list[list]

**验证用例**：
| 输入 | 期望输出 | 匹配关键词 |
|---|---|---|
| "帮我播放周杰伦的歌曲" | `["FilmTele-Play", "Music-Play"]` | 播放（两个类别均有） |
| "打开客厅的空调" | `["HomeAppliance-Control"]` | 空调/打开/灯 |
| "今天北京天气怎么样" | `["Weather-Query"]` | 天气 |
| "明天上午提醒我开会" | `["Alarm-Update"]` | 提醒 |
| "农历五月初五是几号" | `["Calendar-Query"]` | 农历/几号 |
| "播放一首周杰伦的歌" | `["Music-Play", "FilmTele-Play"]` | 播放/歌 |
| "给我讲一个故事" | `["Audio-Play"]` | 故事 |

### 2.3 TF-IDF + SVM 分类

```
POST /v1/text-cls/tfidf
```

- 需要 `assets/weights/tfidf_ml.pkl` 存在
- 流程：输入文本 → jieba 分词 → 去停用词 → TF-IDF 向量化 → LinearSVC 预测 → 返回标签
- 模型不存在时抛异常
- 使用 baidu_stopwords.txt 过滤停用词

### 2.4 BERT 分类

```
POST /v1/text-cls/bert
```

- 需要 `assets/weights/bert.pt`（训练后的权重）+ `assets/models/bert-base-chinese/`（预训练模型）
- 自动选择 GPU / CPU
- `max_length=30`（截断），batch_size=16

### 2.5 LLM 分类

```
POST /v1/text-cls/gpt
```

- 需要配置 `config.py` 中的 LLM 参数（URL / API Key / Model Name）
- 每次推理时动态构建 Few-shot 提示词
- 使用 TF-IDF 从训练集中检索 Top-10 最相似样本作为参考

**Prompt 模板**：
```
你是一个意图识别的专家，请结合待选类别和参考例子进行意图分类。
待选类别：{12个类别用 / 分隔}

历史参考例子如下：
{文本1} -> {标签1}
{文本2} -> {标签2}
...

待识别的文本为：{输入文本}
只需要输出意图类别（从待选类别中选一个），不要其他输出。
```

---

## 3. 错误处理

| 场景 | HTTP 状态码 | error_msg |
|---|---|---|
| 成功 | 200 | "ok" |
| 模型文件缺失 | 200 | 异常堆栈（文件找不到） |
| LLM 连接失败 | 200 | 异常堆栈（连接超时/拒绝） |
| 请求参数错误 | 422 | Pydantic 自动返回的验证错误 |
| 未捕获异常 | 500 | 服务器内部错误 |

注意：所有分类接口的模型层异常统一在 endpoint 内 catch，仍返回 HTTP 200，通过 `error_msg` 传递错误详情。前端据此判断请求是否成功。

---

## 4. 前端调用示例

```javascript
// 前端 JS 调用示例
const response = await fetch('http://localhost:8000/v1/text-cls/regex', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    request_id: 'req_001',
    request_text: '帮我播放周杰伦的歌曲'
  })
});
const data = await response.json();
console.log(data.classify_result); // ["FilmTele-Play"]
console.log(data.classify_time);   // 0.003
```
