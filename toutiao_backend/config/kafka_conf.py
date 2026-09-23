import os
from pathlib import Path

from dotenv import load_dotenv

# 加载 .env 文件（与 db_conf 保持一致）
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Kafka 连接地址：生产者（API 进程）和消费者（独立进程）共用
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

# 浏览量事件主题 & 消费组
# 同一消费组内的多个消费者分担分区，天然支持横向扩容
TOPIC_NEWS_VIEWS = "news-views"
GROUP_NEWS_VIEW_COUNTER = "news-view-counter"

# 消费端攒批参数：满足其一即触发落库（消息数攒够 或 等待够久）
VIEW_FLUSH_INTERVAL = 3.0     # 秒
VIEW_FLUSH_MAX_BATCH = 500    # 条
