import urllib.request, json

tests = [
    ('regex', '播放音乐'),
    ('tfidf', '今天天气'),
    ('bert', '打开空调'),
    ('gpt', '提醒我开会'),
]
for model, text in tests:
    body = json.dumps({'request_id':'t','request_text':text}).encode('utf-8')
    req = urllib.request.Request(f'http://localhost:8000/v1/text-cls/{model}', data=body, method='POST')
    req.add_header('Content-Type', 'application/json')
    try:
        r = urllib.request.urlopen(req, timeout=30)
        d = json.loads(r.read())
        print(f'{model:5s} error={d["error_msg"]:5s} time={d["classify_time"]:.3f}s result={d["classify_result"]}')
    except Exception as e:
        print(f'{model:5s} FAILED: {e}')
