"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  Zap,
  Database,
  Search,
  Globe,
  Puzzle,
  BarChart3,
  Code2,
  Shield,
  Users,
  Github,
  ArrowRight,
  Check,
  Star,
  Terminal,
  FileText,
  MessageSquare,
  ChevronRight,
  Play,
  Layers,
  Upload,
  HelpCircle,
  Rocket,
  ExternalLink,
  Menu,
  X,
} from "lucide-react";

/* ==========================================================================
   Intersection-Observer hook for scroll-triggered animations
   ========================================================================== */

function useInView(options?: IntersectionObserverInit) {
  const ref = useRef<HTMLDivElement>(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true);
          observer.unobserve(el);
        }
      },
      { threshold: 0.15, ...options }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return { ref, inView };
}

/* ==========================================================================
   Animated counter (for GitHub stars placeholder)
   ========================================================================== */

function AnimatedCounter({ target, duration = 2000 }: { target: number; duration?: number }) {
  const [count, setCount] = useState(0);
  const { ref, inView } = useInView();

  useEffect(() => {
    if (!inView) return;
    let start = 0;
    const step = target / (duration / 16);
    const interval = setInterval(() => {
      start += step;
      if (start >= target) {
        setCount(target);
        clearInterval(interval);
      } else {
        setCount(Math.floor(start));
      }
    }, 16);
    return () => clearInterval(interval);
  }, [inView, target, duration]);

  return <span ref={ref}>{count.toLocaleString("fr-FR")}</span>;
}

/* ==========================================================================
   Section wrapper with fade-in animation
   ========================================================================== */

function Section({
  children,
  className = "",
  id,
  dark = false,
}: {
  children: React.ReactNode;
  className?: string;
  id?: string;
  dark?: boolean;
}) {
  const { ref, inView } = useInView();
  return (
    <section
      id={id}
      ref={ref}
      className={`
        relative py-24 md:py-32 transition-all duration-1000
        ${inView ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}
        ${dark ? "bg-gray-950" : "bg-[#0A0A0F]"}
        ${className}
      `}
    >
      {children}
    </section>
  );
}

/* ==========================================================================
   Navbar
   ========================================================================== */

function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handler, { passive: true });
    return () => window.removeEventListener("scroll", handler);
  }, []);

  const links = [
    { label: "Fonctionnalités", href: "#features" },
    { label: "Tarifs", href: "#pricing" },
    { label: "Documentation", href: "#" },
    { label: "GitHub", href: "#open-source" },
  ];

  return (
    <nav
      className={`
        fixed top-0 left-0 right-0 z-50 transition-all duration-300
        ${scrolled ? "bg-gray-950/80 backdrop-blur-xl border-b border-white/5 shadow-2xl" : "bg-transparent"}
      `}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 md:h-20">
          {/* Logo */}
          <a href="#" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/25 group-hover:shadow-indigo-500/40 transition-shadow">
              <Zap className="w-4.5 h-4.5 text-white" strokeWidth={2.5} />
            </div>
            <span className="text-lg font-bold text-white tracking-tight">
              retrieva<span className="text-indigo-400">.ai</span>
            </span>
          </a>

          {/* Desktop links */}
          <div className="hidden md:flex items-center gap-1">
            {links.map((l) => (
              <a
                key={l.label}
                href={l.href}
                className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors rounded-lg hover:bg-white/5"
              >
                {l.label}
              </a>
            ))}
          </div>

          {/* Desktop CTA */}
          <div className="hidden md:flex items-center gap-3">
            <a
              href="#"
              className="text-sm text-gray-400 hover:text-white transition-colors px-4 py-2"
            >
              Connexion
            </a>
            <a
              href="#cta"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-500 transition-all shadow-lg shadow-indigo-600/25 hover:shadow-indigo-500/40 hover:-translate-y-0.5"
            >
              Commencer
              <ArrowRight className="w-3.5 h-3.5" />
            </a>
          </div>

          {/* Mobile menu button */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden p-2 text-gray-400 hover:text-white"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden bg-gray-950/95 backdrop-blur-xl border-b border-white/5">
          <div className="px-4 py-4 space-y-1">
            {links.map((l) => (
              <a
                key={l.label}
                href={l.href}
                onClick={() => setMobileOpen(false)}
                className="block px-4 py-3 text-gray-300 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
              >
                {l.label}
              </a>
            ))}
            <div className="pt-3 border-t border-white/5">
              <a
                href="#cta"
                onClick={() => setMobileOpen(false)}
                className="block w-full text-center px-4 py-3 bg-indigo-600 text-white rounded-lg font-medium"
              >
                Commencer gratuitement
              </a>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}

/* ==========================================================================
   HERO
   ========================================================================== */

function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden bg-[#0A0A0F]">
      {/* Animated gradient orbs */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-[600px] h-[600px] rounded-full bg-indigo-600/20 blur-[128px] animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] rounded-full bg-violet-600/15 blur-[128px] animate-pulse [animation-delay:1s]" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full bg-purple-600/10 blur-[128px] animate-pulse [animation-delay:2s]" />
      </div>

      {/* Grid pattern */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
          backgroundSize: "64px 64px",
        }}
      />

      {/* Radial fade */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_0%,#0A0A0F_70%)]" />

      <div className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center pt-32 pb-20">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-sm text-gray-300 mb-8 backdrop-blur-sm">
          <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          v1.0 est disponible
          <ArrowRight className="w-3.5 h-3.5 text-gray-500" />
        </div>

        {/* Headline */}
        <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-extrabold tracking-tight text-white leading-[1.05] mb-6">
          Le{" "}
          <span className="bg-gradient-to-r from-indigo-400 via-violet-400 to-purple-400 bg-clip-text text-transparent">
            WordPress
          </span>{" "}
          du RAG
        </h1>

        {/* Subheadline */}
        <p className="max-w-2xl mx-auto text-lg sm:text-xl text-gray-400 leading-relaxed mb-10">
          La plateforme open source pour construire, d&eacute;ployer et scaler vos
          applications RAG.{" "}
          <span className="text-white font-medium">En production en 5 minutes.</span>
        </p>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
          <a
            href="#cta"
            className="group inline-flex items-center gap-2.5 px-8 py-4 rounded-full bg-indigo-600 text-white font-semibold text-base hover:bg-indigo-500 transition-all shadow-2xl shadow-indigo-600/25 hover:shadow-indigo-500/40 hover:-translate-y-0.5"
          >
            Commencer gratuitement
            <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
          </a>
          <a
            href="#open-source"
            className="group inline-flex items-center gap-2.5 px-8 py-4 rounded-full border border-white/15 text-white font-semibold text-base hover:bg-white/5 hover:border-white/25 transition-all hover:-translate-y-0.5"
          >
            <Github className="w-5 h-5" />
            Voir sur GitHub
          </a>
        </div>

        {/* Trust badges */}
        <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm text-gray-500">
          {["Open Source", "MIT License", "10+ Connecteurs", "Multi-LLM"].map(
            (badge) => (
              <span key={badge} className="flex items-center gap-2">
                <span className="w-1 h-1 rounded-full bg-indigo-500" />
                {badge}
              </span>
            )
          )}
        </div>

        {/* Hero visual — terminal mockup */}
        <div className="mt-16 sm:mt-20 relative group">
          <div className="absolute -inset-1 bg-gradient-to-r from-indigo-600/20 via-violet-600/20 to-purple-600/20 rounded-2xl blur-xl opacity-50 group-hover:opacity-75 transition-opacity" />
          <div className="relative bg-gray-900/80 backdrop-blur-xl border border-white/10 rounded-xl overflow-hidden shadow-2xl">
            {/* Terminal header */}
            <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5 bg-gray-900/50">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-red-500/70" />
                <div className="w-3 h-3 rounded-full bg-yellow-500/70" />
                <div className="w-3 h-3 rounded-full bg-green-500/70" />
              </div>
              <span className="ml-2 text-xs text-gray-500 font-mono">
                ~ / retrieva
              </span>
            </div>
            <div className="p-5 sm:p-6 text-left font-mono text-sm leading-relaxed">
              <div className="text-gray-500">
                $ docker compose up -d
              </div>
              <div className="text-emerald-400 mt-1.5">
                ✓ retrieva-api &nbsp;&nbsp;&nbsp;Started
              </div>
              <div className="text-emerald-400">
                ✓ retrieva-worker Started
              </div>
              <div className="text-emerald-400">
                ✓ retrieva-dash &nbsp;Started
              </div>
              <div className="mt-3 text-gray-500">
                $ curl localhost:8000/api/v1/health
              </div>
              <div className="text-indigo-400 mt-1.5">
                {`{ "status": "healthy", "version": "1.0.0" }`}
              </div>
              <div className="mt-3 flex items-center gap-2">
                <span className="text-gray-500">$</span>
                <span className="w-2 h-5 bg-indigo-500 animate-pulse" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ==========================================================================
   PROBLEM / SOLUTION
   ========================================================================== */

function ProblemSolution() {
  const items = [
    {
      before: "Des semaines d'int\u00e9gration",
      after: "5 minutes avec Docker",
      icon: Zap,
    },
    {
      before: "Du code spaghetti",
      after: "Une API REST propre",
      icon: Code2,
    },
    {
      before: "Pas de visibilit\u00e9",
      after: "Analytics en temps r\u00e9el",
      icon: BarChart3,
    },
  ];

  return (
    <Section dark id="problem">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-white mb-4">
            Le RAG, c&apos;est compliqu&eacute;.{" "}
            <span className="bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">
              Retrieva, c&apos;est simple.
            </span>
          </h2>
        </div>

        <div className="grid md:grid-cols-3 gap-6 lg:gap-8">
          {items.map((item, i) => (
            <div
              key={i}
              className="group relative bg-white/[0.03] border border-white/[0.06] rounded-2xl p-8 hover:bg-white/[0.05] hover:border-white/10 transition-all duration-500"
            >
              <div className="w-12 h-12 rounded-xl bg-red-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <X className="w-5 h-5 text-red-400" />
              </div>
              <p className="text-gray-400 text-lg line-through decoration-red-400/50 mb-6">
                {item.before}
              </p>

              <div className="h-px bg-gradient-to-r from-transparent via-white/10 to-transparent my-6" />

              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <item.icon className="w-5 h-5 text-emerald-400" />
              </div>
              <p className="text-white text-lg font-semibold">
                {item.after}
              </p>
            </div>
          ))}
        </div>
      </div>
    </Section>
  );
}

/* ==========================================================================
   FEATURES GRID
   ========================================================================== */

function Features() {
  const features = [
    {
      icon: FileText,
      title: "Ingestion Multi-Format",
      desc: "PDF, DOCX, Excel, HTML, Markdown, CSV — ingérez tous vos documents en un clic avec extraction intelligente.",
      gradient: "from-blue-500 to-cyan-500",
    },
    {
      icon: Search,
      title: "Recherche Hybride",
      desc: "Combinez recherche vectorielle, BM25 et reranking pour des résultats ultra-pertinents à chaque requête.",
      gradient: "from-violet-500 to-purple-500",
    },
    {
      icon: Globe,
      title: "10+ Connecteurs",
      desc: "S3, Google Drive, Confluence, Notion, GitHub, Slack — connectez toutes vos sources de données.",
      gradient: "from-emerald-500 to-teal-500",
    },
    {
      icon: BarChart3,
      title: "Dashboard Complet",
      desc: "Analytics, playground, debugger — visualisez et optimisez les performances de votre RAG en temps réel.",
      gradient: "from-orange-500 to-amber-500",
    },
    {
      icon: MessageSquare,
      title: "Widgets Embarquables",
      desc: "Chatbot et recherche intégrables en un seul script. Personnalisables et prêts pour la production.",
      gradient: "from-pink-500 to-rose-500",
    },
    {
      icon: Puzzle,
      title: "Plugin System",
      desc: "20+ plugins disponibles. Créez les vôtres en quelques lignes. Architecture extensible à l'infini.",
      gradient: "from-indigo-500 to-violet-500",
    },
  ];

  return (
    <Section id="features">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <p className="text-indigo-400 font-semibold text-sm tracking-wide uppercase mb-3">
            Fonctionnalit&eacute;s
          </p>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-white mb-4">
            Tout ce dont vous avez besoin
          </h2>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto">
            Une plateforme compl&egrave;te pour g&eacute;rer le cycle de vie complet de vos
            applications RAG.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5 lg:gap-6">
          {features.map((f, i) => (
            <div
              key={i}
              className="group relative bg-white/[0.02] border border-white/[0.06] rounded-2xl p-7 hover:bg-white/[0.04] hover:border-white/10 transition-all duration-500 hover:-translate-y-1"
            >
              {/* Hover glow */}
              <div
                className={`absolute -inset-px rounded-2xl bg-gradient-to-r ${f.gradient} opacity-0 group-hover:opacity-[0.08] transition-opacity duration-500 blur-sm`}
              />

              <div className="relative">
                <div
                  className={`w-11 h-11 rounded-xl bg-gradient-to-br ${f.gradient} flex items-center justify-center mb-5 shadow-lg opacity-90 group-hover:opacity-100 group-hover:scale-110 transition-all duration-300`}
                >
                  <f.icon className="w-5 h-5 text-white" />
                </div>
                <h3 className="text-white font-semibold text-lg mb-2">{f.title}</h3>
                <p className="text-gray-400 text-sm leading-relaxed">{f.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Section>
  );
}

/* ==========================================================================
   HOW IT WORKS
   ========================================================================== */

function HowItWorks() {
  const steps = [
    {
      num: 1,
      title: "Connectez vos donn\u00e9es",
      desc: "Uploadez vos documents ou connectez vos sources de donn\u00e9es via nos 10+ connecteurs.",
      icon: Upload,
    },
    {
      num: 2,
      title: "Posez des questions",
      desc: "Interrogez vos donn\u00e9es via l'API REST, le SDK Python, ou directement depuis le Dashboard.",
      icon: HelpCircle,
    },
    {
      num: 3,
      title: "D\u00e9ployez partout",
      desc: "Widget embarquable, API REST, ou template standalone — d\u00e9ployez comme vous voulez.",
      icon: Rocket,
    },
  ];

  return (
    <Section dark id="how-it-works">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-20">
          <p className="text-indigo-400 font-semibold text-sm tracking-wide uppercase mb-3">
            Comment &ccedil;a marche
          </p>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-white">
            3 &eacute;tapes. 5 minutes.
          </h2>
        </div>

        <div className="relative">
          {/* Connecting line (desktop) */}
          <div className="hidden md:block absolute top-16 left-[16.66%] right-[16.66%] h-px bg-gradient-to-r from-indigo-500/50 via-violet-500/50 to-purple-500/50" />

          <div className="grid md:grid-cols-3 gap-12 md:gap-8">
            {steps.map((s, i) => (
              <div key={i} className="text-center relative">
                {/* Number circle */}
                <div className="relative mx-auto mb-8">
                  <div className="w-32 h-32 rounded-full bg-gradient-to-br from-indigo-500/10 to-violet-500/10 border border-indigo-500/20 flex items-center justify-center mx-auto">
                    <div className="w-20 h-20 rounded-full bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center shadow-xl shadow-indigo-600/25">
                      <s.icon className="w-8 h-8 text-white" />
                    </div>
                  </div>
                  <div className="absolute -top-2 -right-2 w-8 h-8 rounded-full bg-gray-950 border-2 border-indigo-500 flex items-center justify-center">
                    <span className="text-sm font-bold text-indigo-400">{s.num}</span>
                  </div>
                </div>

                <h3 className="text-white font-bold text-xl mb-3">{s.title}</h3>
                <p className="text-gray-400 leading-relaxed max-w-xs mx-auto">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Section>
  );
}

/* ==========================================================================
   CODE EXAMPLE
   ========================================================================== */

function CodeExample() {
  const lines = [
    { text: "# Self-hosted en 5 minutes", type: "comment" },
    { text: "git clone https://github.com/retrieva-ai/retrieva.git", type: "command" },
    { text: "cd retrieva && cp .env.example .env", type: "command" },
    { text: "docker compose up -d", type: "command" },
    { text: "", type: "empty" },
    { text: "# Votre RAG est prêt !", type: "comment" },
    {
      text: 'curl -X POST http://localhost:8000/api/v1/query \\',
      type: "command",
    },
    {
      text: '  -H "Authorization: Bearer rtv_xxx" \\',
      type: "string",
    },
    {
      text: `  -d '{"question": "Comment fonctionne notre produit ?", "collection": "docs"}'`,
      type: "string",
    },
  ];

  return (
    <Section id="code">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <p className="text-indigo-400 font-semibold text-sm tracking-wide uppercase mb-3">
            D&eacute;marrage rapide
          </p>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-white mb-4">
            En production en{" "}
            <span className="bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">
              5 minutes
            </span>
          </h2>
        </div>

        <div className="relative group">
          <div className="absolute -inset-1 bg-gradient-to-r from-indigo-600/20 via-violet-600/20 to-purple-600/20 rounded-2xl blur-xl opacity-50 group-hover:opacity-75 transition-opacity" />
          <div className="relative bg-[#0D1117] border border-white/[0.08] rounded-xl overflow-hidden shadow-2xl">
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-3.5 border-b border-white/5 bg-[#161B22]">
              <div className="flex items-center gap-2.5">
                <Terminal className="w-4 h-4 text-gray-500" />
                <span className="text-xs text-gray-500 font-mono">terminal</span>
              </div>
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-red-500/60" />
                <div className="w-3 h-3 rounded-full bg-yellow-500/60" />
                <div className="w-3 h-3 rounded-full bg-green-500/60" />
              </div>
            </div>

            {/* Code */}
            <div className="p-6 font-mono text-sm leading-7 overflow-x-auto">
              {lines.map((line, i) => (
                <div key={i} className="flex">
                  <span className="w-8 text-right mr-6 text-gray-600 select-none text-xs leading-7">
                    {i + 1}
                  </span>
                  {line.type === "empty" ? (
                    <span>&nbsp;</span>
                  ) : line.type === "comment" ? (
                    <span className="text-gray-500">{line.text}</span>
                  ) : line.type === "command" ? (
                    <span className="text-emerald-400">{line.text}</span>
                  ) : (
                    <span className="text-amber-300">{line.text}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Copy hint */}
        <p className="text-center text-gray-600 text-sm mt-4">
          Copiez, collez, lancez. C&apos;est tout.
        </p>
      </div>
    </Section>
  );
}

/* ==========================================================================
   PRICING
   ========================================================================== */

function Pricing() {
  const plans = [
    {
      name: "Community",
      price: "Gratuit",
      period: "Pour toujours",
      desc: "Self-hosted, pour d\u00e9marrer et exp\u00e9rimenter.",
      cta: "T\u00e9l\u00e9charger",
      popular: false,
      features: [
        "Self-hosted (Docker)",
        "Core features compl\u00e8tes",
        "Ingestion multi-format",
        "Recherche hybride",
        "API REST",
        "Community support",
      ],
    },
    {
      name: "Pro",
      price: "29\u20ac",
      period: "/mois",
      desc: "Cloud manag\u00e9, pour les \u00e9quipes en production.",
      cta: "Essai gratuit 14 jours",
      popular: true,
      features: [
        "Tout Community +",
        "Cloud h\u00e9berg\u00e9 & manag\u00e9",
        "Analytics avanc\u00e9s",
        "Widgets embarquables",
        "Templates personnalisables",
        "\u00c9valuation & m\u00e9triques",
        "Support prioritaire",
      ],
    },
    {
      name: "Enterprise",
      price: "Sur devis",
      period: "",
      desc: "S\u00e9curit\u00e9 et contr\u00f4le pour les grandes organisations.",
      cta: "Nous contacter",
      popular: false,
      features: [
        "Tout Pro +",
        "SSO / SAML",
        "Gestion des utilisateurs",
        "SLA garanti",
        "Support d\u00e9di\u00e9",
        "Custom branding",
        "D\u00e9ploiement on-premise",
      ],
    },
  ];

  return (
    <Section dark id="pricing">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <p className="text-indigo-400 font-semibold text-sm tracking-wide uppercase mb-3">
            Tarifs
          </p>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-white mb-4">
            Simple et transparent
          </h2>
          <p className="text-gray-400 text-lg">
            Commencez gratuitement. Passez au Pro quand vous &ecirc;tes pr&ecirc;t.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6 lg:gap-8 items-start">
          {plans.map((plan, i) => (
            <div
              key={i}
              className={`
                relative rounded-2xl p-8 transition-all duration-500 hover:-translate-y-1
                ${
                  plan.popular
                    ? "bg-gradient-to-b from-indigo-600/10 to-violet-600/5 border-2 border-indigo-500/30 shadow-2xl shadow-indigo-500/10"
                    : "bg-white/[0.02] border border-white/[0.06] hover:border-white/10"
                }
              `}
            >
              {plan.popular && (
                <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                  <span className="px-4 py-1 rounded-full bg-indigo-600 text-white text-xs font-semibold shadow-lg shadow-indigo-600/25">
                    Populaire
                  </span>
                </div>
              )}

              <div className="mb-6">
                <h3 className="text-white font-bold text-xl mb-1">{plan.name}</h3>
                <p className="text-gray-500 text-sm">{plan.desc}</p>
              </div>

              <div className="mb-8">
                <span className="text-4xl font-extrabold text-white">{plan.price}</span>
                <span className="text-gray-500 ml-1">{plan.period}</span>
              </div>

              <a
                href="#cta"
                className={`
                  block w-full text-center py-3 rounded-xl font-semibold text-sm transition-all
                  ${
                    plan.popular
                      ? "bg-indigo-600 text-white hover:bg-indigo-500 shadow-lg shadow-indigo-600/25"
                      : "bg-white/5 text-white border border-white/10 hover:bg-white/10"
                  }
                `}
              >
                {plan.cta}
              </a>

              <ul className="mt-8 space-y-3">
                {plan.features.map((f, j) => (
                  <li key={j} className="flex items-start gap-3 text-sm text-gray-300">
                    <Check className="w-4 h-4 text-indigo-400 mt-0.5 shrink-0" />
                    {f}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </Section>
  );
}

/* ==========================================================================
   OPEN SOURCE
   ========================================================================== */

function OpenSource() {
  return (
    <Section id="open-source">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-sm text-emerald-400 mb-8">
          <Shield className="w-4 h-4" />
          MIT License
        </div>

        <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-white mb-6">
          100% Open Source.{" "}
          <span className="bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">
            Pour toujours.
          </span>
        </h2>

        <p className="text-gray-400 text-lg max-w-xl mx-auto mb-12">
          Retrieva est et restera open source sous licence MIT. Votre RAG, vos donn&eacute;es,
          votre contr&ocirc;le.
        </p>

        {/* Stats */}
        <div className="flex flex-wrap items-center justify-center gap-8 sm:gap-12 mb-12">
          <div className="text-center">
            <div className="flex items-center justify-center gap-2 text-3xl font-bold text-white mb-1">
              <Star className="w-6 h-6 text-yellow-400" />
              <AnimatedCounter target={2847} />
            </div>
            <p className="text-gray-500 text-sm">GitHub Stars</p>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-white mb-1">
              <AnimatedCounter target={500} />+
            </div>
            <p className="text-gray-500 text-sm">D&eacute;veloppeurs</p>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-white mb-1">
              <AnimatedCounter target={120} />+
            </div>
            <p className="text-gray-500 text-sm">Contributors</p>
          </div>
        </div>

        {/* CTA */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <a
            href="#"
            className="group inline-flex items-center gap-2.5 px-8 py-4 rounded-full bg-white/5 border border-white/10 text-white font-semibold hover:bg-white/10 hover:border-white/20 transition-all hover:-translate-y-0.5"
          >
            <Github className="w-5 h-5" />
            Contribuez sur GitHub
            <ExternalLink className="w-4 h-4 text-gray-500 group-hover:text-gray-300 transition-colors" />
          </a>
          <a
            href="#"
            className="inline-flex items-center gap-2.5 px-8 py-4 rounded-full text-gray-400 hover:text-white transition-colors"
          >
            <Users className="w-5 h-5" />
            Rejoignez 500+ d&eacute;veloppeurs
          </a>
        </div>
      </div>
    </Section>
  );
}

/* ==========================================================================
   FINAL CTA
   ========================================================================== */

function FinalCTA() {
  return (
    <Section dark id="cta">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        {/* Glow */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] rounded-full bg-indigo-600/15 blur-[100px]" />
        </div>

        <div className="relative">
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-white mb-6">
            Pr&ecirc;t &agrave; transformer votre{" "}
            <span className="bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">
              RAG
            </span>{" "}
            ?
          </h2>
          <p className="text-gray-400 text-lg mb-10 max-w-xl mx-auto">
            Rejoignez des centaines de d&eacute;veloppeurs qui construisent de meilleures
            applications RAG avec Retrieva.
          </p>

          {/* Email form */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 max-w-md mx-auto mb-6">
            <input
              type="email"
              placeholder="votre@email.com"
              className="w-full sm:flex-1 px-5 py-3.5 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500/50 focus:ring-2 focus:ring-indigo-500/20 transition-all text-sm"
            />
            <button className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-indigo-600 text-white font-semibold text-sm hover:bg-indigo-500 transition-all shadow-lg shadow-indigo-600/25 hover:shadow-indigo-500/40 whitespace-nowrap">
              Commencer
            </button>
          </div>

          <p className="text-gray-600 text-sm">
            Gratuit. Open source. Pas de carte requise.
          </p>
        </div>
      </div>
    </Section>
  );
}

/* ==========================================================================
   FOOTER
   ========================================================================== */

function Footer() {
  const columns = [
    {
      title: "Produit",
      links: ["Features", "Pricing", "Docs", "API"],
    },
    {
      title: "Ressources",
      links: ["Blog", "Guides", "Changelog", "Status"],
    },
    {
      title: "Communaut\u00e9",
      links: ["GitHub", "Discord", "Twitter"],
    },
    {
      title: "L\u00e9gal",
      links: ["Mentions l\u00e9gales", "CGU", "Confidentialit\u00e9"],
    },
  ];

  return (
    <footer className="bg-[#060609] border-t border-white/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-10">
          {/* Brand */}
          <div className="col-span-2 md:col-span-1">
            <a href="#" className="flex items-center gap-2.5 mb-5">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center">
                <Zap className="w-4.5 h-4.5 text-white" strokeWidth={2.5} />
              </div>
              <span className="text-lg font-bold text-white tracking-tight">
                retrieva<span className="text-indigo-400">.ai</span>
              </span>
            </a>
            <p className="text-gray-500 text-sm leading-relaxed">
              La plateforme open source pour le RAG.
            </p>
          </div>

          {/* Link columns */}
          {columns.map((col, i) => (
            <div key={i}>
              <h4 className="text-white font-semibold text-sm mb-4">{col.title}</h4>
              <ul className="space-y-2.5">
                {col.links.map((link, j) => (
                  <li key={j}>
                    <a
                      href="#"
                      className="text-gray-500 hover:text-gray-300 text-sm transition-colors"
                    >
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-16 pt-8 border-t border-white/5 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-gray-600 text-sm">
            &copy; 2025 Retrieva. Open source avec &hearts;
          </p>
          <div className="flex items-center gap-4">
            <a href="#" className="text-gray-600 hover:text-gray-400 transition-colors">
              <Github className="w-5 h-5" />
            </a>
            <a href="#" className="text-gray-600 hover:text-gray-400 transition-colors">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03z" />
              </svg>
            </a>
            <a href="#" className="text-gray-600 hover:text-gray-400 transition-colors">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
              </svg>
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}

/* ==========================================================================
   MAIN PAGE
   ========================================================================== */

export default function LandingPage() {
  /* Smooth scroll for anchor links */
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      const anchor = target.closest("a");
      if (anchor?.hash) {
        const el = document.querySelector(anchor.hash);
        if (el) {
          e.preventDefault();
          el.scrollIntoView({ behavior: "smooth" });
        }
      }
    };
    document.addEventListener("click", handler);
    return () => document.removeEventListener("click", handler);
  }, []);

  return (
    <div className="min-h-screen bg-[#0A0A0F] text-white antialiased selection:bg-indigo-500/30 selection:text-white">
      <Navbar />
      <Hero />
      <ProblemSolution />
      <Features />
      <HowItWorks />
      <CodeExample />
      <Pricing />
      <OpenSource />
      <FinalCTA />
      <Footer />
    </div>
  );
}
