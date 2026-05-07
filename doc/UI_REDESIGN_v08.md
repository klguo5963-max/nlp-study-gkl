# 前端 UI 重构规格 · v0.8

## 1. 项目规格

### 1.1 产品定位
NLP 意图分类模型的**对比测试工作台**，用于直观对比 4 种不同算法在同一输入下的分类结果差异。

### 1.2 当前问题
- 页面分 5 个纵向区块（输入 → 模型选择 → 按钮 → 结果 → 性能面板），需要不停上下滚
- "全部对比"的 4 个结果和"性能面板"之间也有间距，信息碎片化
- 亮色背景 + 蓝紫渐变的配色缺乏个性，看起来像模板
- 文本区域和结果区域之间无视觉关联，用户需要反复拖视线上看下看

### 1.3 核心改造目标
**在一个屏幕高度内展示完整工作流**：输入 → 一键跑 4 个模型 → 结果并排 → 性能数据嵌入结果卡片。
不滚动（或少滚动）看到一切。

### 1.4 审美方向：A — 深色科技风

| 维度 | 选择 |
|---|---|
| 背景 | 深灰/碳黑底 `#0a0e17` |
| 主色 | 冷青蓝 `#00d4ff` 作为科技感高光 |
| 文字 | 冷白 `#e8edf5` 为主 + 浅灰 `#8892a4` 辅助 |
| 卡片 | 毛玻璃效果（`backdrop-filter: blur`）+ 微边框 `rgba(0,212,255,0.15)` |
| 字体 | 正文 `DM Mono`（代码感）、标题 `Space Grotesk`（现代科技） |
| 运动 | 卡片淡入 + 参数数字微跳动 + 加载时脉冲光晕 |
| 区分点 | 结果卡片左上角嵌入活的性能微距（时间/模型名嵌在卡片头部的彩色光条上） |

### 1.5 第一版明确做什么
- 将 5 段式布局压缩为**左右两栏**：左侧输入+控制区、右侧结果区
- 结果卡片在右侧以**2×2 网格**常驻显示（未输入时显示占位 + 提示）
- 性能指标**嵌入每张卡片顶部**（模型名字+响应时间+精度估算），不再单独一个面板
- 深色科技风全新视觉设计
- 保留全部现有交互（单模型分类、全部对比、清空、Ctrl+Enter、边界保护）

### 1.6 第一版明确不做什么
- 不改后端
- 不改 script.js 的业务逻辑（只更新 DOM 操作和样式引用）
- 不引入第三方 JS 框架/库
- 不做响应式多断点适配（右栏在大屏时适配即可）

---

## 2. 页面布局（左右两栏）

```
┌─────────────────────────────────────────────────────┐
│                     Header                           │
│   🚀 意图分类对比工作台 · 多模型联合测试             │
│   [●] 后端运行中                                    │
├───────────────┬─────────────────────────────────────┤
│  左栏 (35%)   │   右栏 (65%)                        │
│               │                                     │
│  ┌─────────┐  │  ┌──────────────┐ ┌──────────────┐ │
│  │ textarea │  │  │ 正则结果卡片  │ │ TF-IDF结果卡  │ │
│  │          │  │  │ 0ms · 低精度  │ │ 3ms · 中精度  │ │
│  └─────────┘  │  └──────────────┘ └──────────────┘ │
│               │  ┌──────────────┐ ┌──────────────┐ │
│  模型按钮     │  │ BERT结果卡片  │ │ LLM结果卡片   │ │
│  [Regex]      │  │ 42ms · 高精度 │ │ 5s · 非常高   │ │
│  [TF-IDF]     │  └──────────────┘ └──────────────┘ │
│  [BERT]       │                                     │
│  [GPT]        │  占位文本（无输入时灰色提示）        │
│               │                                     │
│  [全部对比]    │                                     │
│  [清空]       │                                     │
├───────────────┴─────────────────────────────────────┤
│                    Footer                            │
│  意图分类服务 v0.8                                   │
└─────────────────────────────────────────────────────┘
```

### 2.1 用户动线
1. 打开页面 → 右栏看到 4 个灰色占位卡片，提示"输入文本后点击按钮"
2. 输入区输入文本（左上角）
3. 选模型（点击卡片切换，当前选中高亮）
4. 点"开始分类" → 右栏对应模型卡片变亮，显示结果 + 彩色 badge
5. 或者点"全部对比" → 右栏 4 个卡片同时变亮
6. 每个卡片内部显示：模型名、响应时间、精度标签、分类结果（带彩色 badge）
7. 性能指标嵌入卡片顶部（时间绿色/红色高亮最快的/最慢的）

---

## 3. 技术约束

- **纯静态 HTML/CSS/JS**，不引入构建工具
- **Font Awesome 6** 保留（图标库）
- **Google Fonts 换掉 Inter** → 用 `Space Grotesk`（标题）+ `DM Mono`（代码/数据）
- **不能改 script.js 中这些全局变量和函数签名**：
  - `API_BASE`, `API_ENDPOINTS`, `MODEL_BENCHMARKS`, `CATEGORY_COLORS`
  - `processText`, `compareAllModels`, `clearResults`, `checkAPIStatus`, `setClassifyLoading`
  - `renderBadges`, `displayBenchmarks`, `showError`, `escapeHtml`, `updateCharCount`
  - `getSelectedModel`
- **不能改 HTML 中这些 id**（JS 依赖它们）：
  - `inputText`, `charCount`, `textWarning`, `classifyBtn`, `compareBtn`, `clearBtn`
  - `apiStatus`, `statusIndicator`, `loading`, `resultsContent`, `benchmarkSection`, `benchmarkBody`

### 3.1 重构时需保留的 HTML id 完整清单

```
inputText, charCount, textWarning,
classifyBtn, compareBtn, clearBtn,
apiStatus, statusIndicator, loading,
resultsContent, benchmarkSection, benchmarkBody,
textWarning, charCount
```

---

## 4. 交互细节

### 4.1 默认状态（无输入）
- 左栏：textarea 聚焦，placeholder "输入文本，例如：帮我播放周杰伦的歌曲"
- 右栏：4 个占位卡片，半透明边框，中间文字 "⌨️ 输入文本后点击按钮开始"
- 后端状态：右上角绿点 + "运行中"

### 4.2 单模型分类
1. 选择一个模型卡片（高亮边框）
2. 点"开始分类"
3. 右栏对应卡片变为激活态：
   - 卡片从半透明变为不透明
   - 顶部显示模型名 + 响应时间（green/red 高亮最快/最慢）
   - 中部显示分类结果（带彩色 badge）
   - 底部显示精度标签

### 4.3 全部对比
1. 点"全部对比"
2. 右栏 4 个卡片同时从占位态切换为 loading 态（脉冲光晕边框）
3. 逐个完成后变为激活态
4. 卡片内性能数据实时更新（最快的 green，最慢的 red）

### 4.4 清空
- 4 张卡片回到占位态
- 输入框清空

---

## 5. 视觉规范

### 5.1 色板

| 用途 | 色值 |
|---|---|
| 背景 | `#0a0e17` |
| 卡片背景 | `rgba(15, 23, 42, 0.85)` |
| 卡片边框活跃 | `rgba(0, 212, 255, 0.5)` |
| 卡片边框占位 | `rgba(255, 255, 255, 0.06)` |
| 主色（高光） | `#00d4ff` |
| 文字主 | `#e8edf5` |
| 文字辅助 | `#8892a4` |
| 成功绿 | `#10b981` |
| 警告黄 | `#f59e0b` |
| 错误红 | `#ef4444` |
| Badge 不变 | 保持现有 12 色 |

### 5.2 字体

| 用途 | 字体 |
|---|---|
| 标题/H1 | `Space Grotesk` (Google Fonts, weight 600) |
| 卡片标题 | `Space Grotesk` (weight 500) |
| 数据/时间 | `DM Mono` (Google Fonts, 代码感) |
| 正文 | `DM Mono` (weight 400) |

### 5.3 卡片细节
- 圆角 `12px`
- 毛玻璃 `backdrop-filter: blur(12px)`
- 激活态左上角有一条 2px 彩色光条（对应模型颜色：Regex=#00d4ff, TF-IDF=#10b981, BERT=#8b5cf6, GPT=#f59e0b）
- 占位态光条为透明
- hover 时轻微上浮 `translateY(-2px)` + 阴影增强

### 5.4 动画
- 页面加载：4 个卡片 staggered 出现（`animation-delay: 0.1s, 0.2s, 0.3s, 0.4s`）
- 结果更新：卡片内容 fadeIn 0.4s
- Loading：脉冲光晕 `@keyframes pulse-glow`
- 响应时间数字变化时：微跳动（glitch 效果，只做样式不改变 DOM）

---

## 6. 具体改哪个文件

| 文件 | 改动量 | 说明 |
|---|---|---|
| `frontend/index.html` | **重写** | 从纵向 5 段改为左右两栏布局，保留所有 id |
| `frontend/style.css` | **重写** | 深色科技风全新样式 |
| `frontend/script.js` | **增量修改** | 只更新 `displayResult`（新的卡片渲染）、`compareAllModels`（新卡片渲染）、`clearResults`（新占位），不动业务逻辑 |

### 6.1 script.js 中需保留的函数和变量（只改渲染部分）

**不改的**（业务逻辑）：
```
API_BASE, API_ENDPOINTS, MODEL_BENCHMARKS, CATEGORY_COLORS,
processText (保留调用链，只改 displayResult 的渲染模板),
compareAllModels (保留调用链，只改内部渲染模板),
setClassifyLoading, getSelectedModel,
checkAPIStatus, renderBadges,
clearResults (只改占位 HTML),
showError, escapeHtml, updateCharCount,
TEXT_WARN_LIMIT, TEXT_ERROR_LIMIT,
initEventListeners
```

**改的**（纯渲染）：
- `displayResult`：改为渲染到对应模型的卡片，而非独立卡片
- `compareAllModels` 内部渲染：改为填充已有 4 个卡片容器
- `clearResults`：改为填充占位卡片 HTML

---

## 7. 执行方案

执行时分为以下步骤（skilled 调用 frontend-design 生成全新 HTML/CSS，然后手工调整 script.js 渲染部分）：

### 步骤 1：提交给 frontend-design skill 的输入
- 本规格文档（关键：布局图、色板、字体、动效、id 不可变更清单）
- 已有 `index.html`、`style.css`、`script.js` 源码

### 步骤 2：接收 skill 输出
- 新 `index.html`（保留所有 id，布局改为左右两栏）
- 新 `style.css`（深色科技风）

### 步骤 3：增量修改 script.js
- 更新 `displayResult`：改为填充对应模型卡片，而非 create 新节点
- 更新 `compareAllModels` 的渲染逻辑
- 更新 `clearResults` 的占位 HTML
- 其它函数不动

### 步骤 4：验证
- 4 个模型单模型分类正常
- 全部对比正常（Promise.allSettled + AbortController）
- 清空正常
- Ctrl+Enter 正常
- 边界保护（超时、长度警告、清空 stuck 兜底）正常
- 无滚动在一个屏幕内看到完整内容

---

## 8. 验证清单

| # | 操作 | 预期 |
|---|---|---|
| 1 | 页面初始加载 | 深色背景，4 个半透明占位卡片在右栏，无输入提示 |
| 2 | 输入文本，选一个模型，点开始分类 | 右栏对应卡片激活，显示彩色 badge |
| 3 | 点"全部对比" | 4 个卡片依次激活，显示结果 + 时间 |
| 4 | 全部对比完成后 | 最快的卡片时间绿色，最慢的红色 |
| 5 | 点"清空" | 4 个卡片回到占位态，输入框清空 |
| 6 | 停止后端服务 | 右上角状态变为红色"离线" |
| 7 | 输入 300 字符 | 黄色警告文字出现在输入区 |
| 8 | 输入 600 字符 | 红色警告，按钮灰色不可点 |
| 9 | 全部对比中某个模型返回超时（用改 1ms 超时模拟） | 该卡片显示错误，其他卡片正常显示 |
| 10 | Ctrl+Enter | 触发单模型分类 |
| 11 | 浏览器窗口 1920×1080 | 不滚动看到完整内容（Header + 左右栏 + Footer） |
| 12 | 浏览器窗口 1366×768 | 轻微滚动但主要工作区可见 |
