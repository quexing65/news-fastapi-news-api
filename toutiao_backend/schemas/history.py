from pydantic import BaseModel, Field


class HistoryAddRequest(BaseModel):
    news_id: int = Field(alias="newsId")
