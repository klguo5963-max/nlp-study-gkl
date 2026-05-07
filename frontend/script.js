/* ============================================
   意图分类对比工作台 · 业务逻辑
   v0.8 — UI 重构：深色科技风左右两栏
   ============================================ */

// 类别颜色映射
const CATEGORY_COLORS = {
    'Alarm-Update': 'badge-alarm',
    'Audio-Play': 'badge-audio',
    'Calendar-Query': 'badge-calendar',
    'FilmTele-Play': 'badge-filmtele',
    'HomeAppliance-Control': 'badge-homeapp',
    'Music-Play': 'badge-music',
    'Other': 'badge-other',
    'Radio-Listen': 'badge-radio',
    'TVProgram-Play': 'badge-tvprogram',
    'Travel-Query': 'badge-travel',
    'Video-Play': 'badge-video',
    'Weather-Query': 'badge-weather',
};

const API_BASE = 'http://localhost:8000';
const API_ENDPOINTS = {
    regex: '/v1/text-cls/regex',
    tfidf: '/v1/text-cls/tfidf',
    bert: '/v1/text-cls/bert',
    gpt: '/v1/text-cls/gpt',
};

const MODEL_BENCHMARKS = {
    regex: { time: 10, accuracy: 60, cost: 1, name: '正则匹配', icon: 'filter', accent: '#00d4ff' },
    tfidf: { time: 50, accuracy: 85, cost: 2, name: 'TF-IDF', icon: 'chart-bar', accent: '#10b981' },
    bert: { time: 200, accuracy: 95, cost: 5, name: 'BERT', icon: 'brain', accent: '#8b5cf6' },
    gpt: { time: 1500, accuracy: 90, cost: 10, name: 'LLM', icon: 'comment-dots', accent: '#f59e0b' },
};

const MODEL_KEYS = ['regex', 'tfidf', 'bert', 'gpt'];

// 精度标签映射
function accuracyLabel(acc) {
    if (acc < 60) return '低精度'; else if (acc < 80) return '中精度';
    else if (acc < 90) return '高精度'; else return '非常高';
}

// DOM 引用
const inputText       = document.getElementById('inputText');
const charCount       = document.getElementById('charCount');
const textWarning     = document.getElementById('textWarning');
const classifyBtn     = document.getElementById('classifyBtn');
const compareBtn      = document.getElementById('compareBtn');
const clearBtn        = document.getElementById('clearBtn');
const apiStatus       = document.getElementById('apiStatus');
const statusIndicator = document.getElementById('statusIndicator');
const loading         = document.getElementById('loading');
const resultsGrid     = document.getElementById('resultsGrid');
const benchmarkSection = document.getElementById('benchmarkSection');
const benchmarkBody   = document.getElementById('benchmarkBody');

// ============ 初始化 ============
document.addEventListener('DOMContentLoaded', function () {
    renderPlaceholderCards();
    initEventListeners();
    checkAPIStatus();
});

// ============ 布局渲染 ============

function buildPlaceholderHtml(key) {
    const b = MODEL_BENCHMARKS[key];
    const emojiMap = { regex: '🔍', tfidf: '📊', bert: '🧠', gpt: '💬' };
    return `<div class="result-card-base result-card-placeholder" data-key="${key}">
        <div class="placeholder-text"><div style="font-size:1.5rem;margin-bottom:6px;">${emojiMap[key] || '❓'}</div>${b.name}</div>
    </div>`;
}

function renderPlaceholderCards() {
    resultsGrid.innerHTML = MODEL_KEYS.map(buildPlaceholderHtml).join('');
}

/** 填充单个卡片（单模型分类结果） */
function fillCard(key, ok, data_or_error) {
    const timeMs = ok ? (data_or_error.classify_time * 1000).toFixed(0) : 0;
    const badgesHtml = ok ? renderBadges(data_or_error.classify_result) : '';

    resultsGrid.innerHTML = MODEL_KEYS.map(k => {
        if (k === key) {
            return ok ? buildCardHtml(key, timeMs, badgesHtml) : buildErrorCard(key, data_or_error);
        }
        return buildPlaceholderHtml(k);
    }).join('');
}

/** 填充全部卡片（全部对比） */
function fillAllCards(results) {
    // 收集时间用于高亮
    const times = {};
    results.forEach(r => { if (r.ok) times[r.key] = r.data.classify_time * 1000; });
    const vals = Object.values(times);
    const minT = Math.min(...vals);
    const maxT = Math.max(...vals);

    resultsGrid.innerHTML = results.map(r => {
        const key = r.key;
        if (r.ok) {
            const badgesHtml = renderBadges(r.data.classify_result);
            const ms = times[key];
            let cls = 'time-normal';
            if (vals.length > 1) { if (ms === minT) cls = 'time-fast'; else if (ms === maxT) cls = 'time-slow'; }
            const timeHtml = `${ms.toFixed(0)} ms`;
            const accTag = accuracyLabel(MODEL_BENCHMARKS[key].accuracy);
            return buildCardHtml(key, timeHtml, badgesHtml, cls, accTag);
        } else {
            return buildErrorCard(key, r.error);
        }
    }).join('');
}

function buildCardHtml(key, timeHtml, badgesHtml, timeClass, accTag) {
    const b = MODEL_BENCHMARKS[key];
    const tc = timeClass || 'time-normal';
    const atag = accTag || accuracyLabel(b.accuracy);
    const style = `border-color:rgba(0,212,255,0.2);`;
    const barStyle = `style="opacity:1;background:${b.accent};box-shadow:0 0 8px ${b.accent};"`;
    return `
        <div class="result-card-base result-card-active" data-key="${key}" style="${style}">
            <div class="card-header"><div class="card-title"><i class="fas fa-${b.icon}" style="color:${b.accent};"></i> ${b.name}</div><div class="card-time"><span class="time-value ${tc}">${timeHtml}</span></div></div>
            <div class="card-body"><div class="card-result-label">分类结果</div><div class="card-result-badges">${badgesHtml}</div></div>
            <div class="card-foot"><span class="acc-tag">${atag}</span></div>
            <div class="card-accent-bar" ${barStyle}></div>
        </div>
    `;
}

function buildErrorCard(key, msg) {
    const b = MODEL_BENCHMARKS[key];
    return `
        <div class="result-card-base result-card-active result-card-error" data-key="${key}">
            <div class="card-header"><div class="card-title" style="color:var(--red);"><i class="fas fa-exclamation-triangle"></i> ${b.name}</div></div>
            <div class="card-body"><div class="card-result-label" style="color:var(--red);">请求失败</div><div class="card-result-badges" style="color:var(--red);font-size:0.8rem;">${escapeHtml(msg)}</div></div>
        </div>
    `;
}

// ============ 事件绑定 ============

const TEXT_WARN_LIMIT = 200;
const TEXT_ERROR_LIMIT = 500;

function initEventListeners() {
    inputText.addEventListener('input', updateCharCount);

    document.querySelectorAll('.example-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            inputText.value = this.getAttribute('data-text');
            updateCharCount();
            inputText.focus();
        });
    });

    // model-chip 点击选中 radio
    document.querySelectorAll('.model-chip').forEach(chip => {
        chip.addEventListener('click', function () {
            const radio = this.querySelector('input[type="radio"]');
            if (radio) radio.checked = true;
        });
    });

    classifyBtn.addEventListener('click', processText);
    compareBtn.addEventListener('click', compareAllModels);
    clearBtn.addEventListener('click', clearResults);

    inputText.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            if (!classifyBtn.disabled) classifyBtn.click();
        }
    });
}

function updateCharCount() {
    const len = inputText.value.length;
    charCount.textContent = len;
    if (len > TEXT_ERROR_LIMIT) {
        textWarning.className = 'text-warning-red';
        textWarning.textContent = '文本过长，建议控制在 500 字符以内';
        classifyBtn.disabled = true; compareBtn.disabled = true;
    } else if (len > TEXT_WARN_LIMIT) {
        textWarning.className = 'text-warning-yellow';
        textWarning.textContent = '文本较长，部分模型可能截断';
        if (statusIndicator.className.includes('active')) { classifyBtn.disabled = false; compareBtn.disabled = false; }
    } else {
        textWarning.className = 'text-warning-hidden';
        textWarning.textContent = '';
        if (statusIndicator.className.includes('active')) { classifyBtn.disabled = false; compareBtn.disabled = false; }
    }
}

function getSelectedModel() {
    const radio = document.querySelector('input[name="model"]:checked');
    return radio ? radio.value : 'regex';
}

async function checkAPIStatus() {
    try {
        const resp = await fetch(API_BASE);
        if (resp.ok) {
            apiStatus.textContent = '运行正常';
            statusIndicator.className = 'status-indicator active';
            classifyBtn.disabled = false; compareBtn.disabled = false;
        } else throw new Error('API 不可用');
    } catch {
        apiStatus.textContent = '连接失败';
        statusIndicator.className = 'status-indicator';
        classifyBtn.disabled = true; compareBtn.disabled = true;
    }
}

function setClassifyLoading(active) {
    if (active) {
        loading.classList.add('active');
        classifyBtn.disabled = true; compareBtn.disabled = true;
        classifyBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 分类中...';
        compareBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 对比中...';
    } else {
        loading.classList.remove('active');
        // 检查文本框长度决定是否恢复
        const len = inputText.value.length;
        if (len <= TEXT_ERROR_LIMIT && statusIndicator.className.includes('active')) {
            classifyBtn.disabled = false; compareBtn.disabled = false;
        }
        classifyBtn.innerHTML = '<i class="fas fa-play"></i> 开始分类';
        compareBtn.innerHTML = '<i class="fas fa-flask"></i> 全部对比';
    }
}

// ============ 核心业务逻辑 ============

async function compareAllModels() {
    const text = inputText.value.trim();
    if (!text) { showError('请输入需要分类的文本'); return; }

    // 骨架屏
    resultsGrid.innerHTML = MODEL_KEYS.map(key => `
        <div class="skeleton-card" data-key="${key}">
            <div class="skeleton-line w60"></div>
            <div class="skeleton-line w40"></div>
            <div class="skeleton-line w80"></div>
            <div class="skeleton-line w60"></div>
        </div>
    `).join('');
    benchmarkSection.style.display = 'none';
    setClassifyLoading(true);

    const TIMEOUT_MS = 15000;
    const requests = MODEL_KEYS.map(async (key) => {
        const benchmark = MODEL_BENCHMARKS[key];
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
        try {
            const resp = await fetch(`${API_BASE}${API_ENDPOINTS[key]}`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                signal: controller.signal,
                body: JSON.stringify({ request_id: `cmp_${Date.now()}`, request_text: text }),
            });
            clearTimeout(timer);
            const data = await resp.json();
            if (!resp.ok) throw new Error(data.error_msg || `HTTP ${resp.status}`);
            return { key, data, benchmark, ok: true };
        } catch (err) {
            clearTimeout(timer);
            let msg = err.message;
            if (err.name === 'AbortError') msg = '响应超时（>15s）';
            return { key, benchmark, ok: false, error: msg };
        }
    });

    const settled = await Promise.allSettled(requests);
    const results = settled.map(s =>
        s.status === 'fulfilled' ? s.value : { key: 'unknown', benchmark: MODEL_BENCHMARKS.regex, ok: false, error: '未知错误' }
    );

    fillAllCards(results);
    displayBenchmarks(results);
    setClassifyLoading(false);
}

async function processText() {
    const text = inputText.value.trim();
    if (!text) { showError('请输入需要分类的文本'); return; }

    const model = getSelectedModel();
    const benchmark = MODEL_BENCHMARKS[model];
    setClassifyLoading(true);
    benchmarkSection.style.display = 'none';

    try {
        const resp = await fetch(`${API_BASE}${API_ENDPOINTS[model]}`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ request_id: `req_${Date.now()}`, request_text: text }),
        });
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.error_msg || `HTTP ${resp.status}`);
        fillCard(model, true, data);
    } catch (error) {
        fillCard(model, false, error.message);
    } finally {
        setClassifyLoading(false);
    }
}

// ============ 渲染辅助 ============

function renderBadges(results) {
    const arr = Array.isArray(results) ? results : [String(results)];
    return arr.map(cat => {
        const cls = CATEGORY_COLORS[cat] || 'badge-other';
        return `<span class="badge ${cls}">${escapeHtml(cat)}</span>`;
    }).join('');
}

// 保留 displayResult / showError 作为通用接口（新 UI 不直接使用）
function displayResult(data, model, benchmark) {
    fillCard(model, true, data);
}

function showError(message) {
    // 错误时重置为占位，顶部显示错误
    renderPlaceholderCards();
    // 在占位卡片上方添加一个简单的临时提示
    const firstCard = resultsGrid.firstElementChild;
    if (firstCard) {
        const errDiv = document.createElement('div');
        errDiv.style.cssText = 'grid-column:1/-1;background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);border-radius:8px;padding:12px 16px;color:var(--red);font-size:0.85rem;margin-bottom:4px;';
        errDiv.textContent = message;
        resultsGrid.prepend(errDiv);
        setTimeout(() => errDiv.remove(), 3000);
    }
}

function escapeHtml(text) {
    if (typeof text !== 'string') return String(text);
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function clearResults() {
    if (loading.classList.contains('active')) setClassifyLoading(false);
    renderPlaceholderCards();
    benchmarkSection.style.display = 'none';
    inputText.value = '';
    updateCharCount();
}

function displayBenchmarks(results) {
    const names = { regex: '正则匹配', tfidf: 'TF-IDF', bert: 'BERT', gpt: 'LLM' };
    const icons = { regex: 'filter', tfidf: 'chart-bar', bert: 'brain', gpt: 'comment-dots' };

    const times = {};
    results.forEach(r => { if (r.ok) times[r.key] = r.data.classify_time * 1000; });
    const vals = Object.values(times);
    const minT = Math.min(...vals);
    const maxT = Math.max(...vals);

    benchmarkBody.innerHTML = results.map(r => {
        const name = names[r.key] || r.key;
        const icon = icons[r.key] || 'cube';
        let td, tc;
        if (r.ok) {
            const ms = times[r.key];
            if (vals.length <= 1) tc = 'time-normal';
            else if (ms === minT) tc = 'time-fast';
            else if (ms === maxT) tc = 'time-slow';
            else tc = 'time-normal';
            td = `<span class="${tc}">${ms.toFixed(0)} ms</span>`;
        } else {
            td = '<span style="color:#5a6477;">失败</span>';
        }
        const acc = MODEL_BENCHMARKS[r.key].accuracy;
        const al = acc < 60 ? '低' : acc < 80 ? '中' : acc < 90 ? '高' : '非常高';
        const cost = MODEL_BENCHMARKS[r.key].cost;
        const cl = cost <= 2 ? '低' : cost <= 5 ? '中' : '高';
        return `<tr><td class="model-name"><i class="fas fa-${icon}"></i> ${name}</td><td>${td}</td><td>${al}</td><td>${cl}</td></tr>`;
    }).join('');
    benchmarkSection.style.display = 'block';
}
