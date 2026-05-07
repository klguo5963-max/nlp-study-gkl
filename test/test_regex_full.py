"""验证正则模型所有类别覆盖"""
import urllib.request, json

tests = [
    # 每个类别至少一条
    ("帮我播放周杰伦的歌曲", "Music-Play"),   # 也可能匹配 FilmTele-Play
    ("打开客厅的空调", "HomeAppliance-Control"),
    ("今天北京天气怎么样", "Weather-Query"),
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
        "http://localhost:8000/v1/text-cls/regex",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    r = urllib.request.urlopen(req)
    data = json.loads(r.read())
    result = data["classify_result"]
    # 检查 expected 是否在 result 列表中
    hit = expected in result
    status = "PASS" if hit else "FAIL"
    if not hit:
        all_pass = False
    print(f"[{status}] {text:25s} expected={expected:20s} got={result}")

print()
print(f"=== {'ALL PASS' if all_pass else 'SOME FAILED'} ===")
