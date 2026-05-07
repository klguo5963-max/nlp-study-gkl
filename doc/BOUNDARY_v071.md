# 边界修复规格 · v0.7.1

## 概述

在 v0.7 的三个轮次（多模型 badge → 全部对比 → 性能面板）全部完成后，
补上真实用户使用中会遇到的关键边界场景。

**原则**：
1. 不改后端一行代码
2. 不改现有 HTML 结构（只增不删 id/class）
3. 每次改动只修一个边界，修完即验
4. 回归测试：每个改动完成后，v0.7 的三个已有功能必须正常工作

---

## 边界发现

通过模拟真实用户操作，发现以下边界场景：

### 场景 A：两次快速点击"全部对比"（防抖）

**问题**：`compareAllModels` 和 `processText` 都没有防抖。
第一次请求发出后用户再次点击，会发出第二次请求。两个请求并行执行，
结果区域会被第二次执行的结果覆盖，导致第一次的骨架屏也被第二次覆盖。

**安全等级**：高。会导致 UI 状态混乱。

**修复位置**：只改 `frontend/script.js`

**改动内容**：
- 在 `setClassifyLoading(true)` 中，已经禁用了 classifyBtn 和 compareBtn
- 但 `clearResults` 没有禁用按钮，如果用户在加载中点了清空，会触发冲突
- ✅ 检查 `clearResults` — 它在加载中不应该被禁用（清空操作应该总是可用的）
- 实际问题是：**`setClassifyLoading` 已经做了按钮禁用**，所以防抖已经天然成立了
- 点分类/对比后按钮灰色不可点，用户无法快速点击两次

当前状态：✅ **已防御。** `setClassifyLoading(true)` → 两个按钮 disabled，用户无法双击。

---

### 场景 B：全部对比时某个模型超时（Promise.all 问题）

**问题**：当前用 `Promise.all(requests)`，如果 GPT 模型（最长可达 10s）超时卡住，
整个对比请求会卡在 pending 状态，界面不更新。

**安全等级**：高。用户会看到骨架屏一直不动。

**当前代码**：
```javascript
const results = await Promise.all(requests);
```

**修复目标**：改为 `Promise.allSettled` + 每个请求单独超时（15s），
已完成的卡片先展示，超时的显示"响应超时"。

**改动范围**：只改 `frontend/script.js` 中的 `compareAllModels` 函数。

**具体改动**：
1. 每个 fetch 请求加 `AbortController` 超时（15000ms）
2. 改为 `await Promise.allSettled(requests)`
3. 成功 / rejected / timeout 的卡片各自独立渲染

**验证清单**：

| # | 操作 | 预期 |
|---|---|---|
| 1 | 全部对比，4 个模型都正常 | 4 个卡片全部显示结果 |
| 2 | 在 `fetch` 中超时设为 1ms（测试用） | 4 个卡片显示"请求失败"或超时 |
| 3 | 点单模型分类 | 不受影响 |

**不影响现有代码的原因**：只改 `compareAllModels` 内部实现，
`processText`（单模型分类）不受影响，HTML/CSS 都不动。

---

### 场景 C：输入超长文本无限制

**问题**：当前 textarea 无字符数限制。如果输入 >500 字的文本，
BERT 会截断（512 token 限制），LLM 可能 token 超限产生额外费用。

**安全等级**：中。不涉及崩溃但涉及成本和体验。

**改动范围**：
- `frontend/index.html`：在 textarea 下方或字符数旁边增加一个警告区域
- `frontend/script.js`：`updateCharCount` 中增加阈值判断
- `frontend/style.css`：增加警告文字样式

**具体改动**：
1. 在 `frontend/index.html` 中 `char-count` 旁边增加 `<span id="textWarning"></span>`
2. `updateCharCount` 中：
   - 字符数 ≤ 200：不显示警告
   - 200 < 字符数 ≤ 500：黄色警告 "文本较长，部分模型可能截断"
   - 字符数 > 500：红色警告 "文本过长，建议控制在 500 字符以内"
3. 在 `processText` 和 `compareAllModels` 中增加：
   - 字符数 > 500 时 submit 按钮不可用
4. CSS 增加 `.text-warning`、`.text-danger` 样式

**验证清单**：

| # | 操作 | 预期 |
|---|---|---|
| 1 | 输入 150 个字符 | 无警告，按钮可用 |
| 2 | 输入 300 个字符 | 黄色警告出现，按钮可用 |
| 3 | 输入 600 个字符 | 红色警告出现，按钮灰色不可点 |
| 4 | 清空后 | 警告消失 |

---

### 场景 D：输入为空未做 toast 提示

**问题**：当前输入为空时调用 `showError`，结果是替换结果显示区域的卡片。
用户需要滚动到下面才能看到错误，不够直观。

**安全等级**：低。功能不影响，体验优化。

**修复目标**：在 textarea 下方显示浮动错误提示（2s 自动消失），
而不是替换结果区。

**改动范围**：只改 `frontend/script.js`

**当前代码**：
```javascript
if (!text) {
    showError('请输入需要分类的文本');
    return;
}
```

**修复方式**：不调用 `showError`，改为在文本输入框下方加一句话提示。
但为了最小改动量，这个可以**推迟到 UI 重构时一起做**。

**当前状态**：✅ **暂缓**，UI 重构时统一处理。

---

### 场景 E：清除结果时没有重置全部对比的加载状态

**问题**：如果在全部对比进行中点了"清空结果"，
`clearResults` 会清空结果面板但不会调用 `setClassifyLoading(false)`，
导致按钮仍然是禁用状态。

**安全等级**：中。用户按钮会 stuck。

**当前代码**：
```javascript
function clearResults() {
    resultsContent.innerHTML = `...`;
    document.getElementById('benchmarkSection').style.display = 'none';
    inputText.value = '';
    updateCharCount();
}
```

**修复目标**：`clearResults` 中检测是否处于加载态，如果是则关闭加载态。

**改动范围**：只改 `frontend/script.js` 中的 `clearResults`

**具体改动**：
```javascript
function clearResults() {
    if (loading.classList.contains('active')) {
        setClassifyLoading(false);
    }
    // ... 原有逻辑
}
```

**验证清单**：

| # | 操作 | 预期 |
|---|---|---|
| 1 | 正常对比完成 → 点清空 | 按钮恢复正常，面板消失 |
| 2 | 对比过程中 → 点清空 | 请求被忽略（或者按钮在加载中不可点） |

**注意**：`compareBtn` 在加载中是 disabled 的，所以用户在过程中点不到清空旁边的按钮。
但 `clearBtn` 始终可用。可以加一条判断：如果正在加载且点了清空，先 abort 请求再清空。

✅ 当前状态：**简单方案已够用**，只加 `setClassifyLoading(false)` 兜底。

---

## 最终交付要求

### 需修的边界（按重要性排序）

| 优先级 | 场景 | 改动量 | 文件 | 是否独立 |
|---|---|---|---|---|
| P0 | B — 全部对比超时 | 15 行 | script.js 内 `compareAllModels` | ✅ 完全独立 |
| P1 | C — 输入长度警告 | 20 行 + HTML 2 行 + CSS 15 行 | index.html + script.js + style.css | ⚠️ 跨 3 文件，但每处改动量极小 |
| P2 | E — 清空时 stuck 按钮 | 2 行 | script.js 内 `clearResults` | ✅ 完全独立 |

### 不改的（暂缓至 UI 重构）

| 场景 | 原因 |
|---|---|
| A — 双击防抖 | 已天然防御（按钮 disabled） |
| D — 空输入 toast | 体验优化，UI 重构时统一做 |

---

## 交付顺序

1. **P0 — 超时处理**：改 `compareAllModels`，加 `AbortController` + `Promise.allSettled`
2. 验证 P0（全正常 + 模拟超时两种场景）
3. **P1 — 长度警告**：跨 3 文件，不加新 id，只加新 `<span>`
4. 验证 P1（200/500 阈值 + 回归已有功能）
5. **P2 — 清空 stuck**：`clearResults` 加 2 行
6. 验证 P2（正常清空 + 加载中清空）
7. 最终回归：4 个模型 + 全部对比 + 性能面板 + 清空 + Ctrl+Enter 全部走一遍

---

## 勾选框

- [x] P0 — 全部对比 AbortController + Promise.allSettled
- [x] P1 — 输入长度阈值警告
- [x] P2 — 清空时 stuck 按钮修复
