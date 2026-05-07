"""验证 BERT 接口"""
import urllib.request, json

tests = [
    ("帮我播放周杰伦的歌曲", "Music-Play"),
    ("今天北京天气怎么样", "Weather-Query"),
    ("打开客厅的空调", "HomeAppliance-Control"),
    ("明天上午提醒我开会", "Alarm-Update"),
    ("农历五月初五是几号", "Calendar-Query"),
    ("我要去北京的高铁票", "Travel-Query"),
    ("播放一个游戏视频", "Video-Play"),
    ("收听FM103.9交通广播", "Radio-Listen"),
    ("讲一个故事给我听", "Audio-Play"),
    ("今天有什么电视剧", "FilmTele-Play"),
    ("看看电视节目表", "TVProgram-Play"),
    ("叽里咕噜乱七八糟", "Other"),
]

all_pass = True
for text, expected in tests:
    body = json.dumps({"request_id": "t", "request_text": text}).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:8000/v1/text-cls/bert",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    r = urllib.request.urlopen(req)
    data = json.loads(r.read())
    result = data["classify_result"]
    hit = expected == result[0] if isinstance(result, list) else expected == result
    if not hit:
        all_pass = False
    status = "PASS" if hit else "FAIL"
    print(f"[{status}] {text:25s} expected={expected:20s} got={result}")

print(f"\n=== {'ALL PASS' if all_pass else 'SOME FAILED'} ===")
