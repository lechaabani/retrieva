# create-retrieva-app

Scaffold a Retrieva RAG application in seconds. Zero dependencies.

## Quick Start

```bash
npx create-retrieva-app my-rag-app
```

This launches an interactive wizard that asks for your template choice, API URL, API key, and optional customization.

## Non-Interactive Usage

```bash
npx create-retrieva-app my-rag-app \
  --template chatbot-fullpage \
  --api-url https://api.example.com \
  --api-key rtv_pub_xxx \
  --widget-id wgt_abc123 \
  --color "#2563EB"
```

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--template, -t` | Template name | _(interactive)_ |
| `--api-url` | Retrieva API endpoint | `http://localhost:8000` |
| `--api-key` | Public API key | _(interactive)_ |
| `--widget-id` | Widget ID | _(optional)_ |
| `--color` | Primary brand color (hex) | `#4F46E5` |
| `--help, -h` | Show help | |

## Templates

### Chatbot Full Page (`chatbot-fullpage`)
Full-page chat interface with sidebar, conversation history placeholder, and ChatGPT-style message bubbles.

### Search Portal (`search-portal`)
Semantic search interface with instant results, relevance scoring, filters sidebar, and keyboard navigation.

### FAQ Bot (`faq-bot`)
Interactive FAQ page with suggested questions, expandable answers, source citations, and a custom question form.

## What Gets Created

```
my-rag-app/
  index.html     # Main HTML page
  styles.css     # Themed stylesheet
  app.js         # App logic with your config baked in
  package.json   # With a "serve" script
```

## Running Your App

```bash
cd my-rag-app
npx serve .
```

Then open http://localhost:3000 in your browser.

## Development

To run the CLI locally without publishing:

```bash
node bin/cli.js my-test-app
```
