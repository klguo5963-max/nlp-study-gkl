import urllib.request, json

tests = [
    ("帮我播放周杰伦的歌曲", ["FilmTele-Play"]),
    ("播放电视剧狂飙", ["FilmTele-Play"]),
    ("打开客厅的空调", ["HomeAppliance-Control"]),
    ("听一下中央广播电台", ["HomeAppliance-Control"]),
    ("今天北京天气怎么样", ["Other"]),
    ("听不懂你在说什么", ["Other"]),
]

for text, expected in tests:
    body = json.dumps({"request_id": "t", "request_text": text}).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:8000/v1/text-cls/regex",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    r = urllib.request.urlopen(req)
    data = json.loads(r.read())
    result = data["classify_result"]
    ok = "PASS" if result == expected else "FAIL"
    print(f"[{ok}] {text:20s} -> {result}  ({data['classify_time']}s)")
