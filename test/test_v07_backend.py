import urllib.request, json

tests = [
    ('regex', '帮我播放周杰伦的歌曲'),
    ('tfidf', '今天北京天气怎么样'),
    ('bert', '打开客厅的空调'),
    ('gpt', '提醒我明天上午开会'),
]

for model, text in tests:
    body = json.dumps({'request_id': 'v07', 'request_text': text}).encode()
    req = urllib.request.Request(
        f'http://localhost:8000/v1/text-cls/{model}',
        data=body,
        headers={'Content-Type': 'application/json'},
    )
    r = urllib.request.urlopen(req)
    data = json.loads(r.read())
    time_ms = round(data['classify_time'] * 1000, 0)
    print(f'[{model:5s}] {data["classify_result"]}  ({time_ms:.0f}ms)  error={data["error_msg"]}')
