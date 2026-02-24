"""Schemas for the Query Analytics Dashboard."""

from pydantic import BaseModel, Field


class LatencyTrendPoint(BaseModel):
    """A single data point in the latency trend."""

    date: str = Field(..., description="Date in YYYY-MM-DD format")
    avg_latency: float = Field(..., description="Average latency in ms for this date")
    count: int = Field(..., description="Number of queries on this date")


class TopQuestion(BaseModel):
    """A frequently asked question."""

    question: str = Field(..., description="The question text")
    count: int = Field(..., description="Number of times this question was asked")
    avg_confidence: float = Field(..., description="Average confidence score for this question")


class ConfidenceBucket(BaseModel):
    """A bucket in the confidence distribution."""

    bucket: str = Field(..., description="Confidence range label, e.g. '0-0.2'")
    count: int = Field(..., description="Number of queries in this bucket")


class CollectionUsage(BaseModel):
    """Query count per collection."""

    collection_name: str = Field(..., description="Name of the collection")
    query_count: int = Field(..., description="Number of queries against this collection")


class AnalyticsDashboardResponse(BaseModel):
    """Full analytics dashboard payload."""

    total_queries: int = Field(0, description="Total number of queries")
    avg_latency_ms: float = Field(0.0, description="Overall average latency in milliseconds")
    avg_confidence: float = Field(0.0, description="Overall average confidence score")
    queries_today: int = Field(0, description="Number of queries made today")
    queries_this_week: int = Field(0, description="Number of queries in the current week")
    latency_trend: list[LatencyTrendPoint] = Field(
        default_factory=list,
        description="Daily latency trend for the last 30 days",
    )
    top_questions: list[TopQuestion] = Field(
        default_factory=list,
        description="Top 10 most frequently asked questions",
    )
    confidence_distribution: list[ConfidenceBucket] = Field(
        default_factory=list,
        description="Confidence score distribution across 5 buckets",
    )
    collection_usage: list[CollectionUsage] = Field(
        default_factory=list,
        description="Top 5 collections by query count",
    )
    error_rate: float = Field(0.0, description="Percentage of failed queries (0-100)")
