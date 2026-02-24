import { Shield } from "lucide-react";

type Endpoint = {
  method: "GET" | "POST" | "PUT" | "DELETE";
  path: string;
  desc: string;
};

type EndpointGroup = {
  title: string;
  endpoints: Endpoint[];
};

const methodColors: Record<string, string> = {
  GET: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20",
  POST: "bg-blue-500/15 text-blue-400 border-blue-500/20",
  PUT: "bg-amber-500/15 text-amber-400 border-amber-500/20",
  DELETE: "bg-red-500/15 text-red-400 border-red-500/20",
};

const groups: EndpointGroup[] = [
  {
    title: "Query",
    endpoints: [
      { method: "POST", path: "/api/v1/query", desc: "Poser une question sur vos documents avec g\u00e9n\u00e9ration de r\u00e9ponse" },
      { method: "POST", path: "/api/v1/query/debug", desc: "Query avec informations de debug (chunks retourn\u00e9s, scores, latence)" },
      { method: "POST", path: "/api/v1/search", desc: "Recherche vectorielle pure sans g\u00e9n\u00e9ration de r\u00e9ponse" },
    ],
  },
  {
    title: "Ingest",
    endpoints: [
      { method: "POST", path: "/api/v1/ingest/file", desc: "Ing\u00e9rer un fichier (PDF, DOCX, Excel, CSV, HTML, Markdown)" },
      { method: "POST", path: "/api/v1/ingest/url", desc: "Ing\u00e9rer le contenu d\u2019une URL (scraping + extraction)" },
      { method: "POST", path: "/api/v1/ingest/text", desc: "Ing\u00e9rer du texte brut directement" },
    ],
  },
  {
    title: "Documents",
    endpoints: [
      { method: "GET", path: "/api/v1/documents", desc: "Lister tous les documents avec pagination et filtres" },
      { method: "GET", path: "/api/v1/documents/{id}", desc: "D\u00e9tails d\u2019un document (m\u00e9tadonn\u00e9es, statut, nombre de chunks)" },
      { method: "GET", path: "/api/v1/documents/{id}/chunks", desc: "Lister les chunks d\u2019un document" },
      { method: "DELETE", path: "/api/v1/documents/{id}", desc: "Supprimer un document et tous ses chunks" },
    ],
  },
  {
    title: "Collections",
    endpoints: [
      { method: "GET", path: "/api/v1/collections", desc: "Lister toutes les collections" },
      { method: "POST", path: "/api/v1/collections", desc: "Cr\u00e9er une nouvelle collection" },
      { method: "PUT", path: "/api/v1/collections/{id}", desc: "Modifier une collection (nom, description, settings)" },
      { method: "DELETE", path: "/api/v1/collections/{id}", desc: "Supprimer une collection et tous ses documents" },
      { method: "POST", path: "/api/v1/collections/compare", desc: "Comparer les performances entre deux collections" },
    ],
  },
  {
    title: "Sources",
    endpoints: [
      { method: "GET", path: "/api/v1/sources", desc: "Lister les sources de donn\u00e9es configur\u00e9es" },
      { method: "POST", path: "/api/v1/sources", desc: "Ajouter une nouvelle source (S3, Google Drive, etc.)" },
      { method: "POST", path: "/api/v1/sources/{id}/sync", desc: "D\u00e9clencher la synchronisation d\u2019une source" },
    ],
  },
  {
    title: "Widgets",
    endpoints: [
      { method: "GET", path: "/api/v1/admin/widgets", desc: "Lister les widgets configur\u00e9s" },
      { method: "POST", path: "/api/v1/admin/widgets", desc: "Cr\u00e9er un nouveau widget (chatbot ou recherche)" },
      { method: "POST", path: "/api/v1/widgets/{token}/query", desc: "Endpoint public du widget (pas d\u2019auth requise)" },
      { method: "GET", path: "/api/v1/widgets/{token}/config", desc: "Configuration publique du widget" },
    ],
  },
  {
    title: "Admin",
    endpoints: [
      { method: "GET", path: "/api/v1/admin/users", desc: "Lister les utilisateurs (admin uniquement)" },
      { method: "POST", path: "/api/v1/admin/api-keys", desc: "G\u00e9n\u00e9rer une nouvelle cl\u00e9 API" },
      { method: "GET", path: "/api/v1/admin/plugins", desc: "Lister les plugins install\u00e9s" },
      { method: "GET", path: "/api/v1/admin/settings", desc: "R\u00e9cup\u00e9rer la configuration globale" },
    ],
  },
  {
    title: "Analytics",
    endpoints: [
      { method: "GET", path: "/api/v1/analytics/dashboard", desc: "M\u00e9triques du dashboard (requ\u00eates, latence, satisfaction)" },
      { method: "GET", path: "/api/v1/activity/recent", desc: "Activit\u00e9 r\u00e9cente (queries, ingestions, erreurs)" },
      { method: "GET", path: "/api/v1/suggestions", desc: "Suggestions d\u2019am\u00e9lioration bas\u00e9es sur l\u2019usage" },
    ],
  },
];

export default function ApiReferencePage() {
  return (
    <div>
      {/* Header */}
      <div className="mb-12">
        <h1 className="text-4xl sm:text-5xl font-extrabold text-white mb-4">
          API Reference
        </h1>
        <p className="text-lg text-gray-400 max-w-2xl">
          Tous les endpoints REST de Retrieva, organis&eacute;s par cat&eacute;gorie.
        </p>
      </div>

      {/* Authentication */}
      <div className="bg-gradient-to-r from-indigo-600/10 to-violet-600/5 border border-indigo-500/20 rounded-xl p-6 mb-10">
        <div className="flex items-start gap-3">
          <Shield className="w-5 h-5 text-indigo-400 mt-0.5 shrink-0" />
          <div>
            <h2 className="text-white font-bold text-lg mb-2">Authentification</h2>
            <p className="text-gray-400 text-sm mb-3">
              Toutes les requ&ecirc;tes n&eacute;cessitent un header d&apos;authentification (sauf les endpoints publics des widgets).
            </p>
            <div className="bg-[#0D1117] border border-white/[0.08] rounded-lg px-4 py-3 font-mono text-sm">
              <span className="text-gray-500">Authorization:</span>{" "}
              <span className="text-amber-300">Bearer rtv_xxx</span>
            </div>
            <p className="text-gray-500 text-xs mt-2">
              G&eacute;n&eacute;rez vos cl&eacute;s API depuis le Dashboard ou via POST /api/v1/admin/api-keys.
            </p>
          </div>
        </div>
      </div>

      {/* Base URL */}
      <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-6 mb-10">
        <h3 className="text-white font-semibold mb-2">Base URL</h3>
        <div className="bg-[#0D1117] border border-white/[0.08] rounded-lg px-4 py-3 font-mono text-sm text-emerald-400">
          http://localhost:8000
        </div>
        <p className="text-gray-500 text-xs mt-2">
          Adaptez l&apos;URL selon votre d&eacute;ploiement (ex: https://api.votre-domaine.com).
        </p>
      </div>

      {/* Endpoint groups */}
      <div className="space-y-10">
        {groups.map((group) => (
          <div key={group.title}>
            <h2 className="text-2xl font-bold text-white mb-5 pb-2 border-b border-white/[0.06]">
              {group.title}
            </h2>
            <div className="space-y-3">
              {group.endpoints.map((ep) => (
                <div
                  key={`${ep.method}-${ep.path}`}
                  className="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4 bg-white/[0.02] border border-white/[0.06] rounded-lg px-4 py-3 hover:bg-white/[0.04] hover:border-white/10 transition-all"
                >
                  <span
                    className={`inline-flex items-center justify-center px-2.5 py-0.5 rounded text-xs font-bold border w-16 shrink-0 ${methodColors[ep.method]}`}
                  >
                    {ep.method}
                  </span>
                  <code className="text-sm font-mono text-indigo-300 shrink-0">
                    {ep.path}
                  </code>
                  <span className="text-gray-500 text-sm sm:ml-auto sm:text-right">
                    {ep.desc}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
