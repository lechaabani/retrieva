"""Smart Suggestions endpoint — analyses the tenant's RAG setup and returns
actionable recommendations."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.api_keys import get_current_tenant
from api.database import get_db
from api.models.api_key import ApiKey
from api.models.chunk import Chunk
from api.models.collection import Collection
from api.models.document import Document
from api.models.query_log import QueryLog
from api.models.tenant import Tenant
from api.schemas.suggestions import Suggestion, SuggestionsResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Suggestions"])


@router.get(
    "/suggestions",
    response_model=SuggestionsResponse,
    summary="Smart Suggestions",
    description="Analyse the tenant's RAG setup and return prioritised improvement suggestions.",
)
async def get_suggestions(
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> SuggestionsResponse:
    """Build a list of contextual suggestions based on the tenant's current state."""
    suggestions: list[Suggestion] = []

    # ---- Fetch basic stats ------------------------------------------------
    collection_count_res = await db.execute(
        select(func.count(Collection.id)).where(Collection.tenant_id == tenant.id)
    )
    collection_count: int = collection_count_res.scalar() or 0

    total_doc_count_res = await db.execute(
        select(func.count(Document.id))
        .join(Collection, Document.collection_id == Collection.id)
        .where(Collection.tenant_id == tenant.id)
    )
    total_doc_count: int = total_doc_count_res.scalar() or 0

    # ---- 1. No collections ------------------------------------------------
    if collection_count == 0:
        suggestions.append(
            Suggestion(
                id="no-collections",
                type="setup",
                priority=5,
                title="Creez votre premiere collection",
                description="Creez votre premiere collection pour commencer a ingerer et rechercher des documents.",
                action_label="Creer une collection",
                action_href="/collections",
                icon="FolderPlus",
            )
        )

    # ---- 2. Collections but no documents ----------------------------------
    if collection_count > 0 and total_doc_count == 0:
        suggestions.append(
            Suggestion(
                id="no-documents",
                type="setup",
                priority=5,
                title="Ajoutez des documents",
                description="Ajoutez des documents a vos collections pour alimenter votre base de connaissances.",
                action_label="Importer des documents",
                action_href="/documents",
                icon="FileUp",
            )
        )

    # ---- 3 & 4. Chunk size analysis ---------------------------------------
    if total_doc_count > 0:
        avg_chunk_words_res = await db.execute(
            select(
                func.avg(
                    func.array_length(
                        func.string_to_array(Chunk.content, text("' '")), 1
                    )
                )
            )
            .join(Collection, Chunk.collection_id == Collection.id)
            .where(Collection.tenant_id == tenant.id)
        )
        avg_chunk_words = avg_chunk_words_res.scalar()

        if avg_chunk_words is not None:
            if avg_chunk_words > 1000:
                suggestions.append(
                    Suggestion(
                        id="chunks-too-large",
                        type="warning",
                        priority=4,
                        title="Chunks trop volumineux",
                        description="Vos chunks sont tres grands (moyenne ~{} mots). Envisagez un chunking plus fin pour de meilleurs resultats de recherche.".format(
                            int(avg_chunk_words)
                        ),
                        action_label="Voir les parametres",
                        action_href="/settings",
                        icon="Scissors",
                    )
                )
            elif avg_chunk_words < 50:
                suggestions.append(
                    Suggestion(
                        id="chunks-too-small",
                        type="warning",
                        priority=4,
                        title="Chunks trop petits",
                        description="Vos chunks sont tres petits (moyenne ~{} mots). Envisagez un chunking plus large pour conserver davantage de contexte.".format(
                            int(avg_chunk_words)
                        ),
                        action_label="Voir les parametres",
                        action_href="/settings",
                        icon="Maximize2",
                    )
                )

    # ---- 5. Only one collection -------------------------------------------
    if collection_count == 1:
        suggestions.append(
            Suggestion(
                id="single-collection",
                type="optimization",
                priority=2,
                title="Organisez vos donnees",
                description="Creez des collections thematiques pour de meilleurs resultats et une gestion plus fine de vos documents.",
                action_label="Creer une collection",
                action_href="/collections",
                icon="LayoutGrid",
            )
        )

    # ---- 6. No public API key ---------------------------------------------
    public_key_res = await db.execute(
        select(func.count(ApiKey.id)).where(
            ApiKey.tenant_id == tenant.id,
            ApiKey.key_type == "public",
        )
    )
    public_key_count: int = public_key_res.scalar() or 0

    if public_key_count == 0:
        suggestions.append(
            Suggestion(
                id="no-public-key",
                type="tip",
                priority=3,
                title="Integrez un widget",
                description="Creez une cle API publique pour integrer un widget chatbot ou recherche sur votre site.",
                action_label="Gerer les cles API",
                action_href="/settings",
                icon="Key",
            )
        )

    # ---- 7. Large collection (>1000 docs) ---------------------------------
    if collection_count > 0:
        large_col_res = await db.execute(
            select(Collection.name, func.count(Document.id).label("doc_count"))
            .join(Document, Document.collection_id == Collection.id)
            .where(Collection.tenant_id == tenant.id)
            .group_by(Collection.id)
            .having(func.count(Document.id) > 1000)
            .limit(1)
        )
        large_col = large_col_res.first()
        if large_col:
            suggestions.append(
                Suggestion(
                    id="large-collection-rerank",
                    type="optimization",
                    priority=3,
                    title="Activez le reranking",
                    description="Excellente collection ! '{}' contient plus de 1000 documents. Pensez a activer le reranking pour ameliorer la pertinence.".format(
                        large_col[0]
                    ),
                    action_label="Configurer le reranking",
                    action_href="/settings",
                    icon="ArrowUpDown",
                )
            )

    # ---- 8. No queries logged ---------------------------------------------
    has_queries = False
    try:
        # Try analytics_events first (may not exist)
        try:
            analytics_res = await db.execute(
                text(
                    "SELECT COUNT(*) FROM analytics_events WHERE tenant_id = :tid"
                ).bindparams(tid=tenant.id)
            )
            has_queries = (analytics_res.scalar() or 0) > 0
        except Exception:
            # Fallback to query_logs
            await db.rollback()
            query_log_res = await db.execute(
                select(func.count(QueryLog.id)).where(
                    QueryLog.tenant_id == tenant.id
                )
            )
            has_queries = (query_log_res.scalar() or 0) > 0
    except Exception:
        logger.debug("Could not check query logs for suggestions", exc_info=True)

    if not has_queries:
        suggestions.append(
            Suggestion(
                id="no-queries",
                type="setup",
                priority=4,
                title="Testez vos collections",
                description="Testez vos collections dans le Playground pour verifier la qualite des reponses generees.",
                action_label="Ouvrir le Playground",
                action_href="/playground",
                icon="MessageSquare",
            )
        )

    # ---- 9. Pro tip (always) ----------------------------------------------
    suggestions.append(
        Suggestion(
            id="pro-tip-debugger",
            type="tip",
            priority=1,
            title="Astuce : Pipeline Debugger",
            description="Utilisez le Pipeline Debugger pour visualiser chaque etape du RAG (embedding, retrieval, reranking, generation) et optimiser vos performances.",
            action_label="Essayer le Debugger",
            action_href="/playground",
            icon="Bug",
        )
    )

    # Sort by priority descending and limit to 8
    suggestions.sort(key=lambda s: s.priority, reverse=True)
    suggestions = suggestions[:8]

    return SuggestionsResponse(suggestions=suggestions)
