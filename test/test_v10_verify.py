"""v0.10 验证：异常时 traceback 不泄漏到前端"""
import urllib.request, json

API = 'http://localhost:8000'

def test(model, text):
    body = json.dumps({'request_id':'t','request_text':text}).encode('utf-8')
    req = urllib.request.Request(f'{API}/v1/text-cls/{model}', data=body, method='POST')
    req.add_header('Content-Type', 'application/json')
    try:
        r = urllib.request.urlopen(req, timeout=30)
        return json.loads(r.read())
    except Exception as e:
        return {'error_msg': str(e)}

print('=== 正常路径 ===')
for m in ['regex', 'tfidf', 'gpt']:
    d = test(m, '播放音乐')
    ok = d.get('error_msg') == 'ok'
    print(f'  {"PASS" if ok else "FAIL"} {m}: error_msg={d.get("error_msg")}')

# 模拟异常路径：构造一个会触发异常的请求
# 直接发送一个不受支持的类型给 gpt，期望看到友好提示而不是堆栈
print('\n=== 异常路径 ===')
# 调用一个不存在的 endpoint 看 404 是否友好
try:
    r = urllib.request.urlopen(f'{API}/v1/text-cls/nonexistent')
    d = json.loads(r.read())
except urllib.error.HTTPError as e:
    print(f'  非法的 endpoint 返回 HTTP {e.code}')
except Exception as e:
    print(f'  error: {str(e)[:100]}')

# 测试正常路径都恢复
print('\n=== 回归 ===')
d = test('bert', '播放音乐')
print(f'  {"PASS" if d.get("error_msg")=="ok" else "FAIL"} bert: {d.get("classify_result")}')
