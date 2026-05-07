"""v0.9 回归测试：LLM 惰性初始化后，4 个 endpoint + 异常场景"""
import urllib.request, json, sys

API = 'http://localhost:8000'
passed = failed = 0

def check(label, ok, detail=''):
    global passed, failed
    if ok: passed += 1
    else: failed += 1
    print(f'  {"PASS" if ok else "FAIL"}  {label}  {detail}')

def post(model, text):
    body = json.dumps({'request_id':'t','request_text':text}).encode('utf-8')
    req = urllib.request.Request(f'{API}/v1/text-cls/{model}', data=body, method='POST')
    req.add_header('Content-Type', 'application/json')
    try:
        r = urllib.request.urlopen(req, timeout=30)
        return json.loads(r.read()), True
    except Exception as e:
        return str(e), False

print('=== 1. 健康检查 ===')
try:
    r = urllib.request.urlopen(API)
    d = json.loads(r.read())
    check('健康检查', d['status']=='running')
except Exception as e:
    check('健康检查', False, str(e))

print('=== 2. 4 个 endpoint ===')
for model in ['regex', 'tfidf', 'bert', 'gpt']:
    data, ok = post(model, '播放音乐')
    check(f'{model} 端点', ok and data.get('error_msg')=='ok', str(data.get('classify_result','')))

print('=== 3. 正则多标签 ===')
data, ok = post('regex', '帮我导航到北京，查下明天的天气')
check('regex 多标签', ok and len(data.get('classify_result',[]))>=2, str(data.get('classify_result','')))

print('=== 4. 前端服务正常 ===')
try:
    r = urllib.request.urlopen('http://localhost:8001/')
    check('前端页面', r.status == 200)
except:
    # 前端可能没起，这是可接受的
    check('前端页面', False, '(前端服务可能未启动，不影响后端验证)')

print(f'\n=== 结果: {passed} PASS / {failed} FAIL ===')
sys.exit(0 if failed==0 else 1)
