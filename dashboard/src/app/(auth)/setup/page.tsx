"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  Zap,
  Check,
  ChevronRight,
  ChevronLeft,
  Upload,
  FileText,
  CheckCircle2,
  Copy,
  ExternalLink,
  BookOpen,
  Loader2,
  MessageSquare,
  Database,
  XCircle,
  Wifi,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  getSetupStatus,
  initSetup,
  setApiKey,
  testConnection,
  type SetupInitResponse,
  type ConnectionTestResult,
} from "@/lib/api";
import { cn } from "@/lib/utils";

const STEPS = ["Bienvenue", "IA", "Collection", "Contenu", "Termine"];

export default function SetupPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [checking, setChecking] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [setupResult, setSetupResult] = useState<SetupInitResponse | null>(
    null
  );
  const [copied, setCopied] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  // Form state
  const [platformName, setPlatformName] = useState("Retrieva");
  const [adminEmail, setAdminEmail] = useState("");
  const [adminPassword, setAdminPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [embeddingProvider, setEmbeddingProvider] = useState("openai");
  const [embeddingApiKey, setEmbeddingApiKey] = useState("");
  const [generationProvider, setGenerationProvider] = useState("openai");
  const [generationApiKey, setGenerationApiKey] = useState("");
  const [collectionName, setCollectionName] = useState("General");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadDone, setUploadDone] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);
  const [demoInstalled, setDemoInstalled] = useState(false);
  const [testResults, setTestResults] = useState<Record<string, ConnectionTestResult>>({});
  const [testing, setTesting] = useState<Record<string, boolean>>({});

  // Check if setup is needed
  useEffect(() => {
    getSetupStatus()
      .then((s) => {
        if (!s.needs_setup) router.replace("/login");
        else setChecking(false);
      })
      .catch(() => setChecking(false));
  }, [router]);

  // Auto-test infrastructure services when entering step 1
  useEffect(() => {
    if (step !== 1) return;
    const autoTestServices = ["qdrant", "redis", "database"];
    for (const svc of autoTestServices) {
      if (testResults[svc] || testing[svc]) continue;
      setTesting((prev) => ({ ...prev, [svc]: true }));
      testConnection({ service: svc })
        .then((result) => setTestResults((prev) => ({ ...prev, [svc]: result })))
        .catch(() =>
          setTestResults((prev) => ({
            ...prev,
            [svc]: { service: svc, status: "error", latency_ms: 0, message: "Impossible de joindre le service" },
          }))
        )
        .finally(() => setTesting((prev) => ({ ...prev, [svc]: false })));
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step]);

  const runTest = async (service: string, provider?: string, apiKey?: string) => {
    setTesting((prev) => ({ ...prev, [service]: true }));
    try {
      const result = await testConnection({
        service,
        provider,
        api_key: apiKey,
      });
      setTestResults((prev) => ({ ...prev, [service]: result }));
    } catch (err) {
      setTestResults((prev) => ({
        ...prev,
        [service]: {
          service,
          status: "error",
          latency_ms: 0,
          message: err instanceof Error ? err.message : "Test failed",
        },
      }));
    } finally {
      setTesting((prev) => ({ ...prev, [service]: false }));
    }
  };

  // Submit setup between step 2 and 3 (after collection name)
  const handleInitSetup = async () => {
    if (adminPassword !== confirmPassword) {
      setError("Les mots de passe ne correspondent pas");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await initSetup({
        platform_name: platformName,
        admin_email: adminEmail,
        admin_password: adminPassword,
        embedding_provider: embeddingProvider,
        embedding_api_key: embeddingApiKey || undefined,
        generation_provider: generationProvider,
        generation_api_key: generationApiKey || undefined,
        collection_name: collectionName || undefined,
      });
      setApiKey(result.api_key);
      localStorage.setItem(
        "retrieva_user",
        JSON.stringify({
          id: result.user_id,
          email: adminEmail,
          role: "admin",
        })
      );
      setSetupResult(result);
      setStep(3); // Go to upload step
    } catch (err) {
      setError(err instanceof Error ? err.message : "Setup failed");
    } finally {
      setLoading(false);
    }
  };

  const DEMO_DOCUMENTS = [
    {
      title: "Introduction au RAG (Retrieval-Augmented Generation)",
      text: `Le RAG (Retrieval-Augmented Generation) est une technique d'intelligence artificielle qui combine la recherche d'information avec la generation de texte par un modele de langage (LLM).

Comment fonctionne le RAG ?
Le processus RAG se deroule en trois etapes principales :
1. Indexation : Les documents sont decoupes en chunks (fragments) puis convertis en vecteurs numeriques (embeddings) et stockes dans une base de donnees vectorielle.
2. Recherche (Retrieval) : Quand un utilisateur pose une question, celle-ci est egalement convertie en vecteur. Le systeme recherche les chunks les plus similaires dans la base vectorielle.
3. Generation : Les chunks pertinents sont envoyes au LLM comme contexte, avec la question de l'utilisateur. Le modele genere une reponse basee sur ces informations.

Avantages du RAG :
- Reponses basees sur des donnees reelles et a jour
- Reduction des hallucinations du LLM
- Tracabilite : chaque reponse cite ses sources
- Pas besoin de re-entrainer le modele pour de nouvelles donnees
- Controle fin sur les donnees accessibles

Le RAG est particulierement utile pour les bases de connaissances d'entreprise, le support client, la documentation technique et les assistants juridiques.`,
    },
    {
      title: "Guide Retrieva : Premiers pas",
      text: `Retrieva est une plateforme RAG open source modulaire, concue pour etre aussi simple a utiliser que WordPress.

Architecture de Retrieva :
- API FastAPI : Le coeur du systeme, gere l'ingestion, la recherche et la generation
- Base vectorielle Qdrant : Stocke les embeddings pour la recherche semantique
- PostgreSQL : Stocke les metadonnees, utilisateurs, collections et logs
- Celery Workers : Traitent l'ingestion des documents en arriere-plan
- Dashboard Next.js : Interface d'administration complete

Collections :
Les collections sont des espaces de rangement pour vos documents. Vous pouvez creer une collection par projet, par departement ou par theme. Chaque collection a ses propres parametres de recherche.

Ingestion de documents :
Retrieva supporte de nombreux formats : PDF, DOCX, TXT, Markdown, HTML, CSV, XLSX et JSON. Les documents sont automatiquement decoupes en chunks optimises pour la recherche.

Recherche et Requetes :
Utilisez le Playground pour tester vos requetes. Le systeme combine recherche vectorielle et BM25 (recherche par mots-cles) pour des resultats optimaux. Chaque reponse inclut les sources utilisees avec un score de confiance.

Plugins :
Retrieva dispose d'un systeme de plugins extensible. Vous pouvez ajouter de nouveaux connecteurs (Google Drive, Notion, Confluence), des modeles d'embedding personnalises, ou des transformations de documents.`,
    },
    {
      title: "FAQ Retrieva",
      text: `Questions frequemment posees sur Retrieva :

Q: Quels modeles d'embedding sont supportes ?
R: Retrieva supporte OpenAI (text-embedding-3-small/large), Ollama (modeles locaux comme nomic-embed-text), et Cohere (embed-multilingual-v3). Vous pouvez aussi ajouter d'autres fournisseurs via le systeme de plugins.

Q: Comment optimiser la qualite des reponses ?
R: Plusieurs strategies sont possibles :
1. Ajustez la taille des chunks (par defaut 512 tokens) selon votre contenu
2. Activez le reranking pour ameliorer la pertinence des resultats
3. Utilisez des prompts personnalises adaptes a votre domaine
4. Augmentez le nombre de chunks recuperes (top_k) pour plus de contexte

Q: Retrieva peut-il fonctionner entierement en local ?
R: Oui ! En utilisant Ollama pour les embeddings et un LLM local (comme Llama, Mistral ou Phi), Retrieva peut fonctionner sans aucune connexion internet. Ideal pour les donnees sensibles.

Q: Comment securiser l'acces a mes donnees ?
R: Retrieva offre plusieurs niveaux de securite :
- Authentification par cle API avec permissions granulaires
- Gestion des roles (admin, member, viewer)
- Permissions par collection
- Chiffrement des donnees en transit (HTTPS)

Q: Quelle est la taille maximale des documents ?
R: Il n'y a pas de limite stricte. Les documents volumineux sont automatiquement decoupes en chunks. Pour les fichiers tres lourds (>100MB), l'ingestion se fait en arriere-plan via Celery.

Q: Comment integrer Retrieva dans mon application ?
R: Retrieva expose une API REST complete. Utilisez votre cle API dans le header Authorization: Bearer <votre_cle>. Les endpoints principaux sont /api/v1/query (question-reponse) et /api/v1/search (recherche pure).`,
    },
  ];

  const handleInstallDemo = async () => {
    setDemoLoading(true);
    setError(null);
    try {
      const apiKey = setupResult?.api_key;
      const collectionId = setupResult?.collection_id;
      for (const doc of DEMO_DOCUMENTS) {
        const body: Record<string, string> = {
          content: doc.text,
          title: doc.title,
          collection: collectionName || "General",
        };
        const res = await fetch("/api/v1/ingest/text", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${apiKey}`,
          },
          body: JSON.stringify(body),
        });
        if (!res.ok) throw new Error(`Echec de l'ingestion: ${doc.title}`);
      }
      setDemoInstalled(true);
      setStep(4);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Echec de l'installation demo");
    } finally {
      setDemoLoading(false);
    }
  };

  const handleUpload = async () => {
    if (!uploadFile) {
      setStep(4);
      return;
    }
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", uploadFile);
      formData.append("collection", collectionName || "General");
      const res = await fetch("/api/v1/ingest", {
        method: "POST",
        headers: { Authorization: `Bearer ${setupResult?.api_key}` },
        body: formData,
      });
      if (!res.ok) throw new Error("Upload failed");
      setUploadDone(true);
      setStep(4);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const copyApiKey = () => {
    if (setupResult?.api_key) {
      navigator.clipboard.writeText(setupResult.api_key);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const nextStep = () => {
    setError(null);
    if (step === 0) {
      // Validate step 1
      if (!adminEmail || !adminPassword) {
        setError("Email et mot de passe requis");
        return;
      }
      if (adminPassword.length < 8) {
        setError("Le mot de passe doit contenir au moins 8 caracteres");
        return;
      }
      if (adminPassword !== confirmPassword) {
        setError("Les mots de passe ne correspondent pas");
        return;
      }
      setStep(1);
    } else if (step === 1) {
      // Validate step 2
      if (embeddingProvider !== "ollama" && !embeddingApiKey) {
        setError("La cle API embedding est requise pour ce fournisseur");
        return;
      }
      if (generationProvider !== "ollama" && !generationApiKey) {
        // Allow reuse of same key if same provider
        if (embeddingProvider === generationProvider && embeddingApiKey) {
          setGenerationApiKey(embeddingApiKey);
        } else {
          setError("La cle API LLM est requise pour ce fournisseur");
          return;
        }
      }
      setStep(2);
    } else if (step === 2) {
      // Step 3: submit setup
      handleInitSetup();
    } else if (step === 3) {
      // Step 4: handle upload
      handleUpload();
    }
  };

  if (checking) {
    return (
      <div className="flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-brand-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="w-full max-w-2xl">
      {/* Progress bar */}
      <div className="flex items-center justify-between mb-8">
        {STEPS.map((label, i) => (
          <React.Fragment key={label}>
            <div className="flex flex-col items-center gap-1">
              <div
                className={cn(
                  "w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-colors",
                  i < step
                    ? "bg-brand-600 text-white"
                    : i === step
                      ? "bg-brand-600 text-white ring-4 ring-brand-100 dark:ring-brand-900"
                      : "bg-surface-2 text-text-muted"
                )}
              >
                {i < step ? <Check size={18} /> : i + 1}
              </div>
              <span
                className={cn(
                  "text-xs font-medium",
                  i <= step ? "text-brand-600" : "text-text-muted"
                )}
              >
                {label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div
                className={cn(
                  "flex-1 h-0.5 mx-2 mt-[-20px]",
                  i < step ? "bg-brand-600" : "bg-surface-3"
                )}
              />
            )}
          </React.Fragment>
        ))}
      </div>

      <Card>
        <CardContent className="p-8">
          {/* Step 1: Welcome */}
          {step === 0 && (
            <div className="space-y-6">
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-brand-600 text-white mb-4">
                  <Zap size={32} />
                </div>
                <h2 className="text-2xl font-bold text-text-primary">
                  Bienvenue sur Retrieva
                </h2>
                <p className="text-text-secondary mt-2">
                  Configurons votre plateforme RAG en quelques etapes.
                </p>
              </div>
              <div className="space-y-4">
                <Input
                  label="Nom de la plateforme"
                  value={platformName}
                  onChange={(e) => setPlatformName(e.target.value)}
                  placeholder="Retrieva"
                />
                <Input
                  label="Email administrateur"
                  type="email"
                  value={adminEmail}
                  onChange={(e) => setAdminEmail(e.target.value)}
                  placeholder="admin@example.com"
                  required
                />
                <Input
                  label="Mot de passe"
                  type="password"
                  value={adminPassword}
                  onChange={(e) => setAdminPassword(e.target.value)}
                  placeholder="8 caracteres minimum"
                  required
                />
                <Input
                  label="Confirmer le mot de passe"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirmez votre mot de passe"
                  required
                />
              </div>
            </div>
          )}

          {/* Step 2: AI Providers */}
          {step === 1 && (
            <div className="space-y-6">
              <div className="text-center">
                <h2 className="text-2xl font-bold text-text-primary">
                  Fournisseurs IA
                </h2>
                <p className="text-text-secondary mt-2">
                  Choisissez vos moteurs d&apos;embedding et de generation.
                </p>
              </div>

              {/* Embedding provider */}
              <div className="space-y-3">
                <label className="text-sm font-semibold text-text-primary flex items-center gap-2">
                  <Database size={16} /> Embedding (vectorisation des documents)
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {[
                    { id: "openai", label: "OpenAI", desc: "text-embedding-3" },
                    { id: "ollama", label: "Ollama", desc: "Local, gratuit" },
                    { id: "cohere", label: "Cohere", desc: "embed-v3" },
                    { id: "google", label: "Google", desc: "text-embedding" },
                  ].map((opt) => (
                    <button
                      key={opt.id}
                      onClick={() => setEmbeddingProvider(opt.id)}
                      className={cn(
                        "flex flex-col items-center gap-1 p-3 rounded-xl border-2 transition-all text-center",
                        embeddingProvider === opt.id
                          ? "border-brand-600 bg-brand-50 dark:bg-brand-950"
                          : "border-border hover:border-brand-300"
                      )}
                    >
                      <span className="font-semibold text-sm text-text-primary">{opt.label}</span>
                      <span className="text-[11px] text-text-muted">{opt.desc}</span>
                    </button>
                  ))}
                </div>
                {embeddingProvider !== "ollama" && (
                  <Input
                    label={`Cle API ${embeddingProvider === "openai" ? "OpenAI" : embeddingProvider === "cohere" ? "Cohere" : "Google AI"}`}
                    type="password"
                    value={embeddingApiKey}
                    onChange={(e) => setEmbeddingApiKey(e.target.value)}
                    placeholder={embeddingProvider === "google" ? "AIza..." : "sk-..."}
                  />
                )}
                <div className="flex items-center gap-3">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => runTest("embedding", embeddingProvider, embeddingProvider === "ollama" ? undefined : embeddingApiKey)}
                    disabled={testing.embedding || (embeddingProvider !== "ollama" && !embeddingApiKey)}
                  >
                    {testing.embedding ? <Loader2 size={14} className="animate-spin mr-1" /> : <Wifi size={14} className="mr-1" />}
                    Tester la connexion
                  </Button>
                  {testResults.embedding && (
                    <div className={`flex items-center gap-2 text-sm ${testResults.embedding.status === "ok" ? "text-green-600" : "text-red-600"}`}>
                      {testResults.embedding.status === "ok" ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
                      <span>{testResults.embedding.message}</span>
                      {testResults.embedding.latency_ms > 0 && (
                        <span className="text-text-muted">({Math.round(testResults.embedding.latency_ms)}ms)</span>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Divider */}
              <div className="h-px bg-border" />

              {/* Generation provider */}
              <div className="space-y-3">
                <label className="text-sm font-semibold text-text-primary flex items-center gap-2">
                  <MessageSquare size={16} /> LLM (generation des reponses)
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {[
                    { id: "openai", label: "OpenAI", desc: "GPT-4o" },
                    { id: "anthropic", label: "Claude", desc: "Anthropic" },
                    { id: "google", label: "Gemini", desc: "Google" },
                    { id: "ollama", label: "Ollama", desc: "Local, gratuit" },
                  ].map((opt) => (
                    <button
                      key={opt.id}
                      onClick={() => setGenerationProvider(opt.id)}
                      className={cn(
                        "flex flex-col items-center gap-1 p-3 rounded-xl border-2 transition-all text-center",
                        generationProvider === opt.id
                          ? "border-brand-600 bg-brand-50 dark:bg-brand-950"
                          : "border-border hover:border-brand-300"
                      )}
                    >
                      <span className="font-semibold text-sm text-text-primary">{opt.label}</span>
                      <span className="text-[11px] text-text-muted">{opt.desc}</span>
                    </button>
                  ))}
                </div>
                {generationProvider !== "ollama" && (
                  <Input
                    label={`Cle API ${generationProvider === "openai" ? "OpenAI" : generationProvider === "anthropic" ? "Anthropic" : "Google AI"}`}
                    type="password"
                    value={generationApiKey}
                    onChange={(e) => setGenerationApiKey(e.target.value)}
                    placeholder={generationProvider === "anthropic" ? "sk-ant-..." : generationProvider === "google" ? "AIza..." : "sk-..."}
                  />
                )}
                {embeddingProvider === generationProvider && embeddingProvider !== "ollama" && (
                  <p className="text-xs text-text-muted italic">
                    La meme cle API sera utilisee pour l&apos;embedding et la generation.
                  </p>
                )}
                <div className="flex items-center gap-3">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => runTest("generation", generationProvider, generationProvider === "ollama" ? undefined : generationApiKey)}
                    disabled={testing.generation || (generationProvider !== "ollama" && !generationApiKey)}
                  >
                    {testing.generation ? <Loader2 size={14} className="animate-spin mr-1" /> : <Wifi size={14} className="mr-1" />}
                    Tester la connexion
                  </Button>
                  {testResults.generation && (
                    <div className={`flex items-center gap-2 text-sm ${testResults.generation.status === "ok" ? "text-green-600" : "text-red-600"}`}>
                      {testResults.generation.status === "ok" ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
                      <span>{testResults.generation.message}</span>
                      {testResults.generation.latency_ms > 0 && (
                        <span className="text-text-muted">({Math.round(testResults.generation.latency_ms)}ms)</span>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Infrastructure status */}
              <div className="h-px bg-border" />
              <div className="space-y-3">
                <label className="text-sm font-semibold text-text-primary flex items-center gap-2">
                  <Wifi size={16} /> Infrastructure
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {(["qdrant", "redis", "database"] as const).map((svc) => (
                    <div
                      key={svc}
                      className="flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm"
                    >
                      {testing[svc] ? (
                        <Loader2 size={16} className="animate-spin text-text-muted" />
                      ) : testResults[svc]?.status === "ok" ? (
                        <CheckCircle2 size={16} className="text-green-600" />
                      ) : testResults[svc]?.status === "error" ? (
                        <XCircle size={16} className="text-red-600" />
                      ) : (
                        <div className="w-4 h-4 rounded-full bg-surface-3" />
                      )}
                      <span className="font-medium capitalize">
                        {svc === "qdrant" ? "Qdrant" : svc === "redis" ? "Redis" : "Database"}
                      </span>
                      {testResults[svc] && testResults[svc].latency_ms > 0 && (
                        <span className="text-text-muted ml-auto">
                          {Math.round(testResults[svc].latency_ms)}ms
                        </span>
                      )}
                    </div>
                  ))}
                </div>
                {(["qdrant", "redis", "database"] as const).some(
                  (svc) => testResults[svc]?.status === "error"
                ) && (
                  <p className="text-xs text-red-600">
                    {(["qdrant", "redis", "database"] as const)
                      .filter((svc) => testResults[svc]?.status === "error")
                      .map((svc) => `${svc}: ${testResults[svc]?.message}`)
                      .join(" | ")}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Step 3: Collection */}
          {step === 2 && (
            <div className="space-y-6">
              <div className="text-center">
                <h2 className="text-2xl font-bold text-text-primary">
                  Premiere collection
                </h2>
                <p className="text-text-secondary mt-2">
                  Une collection regroupe vos documents par theme.
                </p>
              </div>
              <Input
                label="Nom de la collection"
                value={collectionName}
                onChange={(e) => setCollectionName(e.target.value)}
                placeholder="General"
              />
            </div>
          )}

          {/* Step 4: Content */}
          {step === 3 && (
            <div className="space-y-6">
              <div className="text-center">
                <h2 className="text-2xl font-bold text-text-primary">
                  Contenu initial
                </h2>
                <p className="text-text-secondary mt-2">
                  Choisissez comment demarrer : donnees de demo pour tester
                  immediatement, ou uploadez vos propres documents.
                </p>
              </div>

              {/* Demo data option */}
              <button
                onClick={handleInstallDemo}
                disabled={demoLoading}
                className={cn(
                  "w-full border-2 rounded-xl p-6 text-left transition-all",
                  demoInstalled
                    ? "border-green-500 bg-green-50 dark:bg-green-950"
                    : "border-brand-600 bg-brand-50 dark:bg-brand-950 hover:shadow-md"
                )}
              >
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-lg bg-brand-600 text-white flex items-center justify-center shrink-0">
                    {demoLoading ? (
                      <Loader2 size={24} className="animate-spin" />
                    ) : demoInstalled ? (
                      <Check size={24} />
                    ) : (
                      <BookOpen size={24} />
                    )}
                  </div>
                  <div>
                    <span className="font-semibold text-text-primary text-lg block">
                      {demoInstalled
                        ? "Donnees de demo installees !"
                        : "Installer les donnees de demo"}
                    </span>
                    <span className="text-sm text-text-secondary block mt-1">
                      3 documents sur le RAG et Retrieva. Testez le Playground
                      immediatement avec des questions comme &quot;Comment
                      fonctionne le RAG ?&quot; ou &quot;Quels formats de
                      fichiers sont supportes ?&quot;
                    </span>
                  </div>
                </div>
              </button>

              {/* Divider */}
              <div className="flex items-center gap-3">
                <div className="flex-1 h-px bg-border" />
                <span className="text-xs text-text-muted font-medium">OU</span>
                <div className="flex-1 h-px bg-border" />
              </div>

              {/* Upload option */}
              <div
                onClick={() => fileRef.current?.click()}
                className={cn(
                  "border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors",
                  uploadFile
                    ? "border-brand-600 bg-brand-50 dark:bg-brand-950"
                    : "border-border hover:border-brand-300"
                )}
              >
                <input
                  ref={fileRef}
                  type="file"
                  accept=".pdf,.docx,.txt,.md,.html,.csv,.json,.xlsx"
                  className="hidden"
                  onChange={(e) =>
                    setUploadFile(e.target.files?.[0] || null)
                  }
                />
                {uploadFile ? (
                  <div className="flex flex-col items-center gap-2">
                    <FileText size={32} className="text-brand-600" />
                    <span className="font-medium text-text-primary">
                      {uploadFile.name}
                    </span>
                    <span className="text-xs text-text-muted">
                      {(uploadFile.size / 1024).toFixed(1)} KB
                    </span>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-2">
                    <Upload size={24} className="text-text-muted" />
                    <span className="font-medium text-text-secondary">
                      Uploadez votre propre document
                    </span>
                    <span className="text-xs text-text-muted">
                      PDF, DOCX, TXT, MD, HTML, CSV, XLSX
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Step 5: Done */}
          {step === 4 && (
            <div className="space-y-6">
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 dark:bg-green-900 text-green-600 mb-4">
                  <CheckCircle2 size={40} />
                </div>
                <h2 className="text-2xl font-bold text-text-primary">
                  C&apos;est pret !
                </h2>
                <p className="text-text-secondary mt-2">
                  Votre plateforme Retrieva est configuree.
                  {demoInstalled &&
                    " 3 documents de demo sont en cours d'indexation. Testez le Playground dans quelques secondes !"}
                  {uploadDone &&
                    !demoInstalled &&
                    " Votre document est en cours d'indexation."}
                </p>
              </div>

              {setupResult?.api_key && (
                <div className="space-y-2">
                  <label className="text-sm font-medium text-text-secondary">
                    Votre cle API (sauvegardez-la !)
                  </label>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 bg-surface-2 rounded-lg px-4 py-3 text-sm font-mono text-text-primary break-all">
                      {setupResult.api_key}
                    </code>
                    <Button
                      variant="outline"
                      onClick={copyApiKey}
                      icon={<Copy size={16} />}
                    >
                      {copied ? "Copie !" : "Copier"}
                    </Button>
                  </div>
                </div>
              )}

              <div className="flex flex-col sm:flex-row gap-3 pt-4">
                {demoInstalled ? (
                  <>
                    <Button
                      className="flex-1"
                      onClick={() => router.push("/playground")}
                      icon={<ExternalLink size={16} />}
                    >
                      Tester le Playground
                    </Button>
                    <Button
                      variant="outline"
                      className="flex-1"
                      onClick={() => router.push("/")}
                    >
                      Aller au Dashboard
                    </Button>
                  </>
                ) : (
                  <>
                    <Button
                      className="flex-1"
                      onClick={() => router.push("/")}
                    >
                      Aller au Dashboard
                    </Button>
                    <Button
                      variant="outline"
                      className="flex-1"
                      onClick={() => router.push("/playground")}
                      icon={<ExternalLink size={16} />}
                    >
                      Tester le Playground
                    </Button>
                  </>
                )}
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="mt-4 rounded-lg border border-red-200 bg-red-50 dark:bg-red-950 dark:border-red-800 p-3 text-sm text-red-700 dark:text-red-300">
              {error}
            </div>
          )}

          {/* Navigation buttons */}
          {step < 4 && (
            <div className="flex justify-between mt-8 pt-4 border-t border-border">
              {step > 0 && step < 3 ? (
                <Button
                  variant="ghost"
                  onClick={() => {
                    setStep(step - 1);
                    setError(null);
                  }}
                  icon={<ChevronLeft size={16} />}
                >
                  Retour
                </Button>
              ) : (
                <div />
              )}
              <div className="flex gap-2">
                {step === 3 && !demoInstalled && (
                  <Button variant="ghost" onClick={() => setStep(4)}>
                    Passer
                  </Button>
                )}
                <Button
                  onClick={nextStep}
                  loading={loading || uploading}
                  icon={step < 3 ? <ChevronRight size={16} /> : undefined}
                >
                  {step === 2
                    ? "Creer la plateforme"
                    : step === 3
                      ? demoInstalled
                        ? uploadFile
                          ? "Uploader et continuer"
                          : "Continuer"
                        : uploadFile
                          ? "Uploader"
                          : "Passer"
                      : "Suivant"}
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
