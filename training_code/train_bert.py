"""
BERT 模型训练脚本

流程：
1. 加载数据集，用 CATEGORY_NAME 固定标签顺序（12 类）
2. 用 bert-base-chinese 的 tokenizer 编码文本
3. 训练 BertForSequenceClassification (12 类)
4. 保存最佳模型（save_pretrained 完整目录 + state_dict 双备份）
"""
import os
import sys
import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from transformers import (
    BertTokenizer,
    BertForSequenceClassification,
    Trainer,
    TrainingArguments,
)
from datasets import Dataset

# 确保能 import 项目根目录
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import DATASET_PATH, CATEGORY_NAME


MODEL_NAME = "bert-base-chinese"
MODEL_CACHE = os.path.join(os.path.dirname(__file__), "..", "assets", "models", MODEL_NAME)
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "weights", "bert", "checkpoints")
WEIGHT_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "weights", "bert.pt")
BERT_BEST_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "weights", "bert_best")

TRAIN_SIZE = 500


def main():
    print("=" * 50)
    print(f"BERT 训练 (数据量: {TRAIN_SIZE}, 类别: {len(CATEGORY_NAME)})")
    print("=" * 50)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"设备: {device}")

    # 1. 加载数据
    print(f"\n[1/5] 加载数据集")
    df = pd.read_csv(DATASET_PATH, sep="\t", header=None)
    texts = list(df[0].values[:TRAIN_SIZE])
    labels = df[1].values[:TRAIN_SIZE]

    # 用 CATEGORY_NAME 固定类别顺序，而非从数据推断
    lbl_encoder = LabelEncoder()
    lbl_encoder.fit(CATEGORY_NAME)
    labels_encoded = lbl_encoder.transform(labels)
    print(f"  样本: {len(texts)}, 类别数: {len(lbl_encoder.classes_)}")

    # 2. 分割
    print(f"\n[2/5] 训练/测试分割")
    x_train, x_test, y_train, y_test = train_test_split(
        texts, labels_encoded, test_size=0.2, stratify=labels_encoded
    )
    print(f"  训练: {len(x_train)}, 测试: {len(x_test)}")

    # 3. 分词
    print(f"\n[3/5] 加载 tokenizer")
    tokenizer = BertTokenizer.from_pretrained(MODEL_NAME, cache_dir=MODEL_CACHE)

    train_enc = tokenizer(x_train, truncation=True, padding=True, max_length=64)
    test_enc = tokenizer(x_test, truncation=True, padding=True, max_length=64)

    train_dataset = Dataset.from_dict({
        "input_ids": train_enc["input_ids"],
        "attention_mask": train_enc["attention_mask"],
        "labels": y_train,
    })
    test_dataset = Dataset.from_dict({
        "input_ids": test_enc["input_ids"],
        "attention_mask": test_enc["attention_mask"],
        "labels": y_test,
    })

    # 4. 加载模型
    print(f"\n[4/5] 加载 BERT 模型 (num_labels={len(CATEGORY_NAME)})")
    model = BertForSequenceClassification.from_pretrained(
        MODEL_NAME,
        cache_dir=MODEL_CACHE,
        num_labels=len(CATEGORY_NAME),
    )
    model.to(device)

    # 5. 训练
    print(f"\n[5/5] 开始训练")
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=4,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        warmup_steps=500,
        weight_decay=0.01,
        logging_steps=50,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        save_total_limit=2,
        disable_tqdm=False,
    )

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        predictions = np.argmax(logits, axis=-1)
        return {"accuracy": (predictions == labels).mean()}

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        compute_metrics=compute_metrics,
    )

    trainer.train()
    eval_result = trainer.evaluate()
    acc = eval_result.get("eval_accuracy", 0)

    # 6. 保存最佳模型（完整目录 + state_dict 双备份）
    best_path = trainer.state.best_model_checkpoint
    if best_path:
        best_model = BertForSequenceClassification.from_pretrained(best_path)
    else:
        best_model = model

    # 保存完整模型目录（save_pretrained 保持命名一致）
    best_model.save_pretrained(BERT_BEST_DIR)
    tokenizer.save_pretrained(BERT_BEST_DIR)
    print(f"\nModel saved: {BERT_BEST_DIR}/ (完整目录)")

    # 同时保存 state_dict 作为兼容备份
    torch.save(best_model.state_dict(), WEIGHT_PATH)
    print(f"Model saved: {WEIGHT_PATH} (state_dict) [test acc: {acc:.4f}]")


if __name__ == "__main__":
    main()
