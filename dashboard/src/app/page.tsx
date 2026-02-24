"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Zap,
  Database,
  Search,
  MessageSquare,
  Puzzle,
  Globe,
  Shield,
  BarChart3,
  Code2,
  ArrowRight,
  CheckCircle2,
  ChevronRight,
  FileText,
  Upload,
  Cpu,
  Layers,
  Terminal,
  Moon,
  Sun,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="group relative rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-6 hover:bg-white/10 hover:border-white/20 transition-all duration-300">
      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
        {icon}
      </div>
      <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
      <p className="text-sm text-slate-400 leading-relaxed">{description}</p>
    </div>
  );
}

function StepCard({
  number,
  title,
  description,
}: {
  number: string;
  title: string;
  description: string;
}) {
  return (
    <div className="relative text-center">
      <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center text-white text-2xl font-bold mx-auto mb-4 shadow-lg shadow-indigo-500/25">
        {number}
      </div>
      <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
      <p className="text-sm text-slate-400">{description}</p>
    </div>
  );
}

function PricingCard({
  name,
  price,
  description,
  features,
  highlighted,
  cta,
}: {
  name: string;
  price: string;
  description: string;
  features: string[];
  highlighted?: boolean;
  cta: string;
}) {
  return (
    <div
      className={`relative rounded-2xl p-8 ${
        highlighted
          ? "bg-gradient-to-b from-indigo-600/20 to-purple-600/20 border-2 border-indigo-500/50 shadow-xl shadow-indigo-500/10"
          : "bg-white/5 border border-white/10"
      }`}
    >
      {highlighted && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-gradient-to-r from-indigo-600 to-purple-600 text-xs font-semibold text-white">
          Populaire
        </div>
      )}
      <h3 className="text-xl font-bold text-white">{name}</h3>
      <div className="mt-4 mb-2">
        <span className="text-4xl font-extrabold text-white">{price}</span>
        {price !== "Sur mesure" && (
          <span className="text-slate-400 ml-1">/mois</span>
        )}
      </div>
      <p className="text-sm text-slate-400 mb-6">{description}</p>
      <Link
        href="/register"
        className={`block w-full text-center py-3 rounded-xl font-semibold text-sm transition-all ${
          highlighted
            ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white hover:from-indigo-500 hover:to-purple-500 shadow-lg shadow-indigo-500/25"
            : "bg-white/10 text-white hover:bg-white/20"
        }`}
      >
        {cta}
      </Link>
      <ul className="mt-6 space-y-3">
        {features.map((f, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
            <CheckCircle2 size={16} className="text-indigo-400 shrink-0 mt-0.5" />
            <span>{f}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function LandingPage() {
  const { isAuthenticated, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && isAuthenticated) {
      router.replace("/overview");
    }
  }, [loading, isAuthenticated, router]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950">
        <div className="animate-spin w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-slate-950 text-white overflow-hidden">
      {/* Ambient background */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-[600px] h-[600px] rounded-full bg-indigo-600/8 blur-[128px]" />
        <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] rounded-full bg-purple-600/8 blur-[128px]" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full bg-indigo-500/3 blur-[200px]" />
      </div>

      {/* Navigation */}
      <nav className="relative z-10 border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/25">
              <Zap size={18} className="text-white" />
            </div>
            <span className="text-xl font-bold">Retrieva</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm text-slate-400">
            <a href="#features" className="hover:text-white transition-colors">Fonctionnalites</a>
            <a href="#how-it-works" className="hover:text-white transition-colors">Comment ca marche</a>
            <a href="#pricing" className="hover:text-white transition-colors">Tarifs</a>
            <a href="#developers" className="hover:text-white transition-colors">Developpeurs</a>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="text-sm text-slate-300 hover:text-white transition-colors px-4 py-2"
            >
              Se connecter
            </Link>
            <Link
              href="/register"
              className="text-sm font-semibold bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 px-5 py-2 rounded-lg transition-all shadow-lg shadow-indigo-500/25"
            >
              Commencer gratuitement
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative z-10 pt-24 pb-20">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-sm font-medium mb-8">
            <Zap size={14} />
            Open Source &middot; Self-hosted &middot; Extensible
          </div>
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight leading-[1.1] max-w-4xl mx-auto">
            Le{" "}
            <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              WordPress
            </span>{" "}
            du RAG
          </h1>
          <p className="mt-6 text-lg md:text-xl text-slate-400 max-w-2xl mx-auto leading-relaxed">
            Plateforme RAG modulaire et extensible. Ingerez vos documents, cherchez semantiquement,
            generez des reponses — le tout pilote par un systeme de plugins.
          </p>
          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/register"
              className="group flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 px-8 py-3.5 rounded-xl font-semibold text-base transition-all shadow-xl shadow-indigo-500/25"
            >
              Demarrer gratuitement
              <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
            </Link>
            <a
              href="#features"
              className="flex items-center gap-2 px-8 py-3.5 rounded-xl font-semibold text-base bg-white/5 border border-white/10 hover:bg-white/10 transition-all"
            >
              Decouvrir
              <ChevronRight size={18} />
            </a>
          </div>

          {/* Tech badges */}
          <div className="mt-16 flex flex-wrap items-center justify-center gap-3">
            {[
              "OpenAI", "Anthropic", "Google Gemini", "Ollama", "Cohere",
              "Qdrant", "PostgreSQL", "Redis", "FastAPI", "Next.js",
            ].map((tech) => (
              <span
                key={tech}
                className="px-3 py-1 rounded-lg bg-white/5 border border-white/10 text-xs text-slate-400 font-medium"
              >
                {tech}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Stats bar */}
      <section className="relative z-10 border-y border-white/5 bg-white/[0.02]">
        <div className="max-w-7xl mx-auto px-6 py-12 grid grid-cols-2 md:grid-cols-4 gap-8">
          {[
            { value: "15+", label: "Plugins inclus" },
            { value: "6", label: "Providers IA" },
            { value: "5 min", label: "Setup complet" },
            { value: "100%", label: "Open Source" },
          ].map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-3xl md:text-4xl font-extrabold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                {stat.value}
              </div>
              <div className="text-sm text-slate-400 mt-1">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section id="features" className="relative z-10 py-24">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-extrabold">
              Tout ce qu&apos;il faut pour du RAG en production
            </h2>
            <p className="mt-4 text-lg text-slate-400 max-w-2xl mx-auto">
              Une plateforme complete, du document brut a la reponse generee.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <FeatureCard
              icon={<Upload size={24} className="text-indigo-400" />}
              title="Ingestion multi-sources"
              description="PDF, DOCX, HTML, CSV, API, scraping web. Connecteurs Notion, Google Drive, Confluence."
            />
            <FeatureCard
              icon={<Search size={24} className="text-purple-400" />}
              title="Recherche hybride"
              description="Recherche vectorielle + BM25 keyword avec reranking cross-encoder pour une precision maximale."
            />
            <FeatureCard
              icon={<MessageSquare size={24} className="text-pink-400" />}
              title="Generation augmentee"
              description="Reponses groundees dans vos donnees avec citations et sources. Multi-providers: OpenAI, Anthropic, Gemini, Ollama."
            />
            <FeatureCard
              icon={<Puzzle size={24} className="text-amber-400" />}
              title="Systeme de plugins"
              description="Architecture extensible: embedders, generators, retrievers, chunkers, connectors. Marketplace integre."
            />
            <FeatureCard
              icon={<Globe size={24} className="text-emerald-400" />}
              title="Widgets embarquables"
              description="Chatbot et barre de recherche a integrer sur votre site en un seul script. Personnalisables."
            />
            <FeatureCard
              icon={<Shield size={24} className="text-sky-400" />}
              title="Multi-tenant & RBAC"
              description="Isolation des donnees par tenant, roles admin/member/viewer, cles API publiques et privees."
            />
            <FeatureCard
              icon={<BarChart3 size={24} className="text-orange-400" />}
              title="Analytics & monitoring"
              description="Dashboard temps reel: latence, confiance, tokens, health check de tous les services."
            />
            <FeatureCard
              icon={<Layers size={24} className="text-teal-400" />}
              title="Templates standalone"
              description="Applications RAG pre-construites: chatbot, portail de recherche, FAQ. Telechargez et deployez."
            />
            <FeatureCard
              icon={<Terminal size={24} className="text-violet-400" />}
              title="SDKs & CLI"
              description="SDK JavaScript et Python, CLI scaffolder, API REST complete avec documentation OpenAPI."
            />
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="relative z-10 py-24 border-t border-white/5">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-extrabold">
              Du zero au RAG en 5 minutes
            </h2>
            <p className="mt-4 text-lg text-slate-400 max-w-2xl mx-auto">
              Un assistant de configuration guide chaque etape.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 md:gap-12">
            <StepCard
              number="1"
              title="Installez"
              description="Docker compose up. Un seul fichier. PostgreSQL, Qdrant, Redis inclus."
            />
            <StepCard
              number="2"
              title="Configurez"
              description="Wizard de setup: choisissez vos providers IA, testez les connexions."
            />
            <StepCard
              number="3"
              title="Ingerez"
              description="Upload de documents ou connecteur automatique. Chunking et indexation en background."
            />
            <StepCard
              number="4"
              title="Deployez"
              description="Widget chatbot sur votre site, API pour vos apps, ou template standalone."
            />
          </div>

          {/* Code snippet */}
          <div className="mt-16 max-w-2xl mx-auto">
            <div className="rounded-xl bg-slate-900 border border-white/10 overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-2.5 border-b border-white/10 bg-white/[0.02]">
                <div className="w-3 h-3 rounded-full bg-red-500/60" />
                <div className="w-3 h-3 rounded-full bg-amber-500/60" />
                <div className="w-3 h-3 rounded-full bg-green-500/60" />
                <span className="ml-2 text-xs text-slate-500 font-mono">terminal</span>
              </div>
              <pre className="p-5 text-sm font-mono leading-relaxed overflow-x-auto">
                <code>
                  <span className="text-slate-500"># Installation en une commande</span>{"\n"}
                  <span className="text-emerald-400">$</span>{" "}
                  <span className="text-slate-300">git clone https://github.com/retrieva/retrieva</span>{"\n"}
                  <span className="text-emerald-400">$</span>{" "}
                  <span className="text-slate-300">cd retrieva && docker compose up -d</span>{"\n\n"}
                  <span className="text-slate-500"># Ou via le CLI scaffolder</span>{"\n"}
                  <span className="text-emerald-400">$</span>{" "}
                  <span className="text-slate-300">npx create-retrieva-app my-rag-app</span>{"\n\n"}
                  <span className="text-indigo-400">{">"}</span>{" "}
                  <span className="text-slate-400">Dashboard:  http://localhost:3000</span>{"\n"}
                  <span className="text-indigo-400">{">"}</span>{" "}
                  <span className="text-slate-400">API:        http://localhost:8000/docs</span>{"\n"}
                  <span className="text-indigo-400">{">"}</span>{" "}
                  <span className="text-slate-400">{"Status:     "}
                    <span className="text-emerald-400">All systems operational</span>
                  </span>
                </code>
              </pre>
            </div>
          </div>
        </div>
      </section>

      {/* Developers */}
      <section id="developers" className="relative z-10 py-24 border-t border-white/5">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-extrabold">
              Construit pour les developpeurs
            </h2>
            <p className="mt-4 text-lg text-slate-400 max-w-2xl mx-auto">
              API-first. SDKs natifs. Documentation complete.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="rounded-xl bg-slate-900 border border-white/10 p-6">
              <div className="text-xs text-slate-500 font-mono mb-3">JavaScript / TypeScript</div>
              <pre className="text-sm font-mono text-slate-300 leading-relaxed">
{`import { Retrieva } from
  '@retrieva/sdk';

const client =
  new Retrieva({ apiKey });

const { answer, sources } =
  await client.query({
    question: "...",
    collection: "docs"
  });`}
              </pre>
            </div>
            <div className="rounded-xl bg-slate-900 border border-white/10 p-6">
              <div className="text-xs text-slate-500 font-mono mb-3">Python</div>
              <pre className="text-sm font-mono text-slate-300 leading-relaxed">
{`from retrieva import Retrieva

client = Retrieva(
  api_key=api_key
)

result = client.query(
  question="...",
  collection="docs"
)`}
              </pre>
            </div>
            <div className="rounded-xl bg-slate-900 border border-white/10 p-6">
              <div className="text-xs text-slate-500 font-mono mb-3">cURL</div>
              <pre className="text-sm font-mono text-slate-300 leading-relaxed">
{`curl -X POST \\
  localhost:8000/api/v1/query \\
  -H "Authorization:
    Bearer rtv_..." \\
  -d '{
    "question": "...",
    "collection_id": "..."
  }'`}
              </pre>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="relative z-10 py-24 border-t border-white/5">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-extrabold">
              Tarification simple et transparente
            </h2>
            <p className="mt-4 text-lg text-slate-400 max-w-2xl mx-auto">
              Open source et gratuit. Plans premium pour les entreprises.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            <PricingCard
              name="Community"
              price="0$"
              description="Pour les projets personnels et les petites equipes"
              cta="Commencer gratuitement"
              features={[
                "Toutes les fonctionnalites",
                "Self-hosted illimite",
                "Communaute Discord",
                "3 collections",
                "1 000 documents",
                "Plugins open source",
              ]}
            />
            <PricingCard
              name="Pro"
              price="49$"
              description="Pour les equipes en croissance"
              cta="Essai gratuit 14 jours"
              highlighted
              features={[
                "Tout dans Community",
                "Collections illimitees",
                "Documents illimites",
                "Support prioritaire",
                "SSO / SAML",
                "Audit logs",
                "Webhooks avances",
              ]}
            />
            <PricingCard
              name="Enterprise"
              price="Sur mesure"
              description="Pour les grandes organisations"
              cta="Contacter les ventes"
              features={[
                "Tout dans Pro",
                "SLA garanti 99.9%",
                "Deploiement on-premise",
                "Support dedie",
                "Formation equipe",
                "Personnalisation",
                "Connecteurs custom",
              ]}
            />
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="relative z-10 py-24 border-t border-white/5">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-3xl md:text-5xl font-extrabold leading-tight">
            Pret a construire votre{" "}
            <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
              IA documentaire
            </span>{" "}
            ?
          </h2>
          <p className="mt-6 text-lg text-slate-400 max-w-2xl mx-auto">
            Rejoignez les equipes qui utilisent Retrieva pour transformer leurs documents en intelligence.
          </p>
          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/register"
              className="group flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 px-8 py-4 rounded-xl font-semibold text-lg transition-all shadow-xl shadow-indigo-500/25"
            >
              Creer mon compte gratuitement
              <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/5 bg-white/[0.01]">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center">
                  <Zap size={14} className="text-white" />
                </div>
                <span className="font-bold">Retrieva</span>
              </div>
              <p className="text-sm text-slate-500 leading-relaxed">
                Le WordPress du RAG.<br />
                Open source, modulaire, extensible.
              </p>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-slate-300 mb-3">Produit</h4>
              <ul className="space-y-2 text-sm text-slate-500">
                <li><a href="#features" className="hover:text-slate-300">Fonctionnalites</a></li>
                <li><a href="#pricing" className="hover:text-slate-300">Tarifs</a></li>
                <li><Link href="/login" className="hover:text-slate-300">Dashboard</Link></li>
                <li><a href="#" className="hover:text-slate-300">Changelog</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-slate-300 mb-3">Developpeurs</h4>
              <ul className="space-y-2 text-sm text-slate-500">
                <li><a href="#" className="hover:text-slate-300">Documentation</a></li>
                <li><a href="#" className="hover:text-slate-300">API Reference</a></li>
                <li><a href="#" className="hover:text-slate-300">SDK JavaScript</a></li>
                <li><a href="#" className="hover:text-slate-300">SDK Python</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-slate-300 mb-3">Entreprise</h4>
              <ul className="space-y-2 text-sm text-slate-500">
                <li><a href="#" className="hover:text-slate-300">Contact</a></li>
                <li><a href="#" className="hover:text-slate-300">Support</a></li>
                <li><a href="#" className="hover:text-slate-300">Securite</a></li>
                <li><a href="#" className="hover:text-slate-300">Mentions legales</a></li>
              </ul>
            </div>
          </div>
          <div className="mt-12 pt-8 border-t border-white/5 flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-xs text-slate-600">
              &copy; 2025 Retrieva. Open source sous licence MIT.
            </p>
            <div className="flex items-center gap-4 text-xs text-slate-600">
              <a href="#" className="hover:text-slate-400">GitHub</a>
              <a href="#" className="hover:text-slate-400">Discord</a>
              <a href="#" className="hover:text-slate-400">Twitter</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
