/* ============================================
   Retrieva Search Portal — App
   ============================================
   Edit the config below to connect to your
   Retrieva instance.
   ============================================ */

const RETRIEVA_CONFIG = {
    apiUrl: "http://localhost:8000",
    apiKey: "YOUR_PUBLIC_API_KEY",
    widgetId: "YOUR_WIDGET_ID",
};

// ---- State ----
let debounceTimer = null;
let currentQuery = "";
let activeIndex = -1;

// ---- DOM refs ----
const $searchInput = document.getElementById("searchInput");
const $searchClear = document.getElementById("searchClear");
const $searchHero = document.getElementById("searchHero");
const $filtersSidebar = document.getElementById("filtersSidebar");
const $resultsHeader = document.getElementById("resultsHeader");
const $resultsCount = document.getElementById("resultsCount");
const $resultsTime = document.getElementById("resultsTime");
const $resultsList = document.getElementById("resultsList");
const $stateEmpty = document.getElementById("stateEmpty");
const $stateLoading = document.getElementById("stateLoading");
const $stateNoResults = document.getElementById("stateNoResults");

// ---- Helpers ----

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function highlightQuery(text, query) {
    if (!query || !text) return escapeHtml(text || "");
    const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const re = new RegExp(`(${escaped})`, "gi");
    return escapeHtml(text).replace(re, "<mark>$1</mark>");
}

function getScoreClass(score) {
    if (score >= 0.8) return "high";
    if (score >= 0.5) return "medium";
    return "low";
}

function truncate(text, len) {
    if (!text) return "";
    return text.length > len ? text.substring(0, len) + "..." : text;
}

function showState(name) {
    $stateEmpty.style.display = name === "empty" ? "" : "none";
    $stateLoading.style.display = name === "loading" ? "" : "none";
    $stateNoResults.style.display = name === "no-results" ? "" : "none";
    $resultsList.style.display = name === "results" ? "" : "none";
    $resultsHeader.style.display = name === "results" ? "" : "none";
}

// ---- Render ----

function renderResults(results, elapsed) {
    if (results.length === 0) {
        showState("no-results");
        $filtersSidebar.classList.remove("visible");
        return;
    }

    showState("results");
    $filtersSidebar.classList.add("visible");
    $resultsCount.textContent = `${results.length} result${results.length !== 1 ? "s" : ""}`;
    $resultsTime.textContent = `${elapsed}ms`;

    $resultsList.innerHTML = results
        .map((result, i) => {
            const title = result.title || result.metadata?.filename || "Untitled Document";
            const content = result.content || result.text || result.snippet || "";
            const score = result.score ?? result.relevance_score ?? 0;
            const scorePercent = Math.round(score * 100);
            const scoreClass = getScoreClass(score);
            const docType = result.metadata?.type || result.metadata?.source || "document";

            return `
                <div class="result-card" data-index="${i}" tabindex="0">
                    <div class="result-card-header">
                        <div class="result-title">${highlightQuery(title, currentQuery)}</div>
                        <span class="result-score ${scoreClass}">${scorePercent}%</span>
                    </div>
                    <div class="result-snippet">${highlightQuery(truncate(content, 280), currentQuery)}</div>
                    <div class="result-meta">
                        <span class="result-meta-item">
                            <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><rect x="2" y="1" width="10" height="12" rx="1.5" stroke="currentColor" stroke-width="1.2" fill="none"/><path d="M5 4h4M5 6.5h4M5 9h2.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
                            ${escapeHtml(docType)}
                        </span>
                        ${
                            result.metadata?.chunk_index !== undefined
                                ? `<span class="result-meta-item">Chunk ${result.metadata.chunk_index + 1}</span>`
                                : ""
                        }
                    </div>
                </div>
            `;
        })
        .join("");

    activeIndex = -1;
}

// ---- API ----

async function performSearch(query) {
    currentQuery = query;
    const startTime = performance.now();

    showState("loading");
    $searchHero.classList.add("compact");

    try {
        const response = await fetch(`${RETRIEVA_CONFIG.apiUrl}/widget/search`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${RETRIEVA_CONFIG.apiKey}`,
            },
            body: JSON.stringify({
                query: query,
                widget_id: RETRIEVA_CONFIG.widgetId,
                top_k: 10,
            }),
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const data = await response.json();
        const elapsed = Math.round(performance.now() - startTime);
        const results = data.results || data.documents || data.hits || [];

        renderResults(results, elapsed);
    } catch (err) {
        console.error("Retrieva search error:", err);
        $resultsList.innerHTML = `
            <div class="state-no-results">
                <p>Search failed: ${escapeHtml(err.message)}</p>
            </div>
        `;
        $resultsList.style.display = "";
        $stateLoading.style.display = "none";
    }
}

function resetSearch() {
    $searchInput.value = "";
    $searchClear.style.display = "none";
    $searchHero.classList.remove("compact");
    $filtersSidebar.classList.remove("visible");
    showState("empty");
    currentQuery = "";
    activeIndex = -1;
    $searchInput.focus();
}

// ---- Debounced search ----

function debouncedSearch() {
    const query = $searchInput.value.trim();

    $searchClear.style.display = query ? "" : "none";

    if (!query) {
        resetSearch();
        return;
    }

    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
        performSearch(query);
    }, 300);
}

// ---- Keyboard navigation ----

function updateActiveCard(newIndex) {
    const cards = $resultsList.querySelectorAll(".result-card");
    if (cards.length === 0) return;

    cards.forEach((c) => c.classList.remove("active"));

    if (newIndex < 0) newIndex = cards.length - 1;
    if (newIndex >= cards.length) newIndex = 0;

    activeIndex = newIndex;
    cards[activeIndex].classList.add("active");
    cards[activeIndex].scrollIntoView({ block: "nearest" });
}

// ---- Events ----

$searchInput.addEventListener("input", debouncedSearch);

$searchClear.addEventListener("click", resetSearch);

// Cmd+K / Ctrl+K to focus
document.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        $searchInput.focus();
        $searchInput.select();
    }

    // Arrow nav in results
    if (e.key === "ArrowDown") {
        e.preventDefault();
        updateActiveCard(activeIndex + 1);
    }
    if (e.key === "ArrowUp") {
        e.preventDefault();
        updateActiveCard(activeIndex - 1);
    }

    // Escape to clear
    if (e.key === "Escape") {
        if ($searchInput.value) {
            resetSearch();
        } else {
            $searchInput.blur();
        }
    }
});

// ---- Init ----
showState("empty");
