"""v0.8 后端回归测试（正确 POST 方式）"""
import urllib.request, json

API = 'http://localhost:8000'

def test_endpoint(name, ep, text):
    body = json.dumps({'request_id':'t','request_text':text}).encode('utf-8')
    req = urllib.request.Request(API+ep, data=body, method='POST')
    req.add_header('Content-Type', 'application/json')
    try:
        r = urllib.request.urlopen(req, timeout=30)
        d = json.loads(r.read())
        ok = d['error_msg'] == 'ok' and len(d['classify_result']) > 0
        print(f'  {name:5s} {d["classify_result"]}  -> {"PASS" if ok else "FAIL"}')
    except Exception as e:
        print(f'  {name:5s} FAILED: {e}')

print('=== 后端 endpoint 回归 ===')
test_endpoint('regex', '/v1/text-cls/regex', '播放音乐')
test_endpoint('tfidf', '/v1/text-cls/tfidf', '今天天气')
test_endpoint('bert', '/v1/text-cls/bert', '打开空调')
test_endpoint('gpt', '/v1/text-cls/gpt', '提醒我开会')

print('=== 正则多标签 ===')
test_endpoint('多标签', '/v1/text-cls/regex', '帮我导航到北京，查下明天的天气')

print('=== 健康检查 ===')
r = urllib.request.urlopen(API)
d = json.loads(r.read())
print(f'  status={d["status"]} version={d["version"]}')
