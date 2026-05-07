"""
BERT 意图分类模型

加载微调后的完整 BERT 模型权重目录，
对输入文本进行 12 类意图分类。
"""
import os
from typing import Union

import torch
from transformers import AutoTokenizer, BertForSequenceClassification

from config import CATEGORY_NAME

_DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 加载微调后的完整模型目录
_BEST_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "weights", "bert_best")

if os.path.exists(os.path.join(_BEST_DIR, "config.json")):
    # save_pretrained 方式加载
    _tokenizer = AutoTokenizer.from_pretrained(_BEST_DIR)
    _model = BertForSequenceClassification.from_pretrained(_BEST_DIR)
    print(f"[bert] Loaded model from {_BEST_DIR}")
else:
    # 兜底：从 state_dict 加载（处理 LayerNorm 命名差异）
    from config import BERT_MODEL_PKL_PATH
    _tokenizer = AutoTokenizer.from_pretrained("bert-base-chinese")
    _model = BertForSequenceClassification.from_pretrained(
        "bert-base-chinese",
        num_labels=len(CATEGORY_NAME),
    )
    state = torch.load(BERT_MODEL_PKL_PATH, map_location=_DEVICE, weights_only=True)
    # 处理 gamma->weight, beta->bias
    new_state = {}
    for k, v in state.items():
        k = k.replace(".gamma", ".weight").replace(".beta", ".bias")
        new_state[k] = v
    _model.load_state_dict(new_state, strict=False)
    print(f"[bert] Loaded from state_dict ({_BEST_DIR} not found)")

_model.to(_DEVICE)
_model.eval()


def model_for_bert(request_text: Union[str, list[str]]) -> Union[str, list[str]]:
    """
    BERT 分类

    :param request_text: 单条字符串或字符串列表
    :return: 单条返回字符串列表，批量返回嵌套列表
    """
    if isinstance(request_text, str):
        texts = [request_text]
    elif isinstance(request_text, list):
        texts = request_text
    else:
        raise TypeError(f"不支持的输入类型: {type(request_text)}")

    encodings = _tokenizer(texts, truncation=True, padding=True, max_length=64, return_tensors="pt")
    input_ids = encodings["input_ids"].to(_DEVICE)
    attention_mask = encodings["attention_mask"].to(_DEVICE)

    with torch.no_grad():
        outputs = _model(input_ids=input_ids, attention_mask=attention_mask)
        logits = outputs.logits
        preds = torch.argmax(logits, dim=-1).cpu().numpy()

    results = [[CATEGORY_NAME[p]] for p in preds]

    if isinstance(request_text, str):
        return results[0]
    return results
