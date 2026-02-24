/* ============================================
   Retrieva Chatbot — Full-Page App
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
const state = {
    messages: [],
    isLoading: false,
};

// ---- DOM refs ----
const $messages = document.getElementById("messages");
const $form = document.getElementById("inputForm");
const $input = document.getElementById("userInput");
const $sendBtn = document.getElementById("sendBtn");
const $sidebarToggle = document.getElementById("sidebarToggle");
const $sidebarClose = document.getElementById("sidebarClose");
const $sidebar = document.getElementById("sidebar");
const $newChatBtn = document.getElementById("newChatBtn");

// ---- Helpers ----

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Minimal markdown-like rendering:
 *  - **bold**
 *  - `inline code`
 *  - ```code blocks```
 *  - newlines -> <br>
 */
function renderMarkdown(text) {
    // Code blocks
    text = text.replace(/```([\s\S]*?)```/g, (_, code) => {
        return `<pre><code>${escapeHtml(code.trim())}</code></pre>`;
    });
    // Inline code
    text = text.replace(/`([^`]+)`/g, (_, code) => {
        return `<code>${escapeHtml(code)}</code>`;
    });
    // Bold
    text = text.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    // Line breaks (but not inside <pre>)
    text = text.replace(/\n/g, "<br>");
    // Wrap loose lines in <p> (simple approach)
    return text;
}

function scrollToBottom() {
    requestAnimationFrame(() => {
        $messages.scrollTop = $messages.scrollHeight;
    });
}

function autoResizeTextarea() {
    $input.style.height = "auto";
    $input.style.height = Math.min($input.scrollHeight, 150) + "px";
}

// ---- Render ----

function renderWelcome() {
    const suggestions = [
        "What can you help me with?",
        "Summarize the main topics",
        "How does this work?",
    ];

    $messages.innerHTML = `
        <div class="welcome">
            <div class="welcome-icon">
                <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
                    <rect width="28" height="28" rx="6" fill="var(--primary)"/>
                    <path d="M8 10h12M8 14h8M8 18h10" stroke="#fff" stroke-width="2" stroke-linecap="round"/>
                </svg>
            </div>
            <h2>How can I help you?</h2>
            <p>Ask me anything about the knowledge base. I will search through the documents and provide accurate answers with sources.</p>
            <div class="welcome-suggestions">
                ${suggestions
                    .map(
                        (s) =>
                            `<button class="suggestion-btn" data-suggestion="${escapeHtml(s)}">${escapeHtml(s)}</button>`
                    )
                    .join("")}
            </div>
        </div>
    `;

    // Bind suggestion buttons
    $messages.querySelectorAll(".suggestion-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            $input.value = btn.dataset.suggestion;
            handleSend();
        });
    });
}

function createMessageEl(msg) {
    const el = document.createElement("div");
    el.className = `message ${msg.role}`;

    const avatarLabel = msg.role === "user" ? "Y" : "R";

    let sourcesHtml = "";
    if (msg.sources && msg.sources.length > 0) {
        sourcesHtml = `
            <div class="sources">
                <div class="sources-label">Sources</div>
                ${msg.sources
                    .map(
                        (src, i) => `
                    <div class="source-item">
                        <span class="source-index">${i + 1}</span>
                        <span>${escapeHtml(src.title || src.content?.substring(0, 120) || "Document")}</span>
                    </div>
                `
                    )
                    .join("")}
            </div>
        `;
    }

    el.innerHTML = `
        <div class="message-avatar">${avatarLabel}</div>
        <div class="message-body">
            <div class="message-content">${
                msg.role === "user"
                    ? escapeHtml(msg.content)
                    : renderMarkdown(msg.content)
            }</div>
            ${sourcesHtml}
        </div>
    `;
    return el;
}

function renderMessages() {
    $messages.innerHTML = "";
    if (state.messages.length === 0) {
        renderWelcome();
        return;
    }
    state.messages.forEach((msg) => {
        $messages.appendChild(createMessageEl(msg));
    });
    scrollToBottom();
}

function showTyping() {
    const el = document.createElement("div");
    el.className = "message assistant";
    el.id = "typingMessage";
    el.innerHTML = `
        <div class="message-avatar">R</div>
        <div class="message-body">
            <div class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    $messages.appendChild(el);
    scrollToBottom();
}

function removeTyping() {
    const el = document.getElementById("typingMessage");
    if (el) el.remove();
}

// ---- API ----

async function sendQuery(question) {
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
        const errorText = await response.text().catch(() => "Unknown error");
        throw new Error(`API error ${response.status}: ${errorText}`);
    }

    return response.json();
}

// ---- Actions ----

async function handleSend() {
    const text = $input.value.trim();
    if (!text || state.isLoading) return;

    // Add user message
    state.messages.push({ role: "user", content: text });
    $input.value = "";
    $input.style.height = "auto";
    renderMessages();

    // Loading state
    state.isLoading = true;
    $sendBtn.disabled = true;
    showTyping();

    try {
        const data = await sendQuery(text);
        removeTyping();

        const answer = data.answer || data.response || "I could not generate an answer.";
        const sources = data.sources || data.documents || [];

        state.messages.push({
            role: "assistant",
            content: answer,
            sources: sources,
        });
    } catch (err) {
        removeTyping();
        console.error("Retrieva query error:", err);
        state.messages.push({
            role: "assistant",
            content: `Sorry, something went wrong. Please try again.\n\n\`${err.message}\``,
            sources: [],
        });
    } finally {
        state.isLoading = false;
        $sendBtn.disabled = false;
        renderMessages();
        $input.focus();
    }
}

function handleNewChat() {
    state.messages = [];
    renderMessages();
    $input.focus();
}

// ---- Events ----

$form.addEventListener("submit", (e) => {
    e.preventDefault();
    handleSend();
});

$input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
    }
});

$input.addEventListener("input", autoResizeTextarea);

$sidebarToggle.addEventListener("click", () => {
    $sidebar.classList.add("open");
});

$sidebarClose.addEventListener("click", () => {
    $sidebar.classList.remove("open");
});

$newChatBtn.addEventListener("click", handleNewChat);

// Close sidebar on outside click (mobile)
document.addEventListener("click", (e) => {
    if (
        $sidebar.classList.contains("open") &&
        !$sidebar.contains(e.target) &&
        e.target !== $sidebarToggle
    ) {
        $sidebar.classList.remove("open");
    }
});

// ---- Init ----
renderWelcome();
