"""
TF-IDF + SVM 模型训练脚本

流程：
1. 加载数据集 (assets/dataset/dataset.csv)
2. jieba 分词 + 去停用词
3. TfidfVectorizer (unigram)
4. LinearSVC 训练
5. joblib 保存模型 (assets/weights/tfidf_ml.pkl)
"""
import os
import sys
import pandas as pd
import jieba
from joblib import dump
from sklearn.svm import LinearSVC
from sklearn.feature_extraction.text import TfidfVectorizer

# 确保能导入项目根目录的 config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import DATASET_PATH, STOPWORDS_PATH, TFIDF_MODEL_PKL_PATH


def load_stopwords(path: str) -> set[str]:
    """加载停用词表"""
    with open(path, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def tokenize(text: str, stopwords: set[str]) -> str:
    """分词 + 去停用词，返回空格分隔的词序列"""
    words = [w for w in jieba.lcut(text) if w not in stopwords and w.strip()]
    return " ".join(words)


def main():
    print("=" * 50)
    print("TF-IDF + SVM 模型训练")
    print("=" * 50)

    # 1. 加载数据
    print(f"\n[1/4] 加载数据集: {DATASET_PATH}")
    df = pd.read_csv(DATASET_PATH, sep="\t", header=None)
    texts = df[0].tolist()
    labels = df[1].tolist()
    print(f"  样本数: {len(texts)}, 类别: {len(set(labels))}")

    # 2. 分词
    print(f"\n[2/4] 加载停用词表 + 分词")
    stopwords = load_stopwords(STOPWORDS_PATH)
    print(f"  停用词: {len(stopwords)} 个")

    tokenized = [tokenize(t, stopwords) for t in texts]
    print(f"  分词完成")

    # 3. TF-IDF 向量化
    print(f"\n[3/4] TF-IDF 向量化")
    tfidf = TfidfVectorizer(ngram_range=(1, 1))
    train_tfidf = tfidf.fit_transform(tokenized)
    print(f"  词表大小: {len(tfidf.get_feature_names_out())}")
    print(f"  向量维度: {train_tfidf.shape}")

    # 4. 训练 SVM
    print(f"\n[4/4] 训练 LinearSVC")
    model = LinearSVC(max_iter=2000)
    model.fit(train_tfidf, labels)
    print(f"  训练完成，准确率: {model.score(train_tfidf, labels):.4f}")

    # 5. 保存模型
    dump((tfidf, model), TFIDF_MODEL_PKL_PATH)
    print(f"\n✅ 模型已保存: {TFIDF_MODEL_PKL_PATH}")


if __name__ == "__main__":
    main()
