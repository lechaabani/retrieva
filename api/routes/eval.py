"""RAG Evaluation endpoints -- test suites for measuring RAG quality."""

import logging
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.api_keys import get_current_tenant
from api.database import get_db
from api.models.tenant import Tenant

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Evaluation"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class TestCase(BaseModel):
    question: str
    expected_answer: Optional[str] = None
    expected_sources: Optional[list[str]] = Field(
        default=None,
        description="Expected document titles or IDs in sources",
    )


class TestSuiteRequest(BaseModel):
    name: str = "Test Suite"
    collection: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Target collection name (must exist for the tenant)",
    )
    top_k: int = Field(default=5, ge=1, le=100)
    test_cases: list[TestCase]


class TestCaseResult(BaseModel):
    question: str
    answer: str
    expected_answer: Optional[str] = None
    sources: list[dict]
    confidence: float
    latency_ms: float
    relevance_score: Optional[float] = None
    answer_similarity: Optional[float] = None
    source_hit: Optional[bool] = None


class TestSuiteResult(BaseModel):
    name: str
    total_cases: int
    avg_confidence: float
    avg_latency_ms: float
    avg_relevance: Optional[float] = None
    source_hit_rate: Optional[float] = None
    results: list[TestCaseResult]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _word_overlap(expected: str, actual: str) -> float:
    """Simple word-overlap similarity between expected and actual answers."""
    expected_words = set(expected.lower().split())
    actual_words = set(actual.lower().split())
    if not expected_words:
        return 0.0
    return round(len(expected_words & actual_words) / len(expected_words), 3)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/eval/run",
    response_model=TestSuiteResult,
    summary="Run Evaluation Suite",
    description="Execute a test suite against the RAG pipeline and return scored results.",
)
async def run_eval(
    payload: TestSuiteRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> TestSuiteResult:
    """Run each test case through the query pipeline and score results."""
    from api.routes.query import (
        _build_generation_engine,
        _build_reranker,
        _build_retrieval_engine,
        _resolve_collection,
    )
    from core.config import get_config
    from core.retrieval.engine import SearchOptions, SearchStrategy

    # Resolve the collection once (validates it exists for this tenant)
    collection = await _resolve_collection(payload.collection, tenant, db)
    cfg = get_config()

    # Build engines once for the whole suite
    try:
        retrieval_engine = _build_retrieval_engine()
        generation_engine = _build_generation_engine()
        reranker = _build_reranker()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to initialize RAG engines: {exc}",
        )

    search_options = SearchOptions(
        strategy=SearchStrategy(cfg.retrieval.default_strategy),
        top_k=payload.top_k,
        score_threshold=cfg.retrieval.score_threshold,
        vector_weight=cfg.retrieval.hybrid_vector_weight,
        keyword_weight=cfg.retrieval.hybrid_keyword_weight,
    )

    results: list[TestCaseResult] = []
    total_confidence = 0.0
    total_latency = 0.0
    total_relevance = 0.0
    relevance_count = 0
    source_hits = 0
    source_checks = 0

    for tc in payload.test_cases:
        start = time.perf_counter()
        try:
            # -- Retrieve ------------------------------------------------
            retrieval_result = await retrieval_engine.search(
                query=tc.question,
                collection_id=str(collection.id),
                options=search_options,
            )
            chunks = retrieval_result.chunks

            # -- Rerank --------------------------------------------------
            if reranker and chunks:
                try:
                    chunks = await reranker.rerank(
                        query=tc.question,
                        chunks=chunks,
                        top_k=payload.top_k,
                    )
                except Exception as exc:
                    logger.warning("Reranking failed during eval, using original ranking: %s", exc)

            # -- Generate ------------------------------------------------
            generation_result = await generation_engine.generate(
                query=tc.question,
                chunks=chunks,
                language="en",
            )

            latency = (time.perf_counter() - start) * 1000
            answer_text = generation_result.answer
            confidence = generation_result.confidence

            # Build source list for the response
            sources = [
                {
                    "title": chunk.metadata.get("title", ""),
                    "content": chunk.content[:200],
                    "score": chunk.score,
                }
                for chunk in chunks
            ]

            # Top relevance score
            relevance_score = chunks[0].score if chunks else None
            if relevance_score is not None:
                total_relevance += relevance_score
                relevance_count += 1

            # Check source hits
            source_hit = None
            if tc.expected_sources:
                source_titles = [s["title"].lower() for s in sources]
                hits = sum(
                    1
                    for es in tc.expected_sources
                    if any(es.lower() in st for st in source_titles)
                )
                source_hit = hits > 0
                source_checks += 1
                if source_hit:
                    source_hits += 1

            # Answer similarity
            answer_similarity = None
            if tc.expected_answer:
                answer_similarity = _word_overlap(tc.expected_answer, answer_text)

            total_confidence += confidence
            total_latency += latency

            results.append(
                TestCaseResult(
                    question=tc.question,
                    answer=answer_text,
                    expected_answer=tc.expected_answer,
                    sources=sources,
                    confidence=confidence,
                    latency_ms=round(latency, 1),
                    relevance_score=relevance_score,
                    answer_similarity=answer_similarity,
                    source_hit=source_hit,
                )
            )
        except Exception as exc:
            latency = (time.perf_counter() - start) * 1000
            total_latency += latency
            logger.error("Eval test case failed for question '%s': %s", tc.question, exc)
            results.append(
                TestCaseResult(
                    question=tc.question,
                    answer=f"Error: {exc}",
                    expected_answer=tc.expected_answer,
                    sources=[],
                    confidence=0.0,
                    latency_ms=round(latency, 1),
                )
            )

    n = len(results) or 1
    return TestSuiteResult(
        name=payload.name,
        total_cases=len(results),
        avg_confidence=round(total_confidence / n, 3),
        avg_latency_ms=round(total_latency / n, 1),
        avg_relevance=round(total_relevance / relevance_count, 3) if relevance_count > 0 else None,
        source_hit_rate=round(source_hits / source_checks, 3) if source_checks > 0 else None,
        results=results,
    )


@router.post(
    "/eval/quick",
    response_model=TestCaseResult,
    summary="Quick Single Query Test",
    description="Run a single test query and return detailed results.",
)
async def quick_eval(
    question: str,
    collection: str,
    expected_answer: Optional[str] = None,
    top_k: int = 5,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> TestCaseResult:
    """Quick test -- run a single question through the pipeline."""
    suite = TestSuiteRequest(
        name="Quick Test",
        collection=collection,
        top_k=top_k,
        test_cases=[TestCase(question=question, expected_answer=expected_answer)],
    )
    result = await run_eval(suite, tenant, db)
    return result.results[0]
