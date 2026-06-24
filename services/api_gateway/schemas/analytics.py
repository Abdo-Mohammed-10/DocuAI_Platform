from pydantic import BaseModel


class OverviewResponse(BaseModel):
    user_id:           str
    total_documents:   int
    total_messages:    int


class DocumentStatusCount(BaseModel):
    status: str
    count:  int


class AnalyticsDashboardResponse(BaseModel):
    overview:        OverviewResponse
    status_breakdown: list[DocumentStatusCount]