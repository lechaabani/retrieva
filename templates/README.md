# Retrieva Templates

Pre-built, standalone HTML/CSS/JS web apps that connect to the Retrieva RAG API. Each template is a complete, self-contained application with no external dependencies or build steps required.

## Available Templates

### 1. `chatbot-fullpage/`

A full-page conversational chatbot interface (similar to ChatGPT). Features a sidebar, message history, typing animation, markdown rendering, and source citations under assistant responses.

**Best for:** Internal knowledge assistants, customer support bots, document Q&A interfaces.

### 2. `search-portal/`

An instant search portal with result cards, relevance scores, and a filters sidebar. Includes debounced search (300ms), keyboard navigation (Cmd+K to focus, arrow keys to navigate results), and highlighted query terms.

**Best for:** Documentation search, knowledge base search pages, semantic search UIs.

### 3. `faq-bot/`

An FAQ-style interface with pre-defined suggested questions displayed as clickable chips. Clicking a chip (or typing a custom question) shows an answer with a collapsible sources section.

**Best for:** Help centers, product FAQ pages, onboarding guides.

## Quick Start

1. **Copy** the template directory you want to use.

2. **Edit the config** at the top of `app.js`:

   ```javascript
   const RETRIEVA_CONFIG = {
       apiUrl: "http://localhost:8000",   // Your Retrieva API URL
       apiKey: "YOUR_PUBLIC_API_KEY",     // Your public API key
       widgetId: "YOUR_WIDGET_ID",        // Your widget ID
   };
   ```

3. **Open `index.html`** in a browser, or deploy to any static hosting provider.

## Customization

### Theming

All templates use CSS custom properties defined in `styles.css`. Edit the `:root` block to change colors:

```css
:root {
    --primary: #4F46E5;       /* Brand color */
    --primary-hover: #4338CA;  /* Brand color on hover */
    --bg: #ffffff;             /* Background */
    --text: #1F2937;           /* Text color */
    /* ... more variables available */
}
```

Dark mode is handled automatically via `prefers-color-scheme: dark`.

### FAQ Bot — Suggested Questions

Edit the `SUGGESTED_QUESTIONS` array in `faq-bot/app.js`:

```javascript
const SUGGESTED_QUESTIONS = [
    { icon: "🚀", text: "How do I get started?" },
    { icon: "📄", text: "What file formats are supported?" },
    // Add your own questions here
];
```

## Deployment

These are plain static files. They work anywhere:

- **Local** — Open `index.html` directly in a browser.
- **Vercel** — Drop the template folder and deploy. Zero config.
- **Netlify** — Drag and drop the folder into the Netlify dashboard.
- **GitHub Pages** — Push to a repo and enable Pages.
- **Any static host** — Upload the three files (`index.html`, `styles.css`, `app.js`) to any web server.
- **Embed** — Serve from a subdirectory of your existing site (e.g., `/help/`, `/search/`, `/chat/`).

### CORS

Make sure your Retrieva API allows requests from the domain where the template is hosted. Configure CORS in your API settings if needed.

## API Endpoints Used

| Template        | Endpoint              | Method | Body                                     |
| --------------- | --------------------- | ------ | ---------------------------------------- |
| chatbot-fullpage | `/widget/query`      | POST   | `{ question, widget_id }`               |
| search-portal   | `/widget/search`      | POST   | `{ query, widget_id, top_k }`           |
| faq-bot         | `/widget/query`       | POST   | `{ question, widget_id }`               |

All requests include an `Authorization: Bearer <apiKey>` header.

## File Structure

```
templates/
├── README.md
├── chatbot-fullpage/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── search-portal/
│   ├── index.html
│   ├── styles.css
│   └── app.js
└── faq-bot/
    ├── index.html
    ├── styles.css
    └── app.js
```
