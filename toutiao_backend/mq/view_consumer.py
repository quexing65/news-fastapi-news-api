"""浏览量消费者：订阅浏览量事件，攒批更新 MySQL 并清理受影响的缓存。

独立于 API 进程运行：
    uv run python -m mq.view_consumer
"""
import asyncio
import time

from aiokafka import AIOKafkaConsumer

from cache.news_cache import invalidate_news_views_cache
from config.db_conf import AsyncSessionLocal
from config.kafka_conf import (
    GROUP_NEWS_VIEW_COUNTER,
    KAFKA_BOOTSTRAP_SERVERS,
    TOPIC_NEWS_VIEWS,
    VIEW_FLUSH_INTERVAL,
    VIEW_FLUSH_MAX_BATCH,
)
from crud.news_cache import batch_increase_news_views
from schemas.mq import ViewEvent

# 攒批缓冲：news_id -> {"count": 本次增量, "category_id": 分类id}
# 同一篇新闻的 N 次浏览合并成一条 UPDATE，把写入热点削平
pending: dict[int, dict[str, int]] = {}


async def flush() -> bool:
    """把攒批的浏览量一次性落库：N次浏览合并成一条 UPDATE。

    失败时保留缓冲稍后重试（返回 False），成功才清缓冲 —— 保证 at-least-once。
    """
    if not pending:
        return True
    updates = dict(pending)
    try:
        async with AsyncSessionLocal() as db:
            await batch_increase_news_views(db, updates)
    except Exception as e:
        print(f"攒批落库失败，缓冲保留稍后重试：{e}", flush=True)
        return False
    pending.clear()
    total = sum(info["count"] for info in updates.values())
    print(f"攒批落库完成：{len(updates)} 篇新闻 / {total} 次浏览", flush=True)
    return True


async def consume():
    consumer = AIOKafkaConsumer(
        TOPIC_NEWS_VIEWS,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=GROUP_NEWS_VIEW_COUNTER,
        enable_auto_commit=False,  # 手动提交：落库成功后再提交消费位点
        auto_offset_reset="earliest",
    )
    # Kafka 可能晚于消费者启动，连接失败时定时重试
    while True:
        try:
            await consumer.start()
            break
        except Exception as e:
            print(f"Kafka 连接失败，3 秒后重试：{e}", flush=True)
            await asyncio.sleep(3)

    last_flush = time.monotonic()
    try:
        while True:
            batches = await consumer.getmany(timeout_ms=500, max_records=VIEW_FLUSH_MAX_BATCH)
            msg_count = 0
            for messages in batches.values():
                for msg in messages:
                    msg_count += 1
                    try:
                        event = ViewEvent.model_validate_json(msg.value)
                    except Exception as e:
                        print(f"非法消息，跳过：{e}", flush=True)  # 毒消息跳过，不能卡死整个分区
                        continue
                    slot = pending.setdefault(event.news_id, {"count": 0, "category_id": event.category_id})
                    slot["count"] += 1

            now = time.monotonic()
            if pending and (msg_count >= VIEW_FLUSH_MAX_BATCH or now - last_flush >= VIEW_FLUSH_INTERVAL):
                # 先落库、成功后再提交消费位点：失败保留缓冲重试，
                # 崩溃时未提交的消息会重新消费 —— 浏览量可能略多计但绝不丢（at-least-once）
                if await flush():
                    await consumer.commit()
                    last_flush = now
                else:
                    await asyncio.sleep(2)  # 落库失败退避，避免空转打爆数据库
    finally:
        # 退出前尽量把攒着的最后一批落库；成功才提交位点，避免丢消息
        if await flush():
            try:
                await consumer.commit()
            except Exception as e:
                print(f"退出前提交消费位点失败：{e}", flush=True)
        await consumer.stop()


def main():
    print(f"浏览量消费者启动：topic={TOPIC_NEWS_VIEWS} group={GROUP_NEWS_VIEW_COUNTER}", flush=True)
    asyncio.run(consume())


if __name__ == "__main__":
    main()
