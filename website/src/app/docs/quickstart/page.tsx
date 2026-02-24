"use client";

import React, { useState } from "react";
import { Check, Copy, Terminal, ArrowRight } from "lucide-react";
import Link from "next/link";

function CodeBlock({ code, language = "bash" }: { code: string; language?: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group my-4">
      <div className="bg-[#0D1117] border border-white/[0.08] rounded-lg overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2 border-b border-white/5 bg-[#161B22]">
          <div className="flex items-center gap-2">
            <Terminal className="w-3.5 h-3.5 text-gray-500" />
            <span className="text-xs text-gray-500 font-mono">{language}</span>
          </div>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-300 transition-colors px-2 py-1 rounded hover:bg-white/5"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-400">Copi&eacute;</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" />
                Copier
              </>
            )}
          </button>
        </div>
        <pre className="p-4 overflow-x-auto">
          <code className="text-sm font-mono text-gray-300 leading-relaxed">{code}</code>
        </pre>
      </div>
    </div>
  );
}

function Step({ num, title, children }: { num: number; title: string; children: React.ReactNode }) {
  return (
    <div className="relative pl-12 pb-10 border-l border-white/[0.06] ml-4">
      {/* Step number */}
      <div className="absolute -left-4 top-0 w-8 h-8 rounded-full bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center text-sm font-bold text-white shadow-lg shadow-indigo-600/25">
        {num}
      </div>
      <div className="pt-0.5">
        <h3 className="text-xl font-bold text-white mb-3">{title}</h3>
        <div className="text-gray-400 leading-relaxed space-y-3">{children}</div>
      </div>
    </div>
  );
}

export default function QuickStartPage() {
  return (
    <div>
      {/* Header */}
      <div className="mb-12">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-xs text-amber-400 font-medium mb-4">
          ~5 minutes
        </div>
        <h1 className="text-4xl sm:text-5xl font-extrabold text-white mb-4">
          D&eacute;marrage Rapide
        </h1>
        <p className="text-lg text-gray-400 max-w-2xl">
          Installez Retrieva et lancez votre premier RAG en 5 minutes.
        </p>
      </div>

      {/* Prerequisites */}
      <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-6 mb-10">
        <h2 className="text-white font-semibold text-lg mb-3">Pr&eacute;requis</h2>
        <ul className="space-y-2">
          <li className="flex items-center gap-3 text-gray-400 text-sm">
            <Check className="w-4 h-4 text-emerald-400 shrink-0" />
            <span><strong className="text-white">Docker</strong> &amp; Docker Compose install&eacute;s</span>
          </li>
          <li className="flex items-center gap-3 text-gray-400 text-sm">
            <Check className="w-4 h-4 text-emerald-400 shrink-0" />
            <span><strong className="text-white">Git</strong> install&eacute;</span>
          </li>
          <li className="flex items-center gap-3 text-gray-400 text-sm">
            <Check className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>Une cl&eacute; API <strong className="text-white">OpenAI</strong> (ou autre LLM compatible)</span>
          </li>
        </ul>
      </div>

      {/* Steps */}
      <div className="mb-12">
        <Step num={1} title="Clonez le repository">
          <p>R&eacute;cup&eacute;rez le code source depuis GitHub.</p>
          <CodeBlock code="git clone https://github.com/retrieva-ai/retrieva.git
cd retrieva" />
        </Step>

        <Step num={2} title="Configurez l'environnement">
          <p>Copiez le fichier d&apos;exemple et renseignez votre cl&eacute; API.</p>
          <CodeBlock code="cp .env.example .env" />
          <p>
            Ouvrez le fichier <code className="text-indigo-400 bg-indigo-500/10 px-1.5 py-0.5 rounded text-sm">.env</code> et
            configurez au minimum :
          </p>
          <CodeBlock code={`# .env
OPENAI_API_KEY=sk-...
SECRET_KEY=votre-secret-key
DATABASE_URL=postgresql://retrieva:retrieva@db:5432/retrieva`} language="env" />
        </Step>

        <Step num={3} title="Lancez avec Docker Compose">
          <p>D&eacute;marrez tous les services en une seule commande.</p>
          <CodeBlock code="docker compose up -d" />
          <p>Attendez quelques secondes que les services d&eacute;marrent, puis v&eacute;rifiez :</p>
          <CodeBlock code={`curl http://localhost:8000/api/v1/health
# => { "status": "healthy", "version": "1.0.0" }`} />
        </Step>

        <Step num={4} title="Ouvrez le Dashboard">
          <p>
            Le dashboard est accessible sur{" "}
            <code className="text-indigo-400 bg-indigo-500/10 px-1.5 py-0.5 rounded text-sm">
              http://localhost:3000
            </code>
          </p>
          <p>
            Connectez-vous avec les identifiants par d&eacute;faut d&eacute;finis dans votre{" "}
            <code className="text-indigo-400 bg-indigo-500/10 px-1.5 py-0.5 rounded text-sm">.env</code>.
          </p>
        </Step>

        <Step num={5} title="Uploadez un document">
          <p>Envoyez votre premier document via l&apos;API.</p>
          <CodeBlock code={`curl -X POST http://localhost:8000/api/v1/ingest/file \\
  -H "Authorization: Bearer rtv_xxx" \\
  -F "file=@mon-document.pdf" \\
  -F "collection=docs"`} />
          <p>
            Vous pouvez aussi uploader directement depuis le Dashboard dans la section{" "}
            <strong className="text-white">Documents</strong>.
          </p>
        </Step>

        <Step num={6} title="Interrogez vos donn\u00e9es">
          <p>Posez votre premi&egrave;re question sur vos documents.</p>
          <CodeBlock code={`curl -X POST http://localhost:8000/api/v1/query \\
  -H "Authorization: Bearer rtv_xxx" \\
  -H "Content-Type: application/json" \\
  -d '{
    "question": "Comment fonctionne notre produit ?",
    "collection": "docs"
  }'`} />
          <p>
            Retrieva va automatiquement rechercher les passages pertinents dans vos documents et
            g&eacute;n&eacute;rer une r&eacute;ponse avec citations.
          </p>
        </Step>
      </div>

      {/* Next steps */}
      <div className="bg-gradient-to-r from-indigo-600/10 to-violet-600/5 border border-indigo-500/20 rounded-xl p-6">
        <h2 className="text-white font-bold text-lg mb-4">Et ensuite ?</h2>
        <div className="space-y-3">
          <Link
            href="/docs/api"
            className="flex items-center gap-2 text-indigo-400 hover:text-indigo-300 text-sm transition-colors"
          >
            <ArrowRight className="w-3.5 h-3.5" />
            Explorer l&apos;API Reference compl&egrave;te
          </Link>
          <Link
            href="/docs/connectors"
            className="flex items-center gap-2 text-indigo-400 hover:text-indigo-300 text-sm transition-colors"
          >
            <ArrowRight className="w-3.5 h-3.5" />
            Connecter vos sources de donn&eacute;es (S3, Google Drive, Notion...)
          </Link>
          <Link
            href="/docs/widgets"
            className="flex items-center gap-2 text-indigo-400 hover:text-indigo-300 text-sm transition-colors"
          >
            <ArrowRight className="w-3.5 h-3.5" />
            Int&eacute;grer un widget chatbot sur votre site
          </Link>
          <Link
            href="/docs/deployment"
            className="flex items-center gap-2 text-indigo-400 hover:text-indigo-300 text-sm transition-colors"
          >
            <ArrowRight className="w-3.5 h-3.5" />
            D&eacute;ployer en production (Kubernetes, VPS, Cloud)
          </Link>
        </div>
      </div>
    </div>
  );
}
