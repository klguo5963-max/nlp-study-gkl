"""v0.7.1 边界修复回归测试"""
import urllib.request, json

API = 'http://localhost:8000'
results = {'pass': 0, 'fail': 0}

def check(label, ok, detail=''):
    if ok:
        results['pass'] += 1
        print(f'  PASS  {label}')
    else:
        results['fail'] += 1
        print(f'  FAIL  {label}  {detail}')

# 1. 后端四个 endpoint
print('=== 后端点回归 ===')
models_endpoints = [('regex', '/v1/text-cls/regex'), ('tfidf', '/v1/text-cls/tfidf'),
                    ('bert', '/v1/text-cls/bert'), ('gpt', '/v1/text-cls/gpt')]
for name, ep in models_endpoints:
    body = json.dumps({'request_id': 'r', 'request_text': '今天天气怎么样'}).encode()
    req = urllib.request.Request(API + ep, data=body, headers={'Content-Type': 'application/json'})
    try:
        r = urllib.request.urlopen(req, timeout=15)
        data = json.loads(r.read())
        ok = data['error_msg'] == 'ok' and len(data['classify_result']) > 0
        check(name, ok, f'status={r.status} error={data.get("error_msg")}')
    except Exception as e:
        check(name, False, str(e))

# 2. 正则多类别返回（导航北京+查天气）
print('=== 正则多标签 ===')
body = json.dumps({'request_id': 'r', 'request_text': '帮我导航到北京，查下明天的天气'}).encode()
req = urllib.request.Request(API + '/v1/text-cls/regex', data=body, headers={'Content-Type': 'application/json'})
try:
    r = urllib.request.urlopen(req)
    data = json.loads(r.read())
    check('正则多标签', len(data['classify_result']) >= 2, str(data['classify_result']))
except Exception as e:
    check('正则多标签', False, str(e))

# 3. 健康检查
print('=== 健康检查 ===')
try:
    r = urllib.request.urlopen(API)
    data = json.loads(r.read())
    check('健康检查', data['status'] == 'running')
except Exception as e:
    check('健康检查', False, str(e))

# 4. 前端 JS 文件包含新特性
print('=== 前端 JS 特性 ===')
try:
    r = urllib.request.urlopen('http://localhost:8001/script.js')
    js = r.read().decode('utf-8')
    check('AbortController', 'AbortController' in js)
    check('allSettled', 'allSettled' in js)
    check('TEXT_WARN_LIMIT=200', 'TEXT_WARN_LIMIT = 200' in js or 'TEXT_WARN_LIMIT=200' in js)
    check('TEXT_ERROR_LIMIT=500', 'TEXT_ERROR_LIMIT = 500' in js or 'TEXT_ERROR_LIMIT=500' in js)
    check('textWarning元素', 'getElementById' + "('textWarning')" in js or 'getElementById("textWarning")' in js)
    check('加载态清空兜底', 'loading.classList.contains' in js.split('clearResults')[1])
except Exception as e:
    check('前端 JS load', False, str(e))

# 5. HTML/CSS 新元素
print('=== 前端 HTML ===')
try:
    r = urllib.request.urlopen('http://localhost:8001/')
    html = r.read().decode('utf-8')
    check('textWarning span', 'id="textWarning"' in html)
except Exception as e:
    check('前端 HTML', False, str(e))

print(f'\n=== 结果: {results["pass"]} PASS / {results["fail"]} FAIL ===')
