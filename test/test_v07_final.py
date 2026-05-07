import urllib.request, json

tests = [
    ('regex', '帮我导航到北京，查下明天的天气'),
    ('tfidf', '帮我导航到北京，查下明天的天气'),
    ('bert', '帮我导航到北京，查下明天的天气'),
    ('gpt', '帮我导航到北京，查下明天的天气'),
]

for model, text in tests:
    body = json.dumps({'request_id': 'v07r3', 'request_text': text}).encode()
    req = urllib.request.Request(
        f'http://localhost:8000/v1/text-cls/{model}',
        data=body,
        headers={'Content-Type': 'application/json'},
    )
    try:
        r = urllib.request.urlopen(req, timeout=30)
        data = json.loads(r.read())
        print(f'[{model:5s}] {data["classify_result"]}  ({round(data["classify_time"]*1000,0):.0f}ms)')
    except Exception as e:
        print(f'[{model:5s}] FAILED: {e}')
