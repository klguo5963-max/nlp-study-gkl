"""
TF-IDF + SVM 意图分类模型

从 joblib 文件中加载预训练的 TfidfVectorizer 和 LinearSVC，
对输入文本分词、向量化后预测意图类别。
"""
from typing import Union

import jieba
import pandas as pd
from joblib import load

from config import TFIDF_MODEL_PKL_PATH, STOPWORDS_PATH

# 加载模型
_tfidf, _model = load(TFIDF_MODEL_PKL_PATH)

# 加载停用词
with open(STOPWORDS_PATH, "r", encoding="utf-8") as f:
    _stopwords = {line.strip() for line in f if line.strip()}


def _tokenize(text: str) -> str:
    """分词 + 去停用词，返回空格分隔"""
    words = [w for w in jieba.lcut(text) if w not in _stopwords and w.strip()]
    return " ".join(words)


def model_for_tfidf(request_text: Union[str, list[str]]) -> Union[str, list[str]]:
    """
    TF-IDF 分类

    :param request_text: 单个字符串或字符串列表
    :return: 单条返回字符串列表，批量返回嵌套列表
    """
    if isinstance(request_text, str):
        tokenized = _tokenize(request_text)
        vec = _tfidf.transform([tokenized])
        return list(_model.predict(vec))

    if isinstance(request_text, list):
        results = []
        for text in request_text:
            tokenized = _tokenize(text)
            vec = _tfidf.transform([tokenized])
            results.append(list(_model.predict(vec)))
        return results

    raise TypeError(f"不支持的输入类型: {type(request_text)}")
