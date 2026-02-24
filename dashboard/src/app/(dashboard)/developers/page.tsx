"use client";

import React, { useState, useEffect } from "react";
import {
  Code2,
  Terminal,
  Copy,
  Check,
  ExternalLink,
  Zap,
  Globe,
  FileCode,
  Package,
  Key,
  BookOpen,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { getHealth, type HealthStatus } from "@/lib/api";

type Tab = "quickstart" | "javascript" | "python" | "cli" | "api" | "widgets";

function CodeBlock({ code, language = "bash" }: { code: string; language?: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group">
      <pre className="bg-gray-950 text-gray-100 rounded-lg p-4 text-sm font-mono overflow-x-auto leading-relaxed">
        <code>{code}</code>
      </pre>
      <button
        onClick={handleCopy}
        className="absolute top-3 right-3 p-1.5 rounded-md bg-gray-800 text-gray-400 hover:text-white opacity-0 group-hover:opacity-100 transition-all"
      >
        {copied ? <Check size={14} /> : <Copy size={14} />}
      </button>
    </div>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <h3 className="text-lg font-semibold text-text-primary mt-8 mb-3">{children}</h3>;
}

function EndpointRow({ method, path, desc }: { method: string; path: string; desc: string }) {
  const colors: Record<string, string> = {
    GET: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400",
    POST: "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-400",
    PUT: "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-400",
    DELETE: "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-400",
  };
  return (
    <div className="flex items-center gap-3 py-2.5 border-b border-border last:border-0">
      <span className={`text-xs font-bold px-2 py-0.5 rounded ${colors[method] || ""}`}>
        {method}
      </span>
      <code className="text-sm font-mono text-text-primary">{path}</code>
      <span className="text-sm text-text-muted ml-auto">{desc}</span>
    </div>
  );
}

export default function DevelopersPage() {
  const [activeTab, setActiveTab] = useState<Tab>("quickstart");
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [apiUrl, setApiUrl] = useState("http://localhost:8000");

  useEffect(() => {
    getHealth().then(setHealth).catch(() => {});
    if (typeof window !== "undefined") {
      setApiUrl(window.location.origin);
    }
  }, []);

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: "quickstart", label: "Quick Start", icon: <Zap size={16} /> },
    { id: "javascript", label: "JavaScript", icon: <FileCode size={16} /> },
    { id: "python", label: "Python", icon: <Code2 size={16} /> },
    { id: "cli", label: "CLI", icon: <Terminal size={16} /> },
    { id: "api", label: "API Reference", icon: <BookOpen size={16} /> },
    { id: "widgets", label: "Widgets", icon: <Globe size={16} /> },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Developer Hub</h1>
          <p className="text-sm text-text-secondary mt-1">
            Integrez Retrieva dans votre application en quelques minutes
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-1 border border-border text-sm">
            <div className={`w-2 h-2 rounded-full ${health ? "bg-green-500" : "bg-gray-400"}`} />
            <span className="text-text-secondary">API</span>
            <span className="text-text-primary font-medium">{health ? "v" + health.version : "..."}</span>
          </div>
          <a
            href="/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-sm text-brand-600 hover:underline"
          >
            Swagger <ExternalLink size={12} />
          </a>
        </div>
      </div>

      {/* Status bar */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-50 dark:bg-blue-950 flex items-center justify-center">
              <Package size={20} className="text-blue-600" />
            </div>
            <div>
              <p className="text-xs text-text-muted">SDK JavaScript</p>
              <p className="text-sm font-semibold text-text-primary">npm install retrieva-js</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-green-50 dark:bg-green-950 flex items-center justify-center">
              <Code2 size={20} className="text-green-600" />
            </div>
            <div>
              <p className="text-xs text-text-muted">SDK Python</p>
              <p className="text-sm font-semibold text-text-primary">pip install retrieva</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-50 dark:bg-purple-950 flex items-center justify-center">
              <Terminal size={20} className="text-purple-600" />
            </div>
            <div>
              <p className="text-xs text-text-muted">CLI</p>
              <p className="text-sm font-semibold text-text-primary">npx create-retrieva-app</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <div className="border-b border-border">
        <div className="flex gap-1 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                activeTab === tab.id
                  ? "border-brand-600 text-brand-600"
                  : "border-transparent text-text-secondary hover:text-text-primary"
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      <div className="max-w-4xl">
        {activeTab === "quickstart" && (
          <div className="space-y-6">
            <p className="text-text-secondary">
              Retrieva est une plateforme RAG complete. Vous pouvez l&apos;integrer de 4 facons :
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                {
                  title: "Widget Embed",
                  desc: "Copiez un <script> et collez-le sur votre site. 30 secondes.",
                  time: "30s",
                  target: "widgets" as Tab,
                },
                {
                  title: "Template",
                  desc: "Telechargez un site complet pre-configure. Deployez n'importe ou.",
                  time: "5 min",
                  target: "cli" as Tab,
                },
                {
                  title: "SDK JavaScript",
                  desc: "npm install retrieva-js. Integrez dans React, Vue, Next.js...",
                  time: "10 min",
                  target: "javascript" as Tab,
                },
                {
                  title: "SDK Python",
                  desc: "pip install retrieva. Backend Flask, Django, FastAPI...",
                  time: "10 min",
                  target: "python" as Tab,
                },
              ].map((item) => (
                <button
                  key={item.title}
                  onClick={() => setActiveTab(item.target)}
                  className="text-left p-4 rounded-xl border border-border bg-surface-0 hover:border-brand-400 hover:shadow-md transition-all group"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-text-primary group-hover:text-brand-600 transition-colors">
                      {item.title}
                    </h3>
                    <span className="text-xs text-text-muted bg-surface-2 px-2 py-0.5 rounded-full">
                      {item.time}
                    </span>
                  </div>
                  <p className="text-sm text-text-secondary">{item.desc}</p>
                </button>
              ))}
            </div>

            <SectionTitle>1. Obtenez votre cle API</SectionTitle>
            <p className="text-sm text-text-secondary">
              Allez dans <strong>API Keys</strong> dans le menu pour generer une cle.
              Utilisez une cle <code className="bg-surface-2 px-1.5 py-0.5 rounded text-xs">rtv_pub_</code> pour le frontend
              et <code className="bg-surface-2 px-1.5 py-0.5 rounded text-xs">rtv_</code> pour le backend.
            </p>

            <SectionTitle>2. Premier appel API</SectionTitle>
            <CodeBlock
              language="bash"
              code={`curl -X POST ${apiUrl}/api/v1/query \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"question": "Comment ca marche ?"}'`}
            />

            <SectionTitle>3. Ingestion de documents</SectionTitle>
            <CodeBlock
              language="bash"
              code={`# Upload un PDF
curl -X POST ${apiUrl}/api/v1/ingest \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -F "file=@mon-document.pdf" \\
  -F "collection=ma-collection"

# Ingestion d'une URL
curl -X POST ${apiUrl}/api/v1/ingest/url \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"url": "https://docs.example.com", "collection": "ma-collection"}'`}
            />
          </div>
        )}

        {activeTab === "javascript" && (
          <div className="space-y-6">
            <SectionTitle>Installation</SectionTitle>
            <CodeBlock code="npm install retrieva-js" />

            <SectionTitle>Configuration</SectionTitle>
            <CodeBlock
              language="js"
              code={`import { Retrieva } from 'retrieva-js'

const rag = new Retrieva({
  apiKey: 'rtv_xxx',           // votre cle API
  baseUrl: '${apiUrl}',  // URL de votre instance
})`}
            />

            <SectionTitle>Poser une question (RAG)</SectionTitle>
            <CodeBlock
              language="js"
              code={`const result = await rag.query('Comment configurer le SSO ?', {
  collectionId: 'uuid-collection',
  topK: 5,
  includeSources: true,
})

console.log(result.answer)      // "Pour configurer le SSO..."
console.log(result.confidence)  // 0.92
console.log(result.sources)     // [{content, score, metadata}]`}
            />

            <SectionTitle>Recherche semantique</SectionTitle>
            <CodeBlock
              language="js"
              code={`const hits = await rag.search('guide configuration', { topK: 10 })

hits.results.forEach(hit => {
  console.log(hit.content, hit.score)
})`}
            />

            <SectionTitle>Ingestion de documents</SectionTitle>
            <CodeBlock
              language="js"
              code={`// Fichier (Node.js)
const fs = require('fs')
const buffer = fs.readFileSync('doc.pdf')
await rag.ingest.file(buffer, 'doc.pdf', { collection: 'docs' })

// Texte
await rag.ingest.text('Contenu de mon article...', 'Mon Article', {
  collection: 'docs'
})

// URL
await rag.ingest.url('https://docs.example.com', {
  collection: 'docs',
  crawlDepth: 1
})`}
            />

            <SectionTitle>Collections</SectionTitle>
            <CodeBlock
              language="js"
              code={`// Lister
const collections = await rag.collections.list()

// Creer
const col = await rag.collections.create({
  name: 'documentation',
  description: 'Docs produit'
})

// Supprimer
await rag.collections.delete(col.id)`}
            />

            <SectionTitle>Widget (frontend public)</SectionTitle>
            <CodeBlock
              language="js"
              code={`import { Retrieva } from 'retrieva-js'

// Utilisez une cle publique (rtv_pub_) pour le frontend
const widget = new Retrieva.Widget({
  apiKey: 'rtv_pub_xxx',
  widgetId: 'uuid-widget',
  baseUrl: '${apiUrl}',
})

const answer = await widget.query('Comment ca marche ?')
const results = await widget.search('tarifs')`}
            />
          </div>
        )}

        {activeTab === "python" && (
          <div className="space-y-6">
            <SectionTitle>Installation</SectionTitle>
            <CodeBlock code="pip install retrieva" />

            <SectionTitle>Configuration</SectionTitle>
            <CodeBlock
              language="python"
              code={`from retrieva import Retrieva

rag = Retrieva(
    api_key="rtv_xxx",
    base_url="${apiUrl}",
)`}
            />

            <SectionTitle>Poser une question (RAG)</SectionTitle>
            <CodeBlock
              language="python"
              code={`result = rag.query(
    "Comment configurer le SSO ?",
    collection_id="uuid-collection",
    top_k=5,
)

print(result.answer)      # "Pour configurer le SSO..."
print(result.confidence)  # 0.92
print(result.sources)     # [Source(content=..., score=...)]`}
            />

            <SectionTitle>Recherche semantique</SectionTitle>
            <CodeBlock
              language="python"
              code={`hits = rag.search("guide configuration", top_k=10)

for hit in hits.results:
    print(f"{hit.score:.2f} - {hit.content[:100]}")`}
            />

            <SectionTitle>Ingestion</SectionTitle>
            <CodeBlock
              language="python"
              code={`# Fichier
rag.ingest.file("documents/guide.pdf", collection="docs")

# Texte
rag.ingest.text(
    "Contenu de l'article...",
    title="Mon Article",
    collection="docs",
)

# URL
rag.ingest.url(
    "https://docs.example.com",
    collection="docs",
    crawl_depth=1,
)`}
            />

            <SectionTitle>Client asynchrone</SectionTitle>
            <CodeBlock
              language="python"
              code={`from retrieva import AsyncRetrieva

async_rag = AsyncRetrieva(api_key="rtv_xxx")

result = await async_rag.query("Ma question")
print(result.answer)`}
            />

            <SectionTitle>Widget (frontend)</SectionTitle>
            <CodeBlock
              language="python"
              code={`from retrieva import Widget

widget = Widget(
    api_key="rtv_pub_xxx",
    widget_id="uuid-widget",
)

answer = widget.query("Comment ca marche ?")
print(answer.answer)`}
            />
          </div>
        )}

        {activeTab === "cli" && (
          <div className="space-y-6">
            <SectionTitle>Creer une application RAG</SectionTitle>
            <CodeBlock code="npx create-retrieva-app my-rag-app" />
            <p className="text-sm text-text-secondary">
              L&apos;assistant interactif vous guide : choix du template, cle API, couleurs.
            </p>

            <SectionTitle>Avec options</SectionTitle>
            <CodeBlock
              code={`npx create-retrieva-app my-app \\
  --template chatbot \\
  --api-url ${apiUrl} \\
  --api-key rtv_pub_xxx \\
  --color "#4F46E5"`}
            />

            <SectionTitle>Templates disponibles</SectionTitle>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {[
                { name: "chatbot", desc: "Chatbot pleine page style ChatGPT" },
                { name: "search", desc: "Portail de recherche avec resultats instantanes" },
                { name: "faq", desc: "FAQ interactive avec questions suggerees" },
              ].map((t) => (
                <div
                  key={t.name}
                  className="p-3 rounded-lg border border-border bg-surface-1"
                >
                  <p className="font-mono text-sm text-brand-600 font-semibold">{t.name}</p>
                  <p className="text-xs text-text-muted mt-1">{t.desc}</p>
                </div>
              ))}
            </div>

            <SectionTitle>Deployer</SectionTitle>
            <CodeBlock
              code={`cd my-rag-app
npx serve .

# Ou deployer sur Vercel, Netlify, GitHub Pages...
# C'est du HTML/CSS/JS statique, ca marche partout.`}
            />
          </div>
        )}

        {activeTab === "api" && (
          <div className="space-y-6">
            <div className="flex items-center gap-3 mb-2">
              <Key size={16} className="text-text-muted" />
              <p className="text-sm text-text-secondary">
                Toutes les routes admin necessitent un header{" "}
                <code className="bg-surface-2 px-1.5 py-0.5 rounded text-xs">
                  Authorization: Bearer rtv_xxx
                </code>
              </p>
            </div>

            <SectionTitle>RAG / Recherche</SectionTitle>
            <Card>
              <CardContent className="p-4">
                <EndpointRow method="POST" path="/api/v1/query" desc="Question RAG (retrieval + generation)" />
                <EndpointRow method="POST" path="/api/v1/search" desc="Recherche semantique seule" />
              </CardContent>
            </Card>

            <SectionTitle>Ingestion</SectionTitle>
            <Card>
              <CardContent className="p-4">
                <EndpointRow method="POST" path="/api/v1/ingest" desc="Upload fichier (PDF, DOCX, TXT...)" />
                <EndpointRow method="POST" path="/api/v1/ingest/text" desc="Ingestion de texte brut" />
                <EndpointRow method="POST" path="/api/v1/ingest/url" desc="Ingestion depuis une URL" />
              </CardContent>
            </Card>

            <SectionTitle>Collections</SectionTitle>
            <Card>
              <CardContent className="p-4">
                <EndpointRow method="GET" path="/api/v1/collections" desc="Lister les collections" />
                <EndpointRow method="POST" path="/api/v1/collections" desc="Creer une collection" />
                <EndpointRow method="GET" path="/api/v1/collections/:id" desc="Detail d'une collection" />
                <EndpointRow method="PUT" path="/api/v1/collections/:id" desc="Modifier une collection" />
                <EndpointRow method="DELETE" path="/api/v1/collections/:id" desc="Supprimer une collection" />
              </CardContent>
            </Card>

            <SectionTitle>Documents</SectionTitle>
            <Card>
              <CardContent className="p-4">
                <EndpointRow method="GET" path="/api/v1/documents" desc="Lister les documents" />
                <EndpointRow method="GET" path="/api/v1/documents/:id" desc="Detail d'un document" />
                <EndpointRow method="DELETE" path="/api/v1/documents/:id" desc="Supprimer un document" />
              </CardContent>
            </Card>

            <SectionTitle>Widgets (endpoints publics)</SectionTitle>
            <Card>
              <CardContent className="p-4">
                <EndpointRow method="POST" path="/widget/query" desc="Question RAG (cle publique)" />
                <EndpointRow method="POST" path="/widget/search" desc="Recherche (cle publique)" />
                <EndpointRow method="GET" path="/widget/config/:id" desc="Config widget (sans auth)" />
              </CardContent>
            </Card>

            <SectionTitle>Admin</SectionTitle>
            <Card>
              <CardContent className="p-4">
                <EndpointRow method="GET" path="/api/v1/admin/analytics" desc="Statistiques d'usage" />
                <EndpointRow method="GET" path="/api/v1/admin/settings" desc="Parametres plateforme" />
                <EndpointRow method="PUT" path="/api/v1/admin/settings" desc="Modifier les parametres" />
                <EndpointRow method="GET" path="/api/v1/admin/users" desc="Lister les utilisateurs" />
                <EndpointRow method="POST" path="/api/v1/admin/users" desc="Creer un utilisateur" />
                <EndpointRow method="GET" path="/api/v1/admin/logs" desc="Logs des requetes" />
                <EndpointRow method="GET" path="/api/v1/admin/api-keys" desc="Lister les cles API" />
                <EndpointRow method="POST" path="/api/v1/admin/api-keys" desc="Generer une cle API" />
              </CardContent>
            </Card>

            <div className="mt-6 p-4 rounded-lg bg-brand-50 dark:bg-brand-950 border border-brand-100 dark:border-brand-900">
              <p className="text-sm text-text-primary">
                Documentation interactive complete sur{" "}
                <a
                  href={`${apiUrl}/docs`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-brand-600 font-medium hover:underline"
                >
                  {apiUrl}/docs
                </a>{" "}
                (Swagger UI)
              </p>
            </div>
          </div>
        )}

        {activeTab === "widgets" && (
          <div className="space-y-6">
            <SectionTitle>Embed en 30 secondes</SectionTitle>
            <p className="text-sm text-text-secondary">
              Creez un widget dans la page <strong>Widgets</strong>, puis copiez le snippet :
            </p>
            <CodeBlock
              language="html"
              code={`<!-- Collez dans votre HTML, juste avant </body> -->
<script
  src="${apiUrl}/widget/chatbot.js"
  data-widget-id="VOTRE_WIDGET_ID"
  data-key="rtv_pub_xxx"
  data-api="${apiUrl}">
</script>`}
            />

            <SectionTitle>Widget Search</SectionTitle>
            <CodeBlock
              language="html"
              code={`<script
  src="${apiUrl}/widget/search.js"
  data-widget-id="VOTRE_WIDGET_ID"
  data-key="rtv_pub_xxx"
  data-api="${apiUrl}"
  data-target="#search-results">
</script>

<div id="search-results"></div>`}
            />

            <SectionTitle>Personnalisation</SectionTitle>
            <p className="text-sm text-text-secondary">
              Le widget recupere automatiquement sa config (couleurs, titre, message d&apos;accueil)
              depuis <code className="bg-surface-2 px-1.5 py-0.5 rounded text-xs">/widget/config/:id</code>.
              Modifiez ces parametres dans la page <strong>Widgets &gt; Editer</strong>.
            </p>

            <SectionTitle>CSS custom</SectionTitle>
            <CodeBlock
              language="css"
              code={`/* Ajoutez vos propres styles apres le script */
<style>
  :root {
    --retrieva-primary: #4F46E5;
    --retrieva-primary-hover: #4338CA;
    --retrieva-text: #1F2937;
  }
</style>`}
            />
          </div>
        )}
      </div>
    </div>
  );
}
