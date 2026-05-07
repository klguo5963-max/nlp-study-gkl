# 检查数据集是否支持多标签
with open('assets/dataset/dataset.csv', 'r', encoding='utf-8') as f:
    lines = f.readlines()
print(f'总条数: {len(lines)}')

# 第一行看看格式
print(f'第一行: {repr(lines[0])}')

# 检查标签是否包含逗号
multi = []
for l in lines:
    if '\t' not in l:
        continue
    parts = l.strip().split('\t')
    if len(parts) < 2:
        continue
    label = parts[1].strip()
    if ',' in label or '、' in label or ' ' in label:
        multi.append(l.strip())
print(f'|n多标签行: {len(multi)}')
if multi:
    for m in multi[:5]:
        print(f'  {m}')

# 检查同一文本对应不同标签
texts = {}
for l in lines:
    if '\t' not in l:
        continue
    parts = l.strip().split('\t')
    if len(parts) < 2:
        continue
    t, lbl = parts[0], parts[1].strip()
    texts.setdefault(t, set()).add(lbl)
dup = {t: lbls for t, lbls in texts.items() if len(lbls) > 1}
print(f'\n相同文本不同标签: {len(dup)} 组')
for t, lbls in list(dup.items())[:5]:
    print(f'  "{t}" -> {lbls}')
