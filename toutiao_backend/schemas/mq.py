from pydantic import BaseModel


# 浏览量事件：详情接口 → Kafka → 消费者攒批落库
class ViewEvent(BaseModel):
    news_id: int
    category_id: int
