from pydantic import BaseModel


class AnalyticsOverviewResponse(BaseModel):
    user_id: str
    total_documents: int
    total_messages: int