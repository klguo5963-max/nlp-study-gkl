"""v0.8 UI 重构回归测试"""
import urllib.request, json, sys

API = 'http://localhost:8000'
FE = 'http://localhost:8001'

def T(label, ok, detail=''):
    sym = 'PASS' if ok else 'FAIL'
    print(f'  {sym}  {label}  {detail}')
    return ok

passes = fails = 0
def check(label, ok, detail=''):
    global passes, fails
    if ok: passes += 1
    else: fails += 1
    T(label, ok, detail)

print('=== 1. 后端 4 个 endpoint ===')
for name, ep in [('regex','/v1/text-cls/regex'),('tfidf','/v1/text-cls/tfidf'),('bert','/v1/text-cls/bert'),('gpt','/v1/text-cls/gpt')]:
    body = json.dumps({'request_id':'r','request_text':'今天天气怎么样'}).encode()
    try:
        r = urllib.request.urlopen(API+ep, data=body, headers={'Content-Type':'application/json'}, timeout=15)
        d = json.loads(r.read())
        check(name, d['error_msg']=='ok' and d['classify_result']!=[])
    except Exception as e:
        check(name, False, str(e))

print('=== 2. 正则多标签 ===')
body = json.dumps({'request_id':'r','request_text':'帮我导航到北京，查下明天的天气'}).encode()
try:
    r = urllib.request.urlopen(API+'/v1/text-cls/regex', data=body, headers={'Content-Type':'application/json'})
    d = json.loads(r.read())
    check('多标签', len(d['classify_result'])>=2, str(d['classify_result']))
except Exception as e:
    check('多标签', False, str(e))

print('=== 3. 健康检查 ===')
try:
    r = urllib.request.urlopen(API)
    d = json.loads(r.read())
    check('健康检查', d['status']=='running')
except Exception as e:
    check('健康检查', False, str(e))

print('=== 4. 前端文件完整性 ===')
for f, klist in [
    ('', ['resultsGrid','benchmarkSection','benchmarkBody','charCount','textWarning','classifyBtn','compareBtn','clearBtn','apiStatus','statusIndicator','loading']),
    ('script.js', ['processText','compareAllModels','clearResults','checkAPIStatus','fillCard','fillAllCards','renderPlaceholderCards','AbortController','allSettled','TEXT_WARN_LIMIT','setClassifyLoading']),
]:
    try:
        r = urllib.request.urlopen(FE+'/'+f)
        c = r.read().decode('utf-8')
        for k in klist:
            check(f'{f} has {k}', k in c)
    except Exception as e:
        check(f'{f} load', False, str(e))

print('=== 5. 边界保护 ===')
html = urllib.request.urlopen(FE+'/').read().decode('utf-8')
check('textWarning span exists', 'textWarning' in html)
check('model-chip exists', 'model-chip' in html)
check('space grotesk imported', 'Space+Grotesk' in html)
check('dm mono imported', 'DM+Mono' in html)

print(f'\n=== 结果: {passes} PASS / {fails} FAIL ===')
sys.exit(0 if fails==0 else 1)
