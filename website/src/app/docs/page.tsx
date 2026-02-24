import Link from "next/link";
import {
  Zap,
  Settings,
  Code2,
  Database,
  Terminal,
  Puzzle,
  Globe,
  Server,
} from "lucide-react";

const sections = [
  {
    title: "D\u00e9marrage Rapide",
    desc: "Installez Retrieva en 5 minutes avec Docker",
    icon: Zap,
    href: "/docs/quickstart",
    gradient: "from-amber-500 to-orange-500",
  },
  {
    title: "Configuration",
    desc: "Personnalisez ingestion, retrieval et g\u00e9n\u00e9ration",
    icon: Settings,
    href: "/docs/configuration",
    gradient: "from-blue-500 to-cyan-500",
  },
  {
    title: "API Reference",
    desc: "Endpoints REST, authentification, schemas",
    icon: Code2,
    href: "/docs/api",
    gradient: "from-violet-500 to-purple-500",
  },
  {
    title: "Connecteurs",
    desc: "S3, Google Drive, Confluence, Notion, GitHub...",
    icon: Database,
    href: "/docs/connectors",
    gradient: "from-emerald-500 to-teal-500",
  },
  {
    title: "SDKs",
    desc: "Python et JavaScript pour int\u00e9grer Retrieva",
    icon: Terminal,
    href: "/docs/sdks",
    gradient: "from-pink-500 to-rose-500",
  },
  {
    title: "Plugins",
    desc: "\u00c9tendez Retrieva avec des plugins custom",
    icon: Puzzle,
    href: "/docs/plugins",
    gradient: "from-indigo-500 to-violet-500",
  },
  {
    title: "Widgets",
    desc: "Int\u00e9grez un chatbot ou une recherche sur votre site",
    icon: Globe,
    href: "/docs/widgets",
    gradient: "from-cyan-500 to-blue-500",
  },
  {
    title: "D\u00e9ploiement",
    desc: "Docker, Kubernetes, VPS, Cloud",
    icon: Server,
    href: "/docs/deployment",
    gradient: "from-orange-500 to-red-500",
  },
];

export default function DocsPage() {
  return (
    <div>
      {/* Header */}
      <div className="mb-12">
        <h1 className="text-4xl sm:text-5xl font-extrabold text-white mb-4">
          Documentation{" "}
          <span className="bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">
            Retrieva
          </span>
        </h1>
        <p className="text-lg text-gray-400 max-w-2xl">
          Tout ce qu&apos;il faut pour construire, d&eacute;ployer et scaler votre RAG.
        </p>
      </div>

      {/* Card grid */}
      <div className="grid sm:grid-cols-2 gap-4">
        {sections.map((s) => (
          <Link
            key={s.href}
            href={s.href}
            className="group relative bg-white/[0.02] border border-white/[0.06] rounded-xl p-6 hover:bg-white/[0.05] hover:border-white/10 transition-all duration-300 hover:-translate-y-0.5"
          >
            {/* Hover glow */}
            <div
              className={`absolute -inset-px rounded-xl bg-gradient-to-r ${s.gradient} opacity-0 group-hover:opacity-[0.07] transition-opacity duration-500 blur-sm`}
            />

            <div className="relative flex items-start gap-4">
              <div
                className={`w-10 h-10 rounded-lg bg-gradient-to-br ${s.gradient} flex items-center justify-center shrink-0 shadow-lg opacity-90 group-hover:opacity-100 group-hover:scale-110 transition-all duration-300`}
              >
                <s.icon className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="text-white font-semibold text-base mb-1 group-hover:text-indigo-300 transition-colors">
                  {s.title}
                </h3>
                <p className="text-gray-500 text-sm leading-relaxed">{s.desc}</p>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
