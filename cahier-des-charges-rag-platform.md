# 📘 Cahier des Charges — RAG Platform

## Le WordPress du RAG

> **Un moteur RAG open-source, généraliste et extensible. Le client branche ses données, consomme l'intelligence comme il veut.**

---

## 1. Vision Produit

### 1.1 Problème

Aujourd'hui, chaque entreprise qui veut intégrer l'IA sur ses propres données doit :

- Choisir un vector store, un modèle d'embedding, un LLM
- Gérer le chunking, le retrieval, le reranking
- Construire un pipeline d'ingestion custom
- Gérer les permissions, la fraîcheur des données, les hallucinations
- Maintenir tout ça dans le temps

**Résultat** : des mois de développement, des compétences rares, des coûts élevés. Seules les grandes entreprises peuvent se le permettre.

### 1.2 Solution

Une **plateforme RAG open-source, plug-and-play**, qui permet à n'importe quelle organisation de :

1. Connecter ses sources de données en quelques clics
2. Indexer automatiquement (chunking, embedding, stockage vectoriel)
3. Consommer l'intelligence via une API universelle (`/query`)
4. Construire ce qu'il veut par-dessus : chatbot, recherche, automation, génération…

### 1.3 Positionnement

| Analogie | CMS | RAG Platform |
|----------|-----|-------------|
| **Core** | Gestion de contenu | Ingestion, indexation, retrieval, génération |
| **Plugins** | WooCommerce, SEO, formulaires | Connecteurs (Notion, SQL, S3, API…) |
| **Thèmes** | Apparence du site | Templates d'usage (chatbot, search, auto-complete…) |
| **Liberté** | Blog, e-commerce, portfolio… | Chatbot, search, automation, génération… |

### 1.4 Cibles

- **Développeurs** : intègrent le RAG via l'API dans leurs apps
- **Entreprises (PME/ETI)** : déploient un chatbot/search interne sans coder
- **Agences/intégrateurs** : utilisent la plateforme pour leurs clients
- **Startups SaaS** : embarquent le moteur RAG dans leur produit

---

## 2. Spécifications Fonctionnelles

### 2.1 Core Engine — Le Moteur RAG

#### 2.1.1 Pipeline d'Ingestion

| Étape | Description | Configurable |
|-------|-------------|-------------|
| **Extract** | Extraction du contenu brut depuis la source | Via connecteurs |
| **Clean** | Nettoyage (HTML, métadonnées inutiles, doublons) | Règles custom |
| **Transform** | Enrichissement (métadonnées, tags, relations) | Transformers custom |
| **Chunk** | Découpage intelligent du contenu | Stratégie configurable |
| **Embed** | Vectorisation des chunks | Modèle configurable |
| **Store** | Stockage dans la base vectorielle | Vector DB configurable |

**Stratégies de chunking supportées :**

- `fixed` — taille fixe (ex: 512 tokens) avec overlap
- `semantic` — découpage par sens (paragraphes, sections)
- `document` — un document = un chunk (pour les petits docs)
- `custom` — le client fournit sa propre logique de découpage

**Ingestion continue :**

- Sync périodique configurable (toutes les X heures)
- Webhooks pour ingestion en temps réel
- Détection de changements (ne ré-indexe que ce qui a changé)
- File d'attente (queue) pour les gros volumes

#### 2.1.2 Moteur de Retrieval

| Composant | Description |
|-----------|-------------|
| **Vector Search** | Recherche sémantique par similarité cosine |
| **Keyword Search** | Recherche full-text classique (BM25) |
| **Hybrid Search** | Combinaison vector + keyword avec pondération configurable |
| **Reranking** | Réordonnancement des résultats par un modèle cross-encoder |
| **Filtres métadonnées** | Filtrage par source, date, tag, permission, type… |
| **Multi-query** | Reformulation automatique de la requête pour élargir le recall |

**Paramètres configurables :**

```yaml
retrieval:
  strategy: hybrid           # vector | keyword | hybrid
  vector_weight: 0.7         # pondération vector vs keyword
  top_k: 10                  # nombre de chunks récupérés
  reranking: true             # activer le reranking
  reranker_model: cross-encoder/ms-marco
  min_relevance_score: 0.5   # seuil minimum de pertinence
```

#### 2.1.3 Moteur de Génération

| Composant | Description |
|-----------|-------------|
| **Context Assembly** | Construction du contexte à partir des chunks récupérés |
| **Prompt Template** | Template configurable avec persona, instructions, format |
| **LLM Call** | Appel au LLM choisi par le client |
| **Citations** | Extraction automatique des sources utilisées dans la réponse |
| **Guardrails** | Détection d'hallucinations, réponses hors-scope |

**LLM supportés :**

- OpenAI (GPT-4o, GPT-4o-mini)
- Anthropic (Claude Sonnet, Claude Haiku)
- Modèles locaux (Ollama, vLLM)
- Tout provider compatible OpenAI API

---

### 2.2 Système de Connecteurs (Plugins)

Chaque connecteur est un module indépendant qui implémente une interface standard :

```
interface Connector {
  name: string
  pull(): Document[]         // Extraire les données
  watch(): EventStream       // Écouter les changements (optionnel)
  testConnection(): boolean  // Vérifier la connexion
}
```

**Connecteurs v1 (MVP) :**

| Connecteur | Type | Priorité |
|-----------|------|---------|
| **File Upload** | Drag & drop PDF, Word, Excel, TXT, MD, CSV | 🔴 Critique |
| **URL Crawler** | Crawl d'un site web ou d'une page | 🔴 Critique |
| **Amazon S3 / GCS** | Bucket de fichiers cloud | 🟡 Important |
| **PostgreSQL / MySQL** | Base de données relationnelle | 🟡 Important |
| **API REST** | Endpoint custom du client | 🟡 Important |
| **Google Drive** | Dossiers et fichiers | 🟢 Souhaitable |
| **Notion** | Pages et bases de données | 🟢 Souhaitable |
| **Confluence** | Espaces et pages | 🟢 Souhaitable |
| **Slack** | Historique de canaux | 🟢 Souhaitable |
| **GitHub** | Repos, issues, wikis | 🟢 Souhaitable |

**Connecteurs communautaires (post-MVP) :**

Le système de plugins permet à la communauté de créer et partager ses propres connecteurs via un registry.

---

### 2.3 API Universelle

L'API est le cœur de la consommation. Le client utilise cette API pour intégrer le RAG où il veut.

#### Endpoints principaux

```
POST   /api/v1/query              # Requête RAG complète (retrieval + génération)
POST   /api/v1/search             # Recherche seule (retrieval sans génération)
POST   /api/v1/ingest             # Ingérer un document à la volée
GET    /api/v1/documents          # Lister les documents indexés
DELETE /api/v1/documents/:id      # Supprimer un document
GET    /api/v1/collections        # Lister les collections
POST   /api/v1/collections        # Créer une collection
GET    /api/v1/health             # Statut du système
```

#### Exemple — Requête `/query`

**Request :**

```json
POST /api/v1/query
{
  "question": "Quels sont les délais de livraison du fournisseur X ?",
  "collection": "docs-fournisseurs",
  "options": {
    "top_k": 5,
    "include_sources": true,
    "language": "fr",
    "max_tokens": 500
  },
  "user_context": {
    "user_id": "adherent_42",
    "role": "adherent"
  }
}
```

**Response :**

```json
{
  "answer": "Selon les conditions générales du fournisseur X, les délais de livraison sont de 48h pour les commandes passées avant 14h, et 72h pour les commandes après 14h.",
  "sources": [
    {
      "document": "CGV_Fournisseur_X_2025.pdf",
      "chunk": "Article 5.2 - Délais de livraison",
      "relevance_score": 0.94,
      "page": 3
    }
  ],
  "confidence": 0.91,
  "tokens_used": 342
}
```

#### Exemple — Requête `/search`

```json
POST /api/v1/search
{
  "query": "politique de retour",
  "collection": "docs-fournisseurs",
  "top_k": 10,
  "filters": {
    "source": "fournisseur_Y",
    "type": "CGV"
  }
}
```

Retourne uniquement les chunks pertinents sans génération LLM — utile pour la recherche, l'auto-complétion, les suggestions.

---

### 2.4 Système de Permissions

| Niveau | Description |
|--------|-------------|
| **Tenant** | Isolation complète entre clients (multi-tenant) |
| **Collection** | Un client peut avoir plusieurs collections (ex: docs RH, docs fournisseurs) |
| **Rôle** | Chaque utilisateur a un rôle qui filtre les documents accessibles |
| **Document** | Métadonnées de permission au niveau du document |

```yaml
permissions:
  roles:
    admin:
      access: "*"
    salarie:
      access: ["docs-internes", "docs-fournisseurs"]
    adherent:
      access: ["docs-fournisseurs"]
      filter_by: "groupe_adherent"
```

---

### 2.5 Dashboard Admin (No-Code)

Interface web pour les utilisateurs non-techniques :

| Fonctionnalité | Description |
|----------------|-------------|
| **Sources** | Ajouter/supprimer/configurer les connecteurs |
| **Documents** | Voir les docs indexés, leur statut, les supprimer |
| **Collections** | Organiser les données en collections thématiques |
| **Playground** | Tester les requêtes en live |
| **Persona** | Configurer le prompt système (ton, instructions, langue) |
| **Analytics** | Voir les requêtes, temps de réponse, taux de confiance |
| **Utilisateurs** | Gérer les rôles et permissions |
| **Clés API** | Générer et révoquer des clés API |
| **Logs** | Historique des requêtes et réponses |
| **Webhooks** | Configurer les callbacks |

---

### 2.6 Templates d'Usage (optionnel, post-MVP)

Des templates prêts à l'emploi pour les cas courants :

| Template | Description |
|----------|-------------|
| **Chatbot Widget** | Widget embed `<script>` à coller sur un site |
| **Search Bar** | Barre de recherche intelligente embeddable |
| **Slack Bot** | Bot Slack qui répond aux questions dans un canal |
| **Email Auto-Reply** | Génération de réponses email basées sur les docs |
| **Doc Generator** | Génération de documents à partir de la base de connaissance |

---

## 3. Spécifications Techniques

### 3.1 Architecture Globale

```
                    ┌──────────────────┐
                    │   Dashboard Web  │
                    │   (React/Next)   │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │   API Gateway    │
                    │  (Auth + Rate    │
                    │   Limiting)      │
                    └────────┬─────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
┌─────────▼──────┐ ┌────────▼────────┐ ┌───────▼────────┐
│  Query Engine  │ │ Ingestion Engine│ │  Admin Engine  │
│  (retrieval +  │ │ (extract, chunk,│ │ (config, users,│
│   generation)  │ │  embed, store)  │ │  analytics)    │
└─────────┬──────┘ └────────┬────────┘ └───────┬────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
┌─────────▼──────┐ ┌────────▼────────┐ ┌───────▼────────┐
│  Vector DB     │ │  PostgreSQL     │ │  Redis/Queue   │
│  (Qdrant ou    │ │  (metadata,     │ │  (jobs, cache, │
│   pgvector)    │ │   config, users)│ │   sessions)    │
└────────────────┘ └─────────────────┘ └────────────────┘
```

### 3.2 Stack Technique

| Couche | Technologie | Justification |
|--------|-------------|--------------|
| **Backend API** | Python (FastAPI) | Écosystème IA riche, performance async |
| **Dashboard** | React + TypeScript (Next.js) | Standard industrie, SSR |
| **Vector DB** | Qdrant (défaut) / pgvector (option) | Qdrant = performance ; pgvector = simplicité |
| **Base relationnelle** | PostgreSQL | Config, métadonnées, utilisateurs, logs |
| **Queue / Cache** | Redis + BullMQ (ou Celery) | Jobs d'ingestion async, cache des embeddings |
| **Embedding** | Configurable (OpenAI, Cohere, sentence-transformers) | Flexibilité client |
| **LLM** | Configurable (OpenAI, Anthropic, Ollama, vLLM) | Agnostique |
| **Conteneurisation** | Docker + Docker Compose | Déploiement universel |
| **Orchestration (cloud)** | Kubernetes | Pour la version managée |
| **CI/CD** | GitHub Actions | Standard open-source |

### 3.3 Structure du Projet

```
rag-platform/
├── docker-compose.yml           # Déploiement one-click
├── config.example.yaml          # Config exemple
├── README.md
│
├── core/                        # Moteur RAG
│   ├── ingestion/
│   │   ├── pipeline.py          # Pipeline d'ingestion principal
│   │   ├── extractors/          # Extraction par type de fichier
│   │   ├── chunkers/            # Stratégies de chunking
│   │   └── embedders/           # Modèles d'embedding
│   │
│   ├── retrieval/
│   │   ├── engine.py            # Moteur de recherche hybride
│   │   ├── reranker.py          # Reranking
│   │   └── filters.py           # Filtres métadonnées/permissions
│   │
│   ├── generation/
│   │   ├── engine.py            # Assemblage contexte + appel LLM
│   │   ├── prompts/             # Templates de prompts
│   │   └── guardrails.py        # Détection hallucinations
│   │
│   └── connectors/              # Système de plugins
│       ├── base.py              # Interface commune
│       ├── file_upload.py
│       ├── url_crawler.py
│       ├── postgres.py
│       ├── s3.py
│       ├── notion.py
│       └── ...
│
├── api/                         # API FastAPI
│   ├── main.py
│   ├── routes/
│   │   ├── query.py             # /query et /search
│   │   ├── ingest.py            # /ingest
│   │   ├── documents.py         # CRUD documents
│   │   ├── collections.py       # CRUD collections
│   │   └── admin.py             # Config, users, analytics
│   ├── auth/                    # Authentification API keys + JWT
│   └── middleware/              # Rate limiting, logging, CORS
│
├── dashboard/                   # Frontend admin (Next.js)
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   └── hooks/
│   └── package.json
│
├── workers/                     # Jobs async
│   ├── ingestion_worker.py      # Traitement des ingestions
│   └── sync_worker.py           # Synchronisation périodique
│
├── plugins/                     # Plugins communautaires
│   └── registry.json
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
└── docs/
    ├── getting-started.md
    ├── configuration.md
    ├── connectors.md
    ├── api-reference.md
    └── deployment.md
```

### 3.4 Modèle de Données

```sql
-- Tenants (multi-tenant)
CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    slug VARCHAR(100) UNIQUE,
    config JSONB,                -- config.yaml en JSON
    created_at TIMESTAMP
);

-- Collections
CREATE TABLE collections (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    name VARCHAR(255),
    description TEXT,
    config JSONB,                -- config spécifique collection
    created_at TIMESTAMP
);

-- Documents
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    collection_id UUID REFERENCES collections(id),
    source_connector VARCHAR(100),
    source_id VARCHAR(500),       -- ID unique dans la source
    title VARCHAR(500),
    content_hash VARCHAR(64),     -- Pour détecter les changements
    metadata JSONB,               -- Tags, permissions, type…
    status VARCHAR(20),           -- pending | processing | indexed | error
    chunks_count INTEGER,
    indexed_at TIMESTAMP,
    created_at TIMESTAMP
);

-- Chunks (métadonnées, les vecteurs sont dans le vector DB)
CREATE TABLE chunks (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    collection_id UUID REFERENCES collections(id),
    content TEXT,
    position INTEGER,
    metadata JSONB,
    vector_id VARCHAR(255),       -- Référence dans le vector DB
    created_at TIMESTAMP
);

-- API Keys
CREATE TABLE api_keys (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    key_hash VARCHAR(64),
    name VARCHAR(255),
    permissions JSONB,
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP
);

-- Query Logs (analytics)
CREATE TABLE query_logs (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    collection_id UUID,
    question TEXT,
    answer TEXT,
    sources JSONB,
    confidence FLOAT,
    tokens_used INTEGER,
    latency_ms INTEGER,
    user_context JSONB,
    created_at TIMESTAMP
);

-- Users (dashboard)
CREATE TABLE users (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    email VARCHAR(255),
    role VARCHAR(50),
    created_at TIMESTAMP
);
```

### 3.5 Configuration Client

Chaque client configure sa plateforme via un fichier `config.yaml` ou via le dashboard :

```yaml
# config.yaml — Exemple complet

platform:
  name: "Mon Entreprise"
  language: "fr"

# Sources de données
sources:
  - name: "Documents fournisseurs"
    connector: file_upload
    path: /data/fournisseurs/

  - name: "Base produits"
    connector: postgres
    connection_string: ${DATABASE_URL}
    query: "SELECT * FROM products WHERE active = true"
    sync_interval: "6h"

  - name: "Site web"
    connector: url_crawler
    url: "https://mon-site.com/docs"
    depth: 3
    sync_interval: "24h"

# Ingestion
ingestion:
  chunking:
    strategy: semantic        # fixed | semantic | document | custom
    max_chunk_size: 512
    overlap: 50
  embedding:
    provider: openai
    model: text-embedding-3-small
    # Alternative local :
    # provider: local
    # model: sentence-transformers/all-MiniLM-L6-v2

# Retrieval
retrieval:
  strategy: hybrid
  vector_weight: 0.7
  top_k: 10
  reranking: true
  reranker_model: cross-encoder/ms-marco-MiniLM-L-6-v2

# Génération
generation:
  provider: openai             # openai | anthropic | ollama | custom
  model: gpt-4o-mini
  # Alternative Anthropic :
  # provider: anthropic
  # model: claude-sonnet-4-5-20250929
  persona: |
    Tu es l'assistant intelligent de Mon Entreprise.
    Tu réponds aux questions en te basant uniquement sur les documents fournis.
    Tu cites toujours tes sources.
    Si tu ne trouves pas la réponse, dis-le clairement.
  max_tokens: 1000
  temperature: 0.1

# Permissions
permissions:
  enabled: true
  roles:
    admin:
      access: "*"
    manager:
      access: ["docs-fournisseurs", "base-produits"]
    employe:
      access: ["base-produits"]

# Vector DB
vector_db:
  provider: qdrant             # qdrant | pgvector
  url: http://qdrant:6333

# Monitoring
analytics:
  enabled: true
  log_queries: true
  log_answers: true
```

---

## 4. Expérience Utilisateur

### 4.1 Parcours Développeur (Self-Hosted)

```
Étape 1 — Clone
$ git clone https://github.com/ton-org/rag-platform.git
$ cd rag-platform

Étape 2 — Configure
$ cp config.example.yaml config.yaml
$ nano config.yaml        # Le dev configure ses sources et son LLM

Étape 3 — Lance
$ docker-compose up -d

Étape 4 — Utilise
$ curl -X POST http://localhost:8000/api/v1/query \
    -H "Authorization: Bearer sk-..." \
    -d '{"question": "Quel est le délai de livraison ?"}'

→ Réponse en 2-3 secondes avec sources
```

**Temps d'installation cible : < 15 minutes.**

### 4.2 Parcours Non-Technique (Cloud)

```
Étape 1 — Inscription sur la plateforme cloud
Étape 2 — Drag & drop des documents (PDF, Word, Excel…)
Étape 3 — Choix du persona ("Tu es l'assistant de…")
Étape 4 — Test dans le playground
Étape 5 — Copier le widget embed ou la clé API
```

**Temps de mise en production cible : < 30 minutes.**

---

## 5. Roadmap

### Phase 1 — MVP (Mois 1-3)

| Feature | Priorité |
|---------|---------|
| Pipeline d'ingestion (extract, chunk, embed, store) | 🔴 Critique |
| Connecteur File Upload (PDF, Word, Excel, TXT, MD) | 🔴 Critique |
| Connecteur URL Crawler | 🔴 Critique |
| Vector DB (Qdrant) | 🔴 Critique |
| Moteur retrieval hybride (vector + keyword) | 🔴 Critique |
| API `/query` et `/search` | 🔴 Critique |
| Support LLM OpenAI + Anthropic | 🔴 Critique |
| Configuration via `config.yaml` | 🔴 Critique |
| Docker Compose one-click | 🔴 Critique |
| Authentification API keys | 🔴 Critique |
| Documentation Getting Started | 🔴 Critique |

**Livrable** : un repo GitHub fonctionnel, installable en 15 min, qui répond à des questions sur des documents uploadés.

### Phase 2 — Dashboard + Connecteurs (Mois 4-6)

| Feature | Priorité |
|---------|---------|
| Dashboard admin (React) | 🟡 Important |
| Playground de test intégré | 🟡 Important |
| Connecteurs S3, PostgreSQL, Google Drive | 🟡 Important |
| Reranking | 🟡 Important |
| Système de permissions/rôles | 🟡 Important |
| Analytics (requêtes, latence, confiance) | 🟡 Important |
| Sync périodique des sources | 🟡 Important |
| Multi-collections | 🟡 Important |

**Livrable** : une plateforme utilisable par des non-développeurs via le dashboard.

### Phase 3 — Scale + Écosystème (Mois 7-12)

| Feature | Priorité |
|---------|---------|
| Version Cloud managée (SaaS) | 🟢 Souhaitable |
| Multi-tenant complet | 🟢 Souhaitable |
| SDK clients (Python, TypeScript, etc.) | 🟢 Souhaitable |
| Système de plugins communautaires | 🟢 Souhaitable |
| Templates d'usage (chatbot widget, Slack bot…) | 🟢 Souhaitable |
| Connecteurs Notion, Confluence, Slack, GitHub | 🟢 Souhaitable |
| Support modèles locaux (Ollama, vLLM) | 🟢 Souhaitable |
| Webhooks et intégrations | 🟢 Souhaitable |
| Guardrails avancés (hallucination detection) | 🟢 Souhaitable |
| Multi-langue avancé | 🟢 Souhaitable |

---

## 6. Modèle Économique

### 6.1 Open-Core

| Offre | Contenu | Prix |
|-------|---------|------|
| **Community** | Core RAG complet, connecteurs de base, API, Docker | **Gratuit (open-source)** |
| **Pro** (self-hosted) | Dashboard, analytics, connecteurs premium, support email | **~49-99€/mois** |
| **Cloud** | Tout hébergé, setup zero, scaling auto | **À l'usage (requêtes + stockage)** |
| **Enterprise** | SSO/SAML, SLA, support dédié, audit logs, déploiement privé | **Sur devis** |

### 6.2 Métriques de Pricing Cloud

- Par requête `/query` : ~0.01-0.05€ selon le LLM
- Par Go de données indexées : ~5-10€/mois
- Par siège utilisateur dashboard : ~10-20€/mois

---

## 7. Métriques de Succès

### 7.1 Métriques Techniques

| Métrique | Cible MVP | Cible v1.0 |
|----------|-----------|-----------|
| Latence `/query` | < 5s | < 3s |
| Latence `/search` | < 500ms | < 200ms |
| Précision retrieval (recall@10) | > 80% | > 90% |
| Uptime | 99% | 99.9% |
| Temps d'installation | < 30 min | < 15 min |
| Documents supportés par instance | 10K | 100K+ |

### 7.2 Métriques Business

| Métrique | Cible 6 mois | Cible 12 mois |
|----------|-------------|--------------|
| GitHub Stars | 1 000 | 5 000 |
| Installations actives | 100 | 500 |
| Clients payants (Pro/Cloud) | 10 | 50 |
| MRR | 5 000€ | 25 000€ |
| Connecteurs communautaires | 5 | 20 |

---

## 8. Risques et Mitigations

| Risque | Impact | Mitigation |
|--------|--------|-----------|
| Concurrence (LangChain, LlamaIndex, Vectara…) | Fort | Différenciation par la simplicité : "en prod en 15 min" |
| Qualité du retrieval insuffisante | Critique | Investir dans le reranking, le chunking sémantique, benchmarks publics |
| Coûts LLM pour les clients | Moyen | Support modèles locaux (Ollama), cache intelligent des réponses |
| Adoption open-source lente | Moyen | Marketing dev (blog, Twitter, demos), documentation exemplaire |
| Sécurité des données clients | Critique | Chiffrement at rest + in transit, isolation multi-tenant, audit |
| Scaling des gros volumes | Moyen | Architecture async, sharding vector DB, ingestion par batch |

---

## 9. Livrables Attendus

| Livrable | Format | Échéance |
|----------|--------|----------|
| Repo GitHub public | Code source | Fin Phase 1 |
| Documentation complète | Markdown (docs/) | Continue |
| Docker Compose fonctionnel | YAML + Dockerfiles | Fin Phase 1 |
| API Reference (OpenAPI/Swagger) | Auto-générée | Fin Phase 1 |
| Dashboard Admin | Application React | Fin Phase 2 |
| Landing page + site docs | Site web | Fin Phase 2 |
| Offre Cloud managée | Infrastructure | Fin Phase 3 |

---

*Document généré le 22 février 2026 — Version 1.0*
