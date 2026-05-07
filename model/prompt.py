"""
LLM 意图分类模型

使用 OpenAI 兼容 API（通义千问等）进行动态 Few-shot 分类：

1. 输入文本 → TF-IDF 向量化，与训练集计算相似度
2. 取 Top-10 最相似样本作为 prompt 参考例子
3. 拼接 prompt 提交到 LLM
4. 提取并返回分类标签

API Key 从 .env 文件加载，不硬编码在代码中。

设计说明：
- 所有初始化（加载模型、读取数据、初始化客户端）使用惰性加载，
  只有在第一次调用 model_for_llm 时才执行。
- 如果 LLM 相关资源不可用（缺 API Key、模型文件等），
  调用返回异常，但不影响服务启动和其他 endpoint。
"""
import os
import logging
import functools
from typing import Union

_CATEGORIES_STR = None

# 惰性资源容器
_lazy = {
    "client": None,
    "tfidf": None,
    "train_texts": None,
    "train_labels": None,
    "train_vecs": None,
    "stopwords": None,
    "categories_str": None,
    "initialized": False,
    "error": None,
}

_logger = logging.getLogger("intent-classify")


def _lazy_init():
    """惰性初始化所有 LLM 相关资源"""
    if _lazy["initialized"]:
        return
    if _lazy["error"]:
        raise RuntimeError(_lazy["error"])

    try:
        from dotenv import load_dotenv
        from joblib import load
        from openai import OpenAI
        import pandas as pd
        import jieba
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity
        from config import (
            TFIDF_MODEL_PKL_PATH,
            DATASET_PATH,
            CATEGORY_NAME,
            LLM_OPENAI_SERVER_URL,
            LLM_API_KEY_ENV,
            LLM_MODEL_NAME,
        )

        # 加载 .env
        _load_dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
        load_dotenv(_load_dotenv_path)

        # 获取 API Key
        _api_key = os.environ.get(LLM_API_KEY_ENV, "")
        if not _api_key:
            raise ValueError(f"环境变量 {LLM_API_KEY_ENV} 未设置，请检查 .env 文件")

        # 初始化 OpenAI 客户端
        _lazy["client"] = OpenAI(api_key=_api_key, base_url=LLM_OPENAI_SERVER_URL)

        # 保存模型名称供后续使用
        _lazy["model_name"] = LLM_MODEL_NAME

        # 加载 TF-IDF 模型
        _lazy["tfidf"], _svm = load(TFIDF_MODEL_PKL_PATH)

        # 读取训练数据
        _df = pd.read_csv(DATASET_PATH, sep="\t", header=None)
        _lazy["train_texts"] = _df[0].tolist()
        _lazy["train_labels"] = _df[1].tolist()

        # 加载停用词
        _stopwords_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "dataset", "baidu_stopwords.txt"
        )
        with open(_stopwords_path, "r", encoding="utf-8") as f:
            _lazy["stopwords"] = {line.strip() for line in f if line.strip()}

        # 预处理训练文本并缓存成向量
        def _tokenize(text: str) -> str:
            words = [w for w in jieba.lcut(text) if w not in _lazy["stopwords"] and w.strip()]
            return " ".join(words)

        _lazy["tokenize"] = _tokenize
        _lazy["train_vecs"] = _lazy["tfidf"].transform(
            [_tokenize(t) for t in _lazy["train_texts"]]
        )

        # 类别列表字符串
        _lazy["categories_str"] = " / ".join(CATEGORY_NAME)

        _lazy["initialized"] = True
        _logger.info("[llm] lazy init complete")

    except Exception as e:
        _lazy["initialized"] = False
        _lazy["error"] = str(e)
        _logger.error(f"[llm] lazy init failed: {e}")
        raise


def model_for_llm(request_text: Union[str, list[str]]) -> Union[str, list[str]]:
    """
    LLM 动态 Few-shot 分类

    :param request_text: 单条字符串或字符串列表
    :return: 单条返回字符串列表，批量返回嵌套列表
    :raises: RuntimeError 如果 LLM 资源初始化失败
    """
    try:
        _lazy_init()
    except Exception as e:
        # 将初始化异常转换为业务异常，由调用方 catch
        raise RuntimeError(f"LLM 服务不可用: {_lazy['error'] or str(e)}")

    if isinstance(request_text, str):
        texts = [request_text]
    elif isinstance(request_text, list):
        texts = request_text
    else:
        raise TypeError(f"不支持的输入类型: {type(request_text)}")

    results = []
    for text in texts:
        result = _classify_single(text)
        results.append([result])

    if isinstance(request_text, str):
        return results[0]
    return results


def _retrieve_similar(text: str, top_k: int = 10) -> tuple:
    """TF-IDF 余弦相似度检索 Top-K 相似样本"""
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity

    tokenized = _lazy["tokenize"](text)
    vec = _lazy["tfidf"].transform([tokenized])
    sims = cosine_similarity(vec, _lazy["train_vecs"])[0]
    top_indices = np.argsort(sims)[-top_k:][::-1]
    return tuple((_lazy["train_texts"][i], _lazy["train_labels"][i]) for i in top_indices)


@functools.lru_cache(maxsize=500)
def _retrieve_cached(text: str) -> tuple:
    """带缓存的相似样本检索（LRU 500 条）"""
    return _retrieve_similar(text, 10)


def _classify_single(text: str) -> str:
    """对单条文本调用 LLM 分类"""
    examples = _retrieve_cached(text)

    example_lines = "\n".join(
        [f"{ex_text} -> {ex_label}" for ex_text, ex_label in examples]
    )

    prompt = (
        f"你是一个意图识别的专家，请结合待选类别和参考例子进行意图分类。\n"
        f"待选类别：{_lazy['categories_str']}\n\n"
        f"历史参考例子如下：\n"
        f"{example_lines}\n\n"
        f"待识别的文本为：{text}\n"
        f"只需要输出意图类别（从待选类别中选一个），不要其他输出。"
    )

    completion = _lazy["client"].chat.completions.create(
        model=_lazy["model_name"],
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=64,
    )

    result = completion.choices[0].message.content.strip()
    return result
