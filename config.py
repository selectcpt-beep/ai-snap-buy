"""
智普 GLM Coding 抢购配置
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ======================== 目标网址 ========================
TARGET_URL = "https://bigmodel.cn/glm-coding?utm_source=bigModel&utm_medium=Experience-Center&utm_content=glm-code&utm_campaign=Platform_Ops&_channel_track_key=8IpDsEJ5"

# ======================== 浏览器状态文件 ========================
AUTH_STATE_FILE = os.path.join(BASE_DIR, "auth_state.json")

# ======================== 监控配置 ========================
CHECK_INTERVAL_SECONDS = 2        # 页面刷新检测间隔（秒）
FAST_CHECK_INTERVAL_SECONDS = 0.5  # 快速模式检测间隔（秒）

# ======================== 反检测配置 ========================
HEADLESS = False                   # 是否无头模式 (建议 False 以便观察)
VIEWPORT = {"width": 1440, "height": 900}
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"

# ======================== 按钮关键词 (用于匹配页面上的购买按钮) ========================
BUY_BUTTON_KEYWORDS = [
    "立即购买", "立即订阅", "抢购", "购买", "订阅",
    "立即开通", "开通", "buy", "subscribe", "purchase",
]

# 不可用/已售罄的关键词
SOLD_OUT_KEYWORDS = [
    "已售罄", "售罄", "已抢光", "抢光了", "sold out",
]

# 人数过多关键词
TOO_MANY_KEYWORDS = [
    "人数太多", "稍后再试", "稍后重试", "请稍后", "排队", "too many",
]

# ======================== 最大运行时间 (秒), 0 表示无限制 ========================
MAX_RUNTIME_SECONDS = 0

# ======================== 通知方式 ========================
ENABLE_SOUND = True   # 成功时播放系统声音
