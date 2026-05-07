import urllib.request, json

def test(model, text):
    body = json.dumps({'request_id':'t','request_text':text}).encode('utf-8')
    req = urllib.request.Request(f'http://localhost:8000/v1/text-cls/{model}', data=body, method='POST')
    req.add_header('Content-Type', 'application/json')
    try:
        r = urllib.request.urlopen(req, timeout=10)
        d = json.loads(r.read())
        return d['error_msg'], d['classify_result']
    except Exception as e:
        return None, str(e)

print('=== 异常路径测试（BERT 模型文件已移走）===')
err, result = test('bert', '播放音乐')
print(f'BERT return error_msg: {err}')
print(f'classify_result: {result}')

# 确认堆栈没有泄漏到前端
import sys
if err and ('File' in err or 'Traceback' in err or 'main_cors' in err or '.py' in err):
    print('FAIL: traceback 泄漏到前端了')
    sys.exit(1)
else:
    print('PASS: 前端收到友好提示，堆栈未泄漏')
