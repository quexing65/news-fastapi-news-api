from aiokafka import AIOKafkaProducer

from config.kafka_conf import KAFKA_BOOTSTRAP_SERVERS, TOPIC_NEWS_VIEWS
from schemas.mq import ViewEvent

# 模块级单例：随应用启动创建、关闭销毁（main.py 的 lifespan 管理）
_producer: AIOKafkaProducer | None = None


async def start_producer():
    # Kafka 不可用时不能阻断 API 启动：浏览量统计属于辅助功能，降级为暂不统计
    global _producer
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        acks=1,  # leader 确认即可，浏览量允许极端情况下少量丢失，换取低延迟
    )
    try:
        await producer.start()
        _producer = producer
        print("Kafka 生产者启动成功", flush=True)
    except Exception as e:
        print(f"Kafka 生产者启动失败，浏览量统计暂不可用：{e}", flush=True)


async def stop_producer():
    global _producer
    if _producer is not None:
        await _producer.stop()
        _producer = None


def _log_send_error(future):
    # fire-and-forget：发送失败只记日志，不影响阅读主流程
    exc = future.exception()
    if exc:
        print(f"浏览量消息发送失败：{exc}", flush=True)


async def publish_view_event(news_id: int, category_id: int) -> bool:
    """发送浏览量事件，立即返回，不等待落库"""
    if _producer is None:
        return False
    try:
        # 构造到发送整体兜底：发布浏览量永远不能拖垮阅读主流程
        event = ViewEvent(news_id=news_id, category_id=category_id)
        future = await _producer.send(TOPIC_NEWS_VIEWS, event.model_dump_json().encode("utf-8"))
        future.add_done_callback(_log_send_error)
        return True
    except Exception as e:
        print(f"浏览量消息发送失败：{e}", flush=True)
        return False
