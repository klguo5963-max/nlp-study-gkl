"""
从数据集提取每个类别的高频关键词，辅助生成正则规则
"""
import csv
import jieba
from collections import Counter

# 加载停用词
stopwords = set()
try:
    with open("assets/dataset/baidu_stopwords.txt", "r", encoding="utf-8") as f:
        for line in f:
            stopwords.add(line.strip())
except FileNotFoundError:
    pass

# 读取数据集
category_texts = {}
with open("assets/dataset/dataset.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f, delimiter="\t")
    for row in reader:
        if len(row) >= 2:
            text, label = row[0].strip(), row[1].strip()
            if label not in category_texts:
                category_texts[label] = []
            category_texts[label].append(text)

# 对每个类别统计词频（排除停用词）
for label in sorted(category_texts.keys()):
    texts = category_texts[label]
    words = []
    for t in texts:
        words.extend([w for w in jieba.lcut(t) if len(w) >= 2 and w not in stopwords])
    top = Counter(words).most_common(15)
    print(f"\n{label} ({len(texts)}条)")
    print("  " + ", ".join(f"{w}({c})" for w, c in top))
