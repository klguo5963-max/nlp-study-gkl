"""
正则匹配意图分类模型

基于 config.py 中的 REGEX_RULE 规则字典做关键词匹配。
匹配到多个规则时返回全部匹配类别，未匹配返回 ["Other"]。
支持单条字符串和批量字符串列表。

注意：REGEX_RULE 中的关键词可以是普通文本或正则表达式。
- 纯文本关键词会自动用 re.escape 转义
- 以 "REGEX:" 开头的关键词按原始正则处理（例如 "REGEX:看.*剧"）
"""
import re
from typing import Union

from config import REGEX_RULE

_PREFIX = "REGEX:"

# 预编译正则 pattern
_COMPILED: dict[str, re.Pattern] = {}
for category, keywords in REGEX_RULE.items():
    if not keywords:
        _COMPILED[category] = None
        continue
    patterns = []
    for kw in keywords:
        if kw.startswith(_PREFIX):
            patterns.append(kw[len(_PREFIX):])
        else:
            patterns.append(re.escape(kw))
    _COMPILED[category] = re.compile("|".join(patterns))


def model_for_regex(request_text: Union[str, list[str]]) -> Union[str, list[str]]:
    """
    正则匹配分类

    返回所有匹配的类别列表。如果多个类别都匹配，全部返回。
    无匹配时返回 ["Other"]。
    """
    def _match_single(text: str) -> list[str]:
        matched = []
        for category, pattern in _COMPILED.items():
            if pattern is None:
                continue
            if pattern.search(text):
                matched.append(category)
        return matched if matched else ["Other"]

    if isinstance(request_text, str):
        return _match_single(request_text)

    if isinstance(request_text, list):
        return [_match_single(text) for text in request_text]

    raise TypeError(f"不支持的输入类型: {type(request_text)}")
