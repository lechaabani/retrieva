/* ============================================
   Retrieva FAQ Bot — App
   ============================================
   Edit the config below to connect to your
   Retrieva instance.
   ============================================ */

const RETRIEVA_CONFIG = {
    apiUrl: "http://localhost:8000",
    apiKey: "YOUR_PUBLIC_API_KEY",
    widgetId: "YOUR_WIDGET_ID",
};

/**
 * Pre-defined suggested questions.
 * Customize these to match your knowledge base content.
 */
const SUGGESTED_QUESTIONS = [
    { icon: "🚀", text: "How do I get started?" },
    { icon: "🔑", text: "How does authentication work?" },
    { icon: "📄", text: "What file formats are supported?" },
    { icon: "⚡", text: "How can I improve search accuracy?" },
    { icon: "🔌", text: "What integrations are available?" },
    { icon: "💰", text: "What are the pricing plans?" },
];

// ---- State ----
let isLoading = false;
let sourcesOpen = false;

// ---- DOM refs ----
const $suggestionsGrid = document.getElementById("suggestionsGrid");
const $answerSection = document.getElementById("answerSection");
const $answerCard = document.getElementById("answerCard");
const $answerQuestion = document.getElementById("answerQuestion");
const $answerLoading = document.getElementById("answerLoading");
const $answerBody = document.getElementById("answerBody");
const $answerText = document.getElementById("answerText");
const $answerError = document.getElementById("answerError");
const $answerClose = document.getElementById("answerClose");
const $sourcesAccordion = document.getElementById("sourcesAccordion");
const $sourcesToggle = document.getElementById("sourcesToggle");
const $sourcesLabel = document.getElementById("sourcesLabel");
const $sourcesList = document.getElementById("sourcesList");
const $customForm = document.getElementById("customForm");
const $customInput = document.getElementById("customInput");
const $customSubmitBtn = document.getElementById("customSubmitBtn");

// ---- Helpers ----

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function renderMarkdown(text) {
    text = text.replace(/```([\s\S]*?)```/g, (_, code) => {
        return `<pre><code>${escapeHtml(code.trim())}</code></pre>`;
    });
    text = text.replace(/`([^`]+)`/g, (_, code) => {
        return `<code>${escapeHtml(code)}</code>`;
    });
    text = text.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    text = text.replace(/\n\n/g, "</p><p>");
    text = text.replace(/\n/g, "<br>");
    return `<p>${text}</p>`;
}

// ---- Render Suggestions ----

function renderSuggestions() {
    $suggestionsGrid.innerHTML = SUGGESTED_QUESTIONS.map(
        (q, i) => `
        <button class="suggestion-chip" data-index="${i}">
            <span class="chip-icon">${q.icon}</span>
            ${escapeHtml(q.text)}
        </button>
    `
    ).join("");

    $suggestionsGrid.querySelectorAll(".suggestion-chip").forEach((chip) => {
        chip.addEventListener("click", () => {
            const idx = parseInt(chip.dataset.index, 10);
            askQuestion(SUGGESTED_QUESTIONS[idx].text);

            // Highlight active chip
            $suggestionsGrid
                .querySelectorAll(".suggestion-chip")
                .forEach((c) => c.classList.remove("active"));
            chip.classList.add("active");
        });
    });
}

// ---- Answer display ----

function showAnswerState(state) {
    $answerLoading.style.display = state === "loading" ? "" : "none";
    $answerBody.style.display = state === "body" ? "" : "none";
    $answerError.style.display = state === "error" ? "" : "none";
}

function showAnswer(question) {
    $answerSection.style.display = "";
    $answerQuestion.textContent = question;
    sourcesOpen = false;
    $sourcesAccordion.classList.remove("open");
    $sourcesAccordion.style.display = "none";

    // Scroll into view
    setTimeout(() => {
        $answerSection.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }, 100);
}

function closeAnswer() {
    $answerSection.style.display = "none";
    $suggestionsGrid
        .querySelectorAll(".suggestion-chip")
        .forEach((c) => c.classList.remove("active"));
}

function renderSources(sources) {
    if (!sources || sources.length === 0) {
        $sourcesAccordion.style.display = "none";
        return;
    }

    $sourcesAccordion.style.display = "";
    $sourcesLabel.textContent = `Show sources (${sources.length})`;

    $sourcesList.innerHTML = sources
        .map(
            (src, i) => `
        <div class="source-card">
            <span class="source-number">${i + 1}</span>
            <span>${escapeHtml(src.title || src.content?.substring(0, 150) || "Document " + (i + 1))}</span>
        </div>
    `
        )
        .join("");
}

// ---- API ----

async function askQuestion(question) {
    if (isLoading) return;

    isLoading = true;
    $customSubmitBtn.disabled = true;

    showAnswer(question);
    showAnswerState("loading");

    try {
        const response = await fetch(`${RETRIEVA_CONFIG.apiUrl}/widget/query`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${RETRIEVA_CONFIG.apiKey}`,
            },
            body: JSON.stringify({
                question: question,
                widget_id: RETRIEVA_CONFIG.widgetId,
            }),
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const data = await response.json();
        const answer = data.answer || data.response || "No answer found.";
        const sources = data.sources || data.documents || [];

        $answerText.innerHTML = renderMarkdown(answer);
        renderSources(sources);
        showAnswerState("body");
    } catch (err) {
        console.error("Retrieva query error:", err);
        showAnswerState("error");
    } finally {
        isLoading = false;
        $customSubmitBtn.disabled = false;
    }
}

// ---- Events ----

$answerClose.addEventListener("click", closeAnswer);

$sourcesToggle.addEventListener("click", () => {
    sourcesOpen = !sourcesOpen;
    $sourcesAccordion.classList.toggle("open", sourcesOpen);
    $sourcesLabel.textContent = sourcesOpen
        ? `Hide sources`
        : `Show sources (${$sourcesList.children.length})`;
});

$customForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const question = $customInput.value.trim();
    if (!question) return;

    // Clear active chip highlight
    $suggestionsGrid
        .querySelectorAll(".suggestion-chip")
        .forEach((c) => c.classList.remove("active"));

    askQuestion(question);
    $customInput.value = "";
});

// ---- Init ----
renderSuggestions();
