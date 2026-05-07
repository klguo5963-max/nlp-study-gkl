"""
集中配置文件
所有可调参数统一在此管理
"""

# 正则规则: 类别 -> 关键词列表
# 关键词基于数据集实际统计选取，覆盖核心词汇即可，
# 无需全量覆盖（剩余由 TF-IDF/BERT/LLM 处理）
REGEX_RULE = {
    "Alarm-Update": [
        "闹钟", "提醒", "备忘录", "记得", "删除", "取消", "关闭",
        "设定", "设置", "创建", "增加", "修改"
    ],
    "Audio-Play": [
        "有声小说", "小说", "广播剧", "故事", "音频"
    ],
    "Calendar-Query": [
        "农历", "几号", "星期几", "周几", "礼拜", "节日",
        "啥时候", "哪天", "是几", "是什么时候"
    ],
    "FilmTele-Play": [
        "播放", "电视剧", "电影", "剧", "影片", "剧集",
        "REGEX:看.*剧", "REGEX:看.*电影", "REGEX:看.*片"
    ],
    "HomeAppliance-Control": [
        "空调", "洗衣机", "冰箱", "开关", "打开", "关闭",
        "调高", "调低", "温度", "模式", "风速", "调到",
        "加湿器", "净化器", "空气净化器", "电饭煲", "电扇",
        "浴霸", "窗帘", "热水器", "电磁炉", "烤箱", "灯"
    ],
    "Music-Play": [
        "播放", "歌曲", "音乐", "歌", "听", "单曲循环",
        "循环", "专辑", "唱", "来一首", "放一首", "随机",
        "顺序播放"
    ],
    "Other": [],  # 兜底，不设关键词
    "Radio-Listen": [
        "广播", "电台", "频率", "FM", "收听", "之声",
        "广播电台", "音乐台", "交通广播", "频道"
    ],
    "TVProgram-Play": [
        "电视节目", "节目表", "电视", "回看", "重播"
    ],
    "Travel-Query": [
        "机票", "高铁", "火车", "汽车票", "航班",
        "路线", "导航", "怎么走", "怎么去", "REGEX:到.*怎么",
        "打车", "动车", "大巴", "车票", "票价"
    ],
    "Video-Play": [
        "视频", "直播", "游戏视频", "解说", "比赛视频",
        "回放", "花絮", "录播", "REGEX:看.*视频"
    ],
    "Weather-Query": [
        "天气", "温度", "下雨", "气温", "紫外线",
        "湿度", "空气质量", "风力", "风大", "降温",
        "降雨", "下雪", "晴天", "阴天", "台风",
        "雾霾", "多少度"
    ],
}

# 全部类别列表
# 字母序类别列表（与 LabelEncoder.fit() 字母排序一致）
CATEGORY_NAME: list[str] = [
    'Alarm-Update', 'Audio-Play', 'Calendar-Query', 'FilmTele-Play',
    'HomeAppliance-Control', 'Music-Play', 'Other', 'Radio-Listen',
    'TVProgram-Play', 'Travel-Query', 'Video-Play', 'Weather-Query',
]

# 数据集路径
DATASET_PATH: str = "assets/dataset/dataset.csv"
STOPWORDS_PATH: str = "assets/dataset/baidu_stopwords.txt"

# 模型权重路径
TFIDF_MODEL_PKL_PATH: str = "assets/weights/tfidf_ml.pkl"
BERT_MODEL_PKL_PATH: str = "assets/weights/bert.pt"
BERT_MODEL_PERTRAINED_PATH: str = "assets/models/bert-base-chinese/"

# LLM 配置（OpenAI 兼容接口）
# API Key 从 .env 文件加载，不在代码中硬编码
LLM_OPENAI_SERVER_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
LLM_API_KEY_ENV: str = "LLM_API_KEY"  # .env 中的环境变量名
LLM_MODEL_NAME: str = "qwen3-max"
