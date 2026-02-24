const BASE_URL = "/api/v1";

export function getApiKey(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("retrieva_api_key");
}

export function setApiKey(key: string): void {
  localStorage.setItem("retrieva_api_key", key);
}

export function clearApiKey(): void {
  localStorage.removeItem("retrieva_api_key");
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
}

class ApiError extends Error {
  status: number;
  details: unknown;

  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

async function request<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { method = "GET", body, headers = {} } = options;
  const apiKey = getApiKey();

  const config: RequestInit = {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}),
      ...headers,
    },
  };

  if (body && method !== "GET") {
    config.body = JSON.stringify(body);
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, config);

  if (!response.ok) {
    let details: unknown;
    try {
      details = await response.json();
    } catch {
      details = await response.text();
    }
    throw new ApiError(
      `API Error: ${response.status} ${response.statusText}`,
      response.status,
      details
    );
  }

  if (response.status === 204) return undefined as T;
  return response.json();
}

async function requestMultipart<T>(
  endpoint: string,
  formData: FormData
): Promise<T> {
  const apiKey = getApiKey();
  const config: RequestInit = {
    method: "POST",
    headers: apiKey ? { Authorization: `Bearer ${apiKey}` } : {},
    body: formData,
  };

  const response = await fetch(`${BASE_URL}${endpoint}`, config);

  if (!response.ok) {
    let details: unknown;
    try {
      details = await response.json();
    } catch {
      details = await response.text();
    }
    throw new ApiError(
      `API Error: ${response.status} ${response.statusText}`,
      response.status,
      details
    );
  }

  return response.json();
}

// ---- Query / Search ----

export interface QueryRequest {
  question: string;
  collection_id?: string;
  top_k?: number;
  include_sources?: boolean;
  language?: string;
}

export interface Source {
  document_id: string;
  chunk_id: string;
  content: string;
  score: number;
  metadata?: Record<string, unknown>;
}

export interface QueryResponse {
  answer: string;
  sources: Source[];
  confidence: number;
  latency_ms: number;
  tokens_used?: number;
}

export interface SearchResponse {
  results: Source[];
  latency_ms: number;
}

export function query(req: QueryRequest): Promise<QueryResponse> {
  return request("/query", { method: "POST", body: req });
}

export function search(req: QueryRequest): Promise<SearchResponse> {
  return request("/search", { method: "POST", body: req });
}

// ---- Query Debug ----

export interface DebugChunk {
  content: string;
  score: number;
  doc_id: string;
}

export interface DebugStep {
  name: string;
  label: string;
  duration_ms: number;
  details: Record<string, unknown>;
  chunks?: DebugChunk[];
}

export interface DebugQueryResponse {
  answer: string;
  confidence: number;
  total_latency_ms: number;
  steps: DebugStep[];
  sources: Source[];
}

export function queryDebug(params: {
  question: string;
  collection: string;
  options?: {
    top_k?: number;
    include_sources?: boolean;
    language?: string;
    max_tokens?: number;
  };
}): Promise<DebugQueryResponse> {
  return request("/query/debug", { method: "POST", body: params });
}

// ---- Ingest ----

export interface IngestResponse {
  document_id: string;
  chunks: number;
  status: string;
}

export function uploadDocument(
  file: File,
  collection?: string
): Promise<IngestResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (collection) formData.append("collection", collection);
  return requestMultipart("/ingest", formData);
}

export function ingestText(
  text: string,
  title: string,
  collection?: string
): Promise<IngestResponse> {
  return request("/ingest/text", {
    method: "POST",
    body: { content: text, title, collection },
  });
}

export function ingestUrl(
  url: string,
  collection?: string
): Promise<IngestResponse> {
  return request("/ingest/url", {
    method: "POST",
    body: { url, collection },
  });
}

// ---- Collections ----

export interface Collection {
  id: string;
  tenant_id: string;
  name: string;
  description: string | null;
  config: Record<string, unknown>;
  created_at: string;
  documents_count: number;
  chunks_count: number;
}

export interface CollectionsResponse {
  collections: Collection[];
  total: number;
  page: number;
  per_page: number;
}

export function getCollections(): Promise<Collection[]> {
  return request<CollectionsResponse>("/collections?per_page=100").then(
    (r) => r.collections
  );
}

export function getCollection(id: string): Promise<Collection> {
  return request(`/collections/${id}`);
}

export function createCollection(data: {
  name: string;
  description?: string;
}): Promise<Collection> {
  return request("/collections", { method: "POST", body: data });
}

export function updateCollection(
  id: string,
  data: { name?: string; description?: string }
): Promise<Collection> {
  return request(`/collections/${id}`, { method: "PUT", body: data });
}

export function deleteCollection(id: string): Promise<void> {
  return request(`/collections/${id}`, { method: "DELETE" });
}

// ---- Documents ----

export interface Document {
  id: string;
  title: string;
  collection_id: string;
  collection_name?: string;
  source_connector: string;
  source_id?: string;
  content_hash?: string;
  status: string;
  chunks_count: number;
  indexed_at: string | null;
  created_at: string;
  metadata?: Record<string, unknown>;
}

export interface DocumentsResponse {
  documents: Document[];
  total: number;
  page: number;
  per_page: number;
}

export function getDocuments(params?: {
  page?: number;
  page_size?: number;
  search?: string;
  collection_id?: string;
  status?: string;
}): Promise<DocumentsResponse> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set("page", String(params.page));
  if (params?.page_size)
    searchParams.set("per_page", String(params.page_size));
  if (params?.search) searchParams.set("search", params.search);
  if (params?.collection_id)
    searchParams.set("collection_id", params.collection_id);
  if (params?.status) searchParams.set("status", params.status);
  const qs = searchParams.toString();
  return request(`/documents${qs ? `?${qs}` : ""}`);
}

export function getDocument(id: string): Promise<Document> {
  return request(`/documents/${id}`);
}

export function deleteDocument(id: string): Promise<void> {
  return request(`/documents/${id}`, { method: "DELETE" });
}

// ---- Admin: Analytics ----

export interface AnalyticsBucket {
  date: string;
  query_count: number;
  avg_latency_ms: number;
  avg_confidence: number;
}

export interface AnalyticsData {
  total_queries: number;
  avg_latency_ms: number;
  avg_confidence: number;
  total_tokens_used: number;
  period_start: string;
  period_end: string;
  buckets: AnalyticsBucket[];
}

export function getAnalytics(params?: {
  days?: number;
}): Promise<AnalyticsData> {
  const searchParams = new URLSearchParams();
  if (params?.days) searchParams.set("days", String(params.days));
  const qs = searchParams.toString();
  return request(`/admin/analytics${qs ? `?${qs}` : ""}`);
}

// ---- Admin: Users ----

export interface User {
  id: string;
  email: string;
  role: string;
  created_at: string;
}

export function getUsers(): Promise<User[]> {
  return request("/admin/users");
}

export function createUser(data: {
  email: string;
  role: string;
  password: string;
}): Promise<User> {
  return request("/admin/users", { method: "POST", body: data });
}

export function updateUser(
  id: string,
  data: { email?: string; role?: string; password?: string }
): Promise<User> {
  return request(`/admin/users/${id}`, { method: "PUT", body: data });
}

export function deleteUser(id: string): Promise<void> {
  return request(`/admin/users/${id}`, { method: "DELETE" });
}

// ---- Admin: API Keys ----

export interface ApiKey {
  id: string;
  name: string;
  raw_key?: string;
  key_prefix: string;
  permissions: Record<string, unknown> | string[];
  last_used_at: string | null;
  expires_at: string | null;
  created_at: string;
}

export function getApiKeys(): Promise<ApiKey[]> {
  return request("/admin/api-keys");
}

export function createApiKey(data: {
  name: string;
  permissions: string[];
  expires_in_days?: number;
}): Promise<ApiKey> {
  return request("/admin/api-keys", { method: "POST", body: data });
}

export function revokeApiKey(id: string): Promise<void> {
  return request(`/admin/api-keys/${id}`, { method: "DELETE" });
}

// ---- Admin: Logs ----

export interface LogEntry {
  id: string;
  tenant_id: string;
  collection_id: string;
  question: string;
  answer: string | null;
  sources: Source[];
  confidence: number | null;
  tokens_used: number | null;
  latency_ms: number | null;
  created_at: string;
  collection_name?: string;
  error?: string;
}

export interface LogsResponse {
  logs: LogEntry[];
  total: number;
  page: number;
  per_page: number;
}

export function getLogs(params?: {
  page?: number;
  page_size?: number;
  collection_id?: string;
  start_date?: string;
  end_date?: string;
  min_confidence?: number;
  max_confidence?: number;
}): Promise<LogsResponse> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set("page", String(params.page));
  if (params?.page_size)
    searchParams.set("per_page", String(params.page_size));
  if (params?.collection_id)
    searchParams.set("collection_id", params.collection_id);
  if (params?.start_date) searchParams.set("start_date", params.start_date);
  if (params?.end_date) searchParams.set("end_date", params.end_date);
  if (params?.min_confidence != null)
    searchParams.set("min_confidence", String(params.min_confidence));
  if (params?.max_confidence != null)
    searchParams.set("max_confidence", String(params.max_confidence));
  const qs = searchParams.toString();
  return request(`/admin/logs${qs ? `?${qs}` : ""}`);
}

// ---- Plugins ----

export interface PluginInfo {
  name: string;
  type: string;
  version: string;
  description: string;
  author: string;
  status: string;
  source: string;
  bundled: boolean;
  config_schema: Record<string, any>;
  config: Record<string, any>;
  tags: string[];
}

export function getPlugins(): Promise<PluginInfo[]> {
  return request<{ plugins: PluginInfo[] }>("/plugins").then((r) => r.plugins);
}

export function getPlugin(name: string): Promise<PluginInfo> {
  return request(`/plugins/${name}`);
}

export function enablePlugin(name: string): Promise<void> {
  return request(`/plugins/${name}/enable`, { method: "POST" });
}

export function disablePlugin(name: string): Promise<void> {
  return request(`/plugins/${name}/disable`, { method: "POST" });
}

export function installPlugin(source: string): Promise<PluginInfo> {
  return request("/plugins/install", { method: "POST", body: { source } });
}

export function uninstallPlugin(name: string): Promise<void> {
  return request(`/plugins/${name}`, { method: "DELETE" });
}

export function configurePlugin(
  name: string,
  config: Record<string, any>
): Promise<void> {
  return request(`/plugins/${name}/config`, { method: "PUT", body: { config } });
}

export function getMarketplace(): Promise<any> {
  return request("/plugins/marketplace");
}

// ---- Connectors / Sources ----

export interface Connector {
  id: string;
  name: string;
  type: string;
  status: "connected" | "syncing" | "error" | "disconnected";
  last_sync: string | null;
  document_count: number;
  config: Record<string, string>;
}

export function getConnectors(): Promise<Connector[]> {
  return request("/sources");
}

export function createConnector(data: {
  name: string;
  type: string;
  config?: Record<string, string>;
}): Promise<Connector> {
  return request("/sources", { method: "POST", body: data });
}

export function deleteConnector(id: string): Promise<void> {
  return request(`/sources/${id}`, { method: "DELETE" });
}

export function syncConnector(id: string): Promise<{ status: string }> {
  return request(`/sources/${id}/sync`, { method: "POST" });
}

export function testConnector(id: string): Promise<{ ok: boolean; message: string }> {
  return request(`/sources/${id}/test`, { method: "POST" });
}

// ---- Admin: Settings ----

export interface PlatformSettings {
  platform_name: string;
  default_language: string;
  default_persona: string;
  retrieval_strategy: string;
  vector_weight: number;
  default_top_k: number;
  reranking: boolean;
  generation_provider: string;
  generation_model: string;
  temperature: number;
  max_tokens: number;
  webhook_url: string;
  webhook_secret: string;
  webhook_events: string[];
}

export function getSettings(): Promise<PlatformSettings> {
  return request("/admin/settings");
}

export function updateSettings(data: Partial<PlatformSettings>): Promise<PlatformSettings> {
  return request("/admin/settings", { method: "PUT", body: data });
}

// ---- Health ----

export interface HealthStatus {
  status: string;
  version: string;
  uptime?: number;
  database?: string;
  components?: Record<string, { status: string; latency_ms?: number }>;
}

export function getHealth(): Promise<HealthStatus> {
  return request("/health");
}

// ---------------------------------------------------------------------------
// Setup (unprotected)
// ---------------------------------------------------------------------------

export interface SetupStatus {
  needs_setup: boolean;
}

export interface SetupInitRequest {
  platform_name: string;
  admin_email: string;
  admin_password: string;
  embedding_provider: string;
  embedding_api_key?: string;
  generation_provider: string;
  generation_model?: string;
  generation_api_key?: string;
  collection_name?: string;
}

export interface SetupInitResponse {
  tenant_id: string;
  user_id: string;
  api_key: string;
  collection_id?: string;
  message: string;
}

export async function getSetupStatus(): Promise<SetupStatus> {
  const res = await fetch("/api/v1/setup/status");
  if (!res.ok) throw new Error("Failed to check setup status");
  return res.json();
}

export async function initSetup(data: SetupInitRequest): Promise<SetupInitResponse> {
  const res = await fetch("/api/v1/setup/init", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Setup failed");
  }
  return res.json();
}

// ---- Widgets ----

export interface WidgetConfig {
  id: string;
  tenant_id: string;
  name: string;
  widget_type: "chatbot" | "search";
  collection_id: string | null;
  config: Record<string, unknown>;
  public_api_key_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
  raw_public_key?: string;
}

export interface WidgetEmbed {
  widget_id: string;
  embed_code: string;
  public_key_prefix: string | null;
}

export function getWidgets(): Promise<WidgetConfig[]> {
  return request("/admin/widgets");
}

export function getWidget(id: string): Promise<WidgetConfig> {
  return request(`/admin/widgets/${id}`);
}

export function createWidget(data: {
  name: string;
  widget_type: "chatbot" | "search";
  collection_id?: string;
  config?: Record<string, unknown>;
}): Promise<WidgetConfig> {
  return request("/admin/widgets", { method: "POST", body: data });
}

export function updateWidget(
  id: string,
  data: { name?: string; collection_id?: string; config?: Record<string, unknown>; is_active?: boolean }
): Promise<WidgetConfig> {
  return request(`/admin/widgets/${id}`, { method: "PUT", body: data });
}

export function deleteWidget(id: string): Promise<void> {
  return request(`/admin/widgets/${id}`, { method: "DELETE" });
}

export function getWidgetEmbed(id: string): Promise<WidgetEmbed> {
  return request(`/admin/widgets/${id}/embed`);
}

// ---- Templates ----

export interface TemplateInfo {
  name: string;
  title: string;
  description: string;
  template_type: string;
  files: string[];
}

export function getTemplates(): Promise<TemplateInfo[]> {
  return request("/templates");
}

export function getTemplate(name: string): Promise<TemplateInfo> {
  return request(`/templates/${name}`);
}

export async function downloadTemplate(
  name: string,
  config: { api_url: string; api_key: string; widget_id: string; config?: Record<string, unknown> }
): Promise<Blob> {
  const apiKey = getApiKey();
  const res = await fetch(`/api/v1/templates/${name}/download`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}),
    },
    body: JSON.stringify(config),
  });
  if (!res.ok) throw new Error("Failed to download template");
  return res.blob();
}

// ---- Connection Testing ----

export interface ConnectionTestResult {
  service: string;
  status: string;
  latency_ms: number;
  message: string;
  details?: Record<string, unknown>;
}

export async function testConnection(data: {
  service: string;
  provider?: string;
  api_key?: string;
  base_url?: string;
}): Promise<ConnectionTestResult> {
  const res = await fetch("/api/v1/setup/test-connection", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Connection test failed");
  }
  return res.json();
}

// ---- Import / Export ----

export function exportConfig(): Promise<Record<string, unknown>> {
  return request("/admin/export");
}

export function importConfig(data: Record<string, unknown>, merge?: boolean): Promise<{
  message: string;
  imported: { settings: boolean; collections: number; widgets: number; webhooks: number };
}> {
  const params = merge !== undefined ? `?merge=${merge}` : "";
  return request(`/admin/import${params}`, { method: "POST", body: data });
}

// ---- Registration ----

export async function registerAccount(data: {
  email: string;
  password: string;
  name?: string;
  org_name?: string;
}): Promise<{
  access_token: string;
  api_key: string;
  user: { id: string; email: string; role: string };
  tenant_name: string;
}> {
  const res = await fetch("/api/v1/admin/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Registration failed");
  }
  return res.json();
}

// ---- Evaluation ----

export interface EvalTestCase {
  question: string;
  expected_answer?: string;
  expected_sources?: string[];
}

export interface EvalTestCaseResult {
  question: string;
  answer: string;
  expected_answer?: string;
  sources: Array<{ title: string; content: string; score: number }>;
  confidence: number;
  latency_ms: number;
  relevance_score?: number;
  answer_similarity?: number;
  source_hit?: boolean;
}

export interface EvalSuiteResult {
  name: string;
  total_cases: number;
  avg_confidence: number;
  avg_latency_ms: number;
  avg_relevance?: number;
  source_hit_rate?: number;
  results: EvalTestCaseResult[];
}

export function runEvalSuite(data: {
  name?: string;
  collection: string;
  top_k?: number;
  test_cases: EvalTestCase[];
}): Promise<EvalSuiteResult> {
  return request("/eval/run", { method: "POST", body: data });
}

export function quickEval(
  question: string,
  collection: string,
  expectedAnswer?: string,
  topK?: number,
): Promise<EvalTestCaseResult> {
  const params = new URLSearchParams({ question, collection });
  if (expectedAnswer) params.set("expected_answer", expectedAnswer);
  if (topK) params.set("top_k", String(topK));
  return request(`/eval/quick?${params}`, { method: "POST" });
}

// ---- Document Intelligence ----

export interface ChunkInfo {
  index: number;
  chunk_id: string;
  content: string;
  metadata: Record<string, unknown>;
  word_count: number;
  vector_id?: string;
}

export interface DocumentChunksResponse {
  document_id: string;
  title: string;
  status: string;
  chunks_count: number;
  collection_id: string;
  chunks: ChunkInfo[];
}

export function getDocumentChunks(id: string): Promise<DocumentChunksResponse> {
  return request(`/documents/${id}/chunks`);
}

// ---- Activity Feed ----

export interface ActivityEvent {
  id: string;
  type: "document_ingested" | "query_made" | "collection_created" | "api_key_created" | "error" | string;
  title: string;
  description: string;
  timestamp: string;
  metadata: Record<string, unknown>;
}

export interface ActivityFeedResponse {
  events: ActivityEvent[];
  total_count: number;
}

export function getActivityFeed(limit?: number): Promise<ActivityFeedResponse> {
  const params = new URLSearchParams();
  if (limit) params.set("limit", String(limit));
  const qs = params.toString();
  return request(`/activity/recent${qs ? `?${qs}` : ""}`);
}

// ---- Collection Comparison ----

export interface CompareRequest {
  collection_a_id: string;
  collection_b_id: string;
  question?: string;
}

export interface CollectionStats {
  id: string;
  name: string;
  doc_count: number;
  chunk_count: number;
  total_words: number;
  avg_chunk_size: number;
  last_updated: string | null;
}

export interface CompareQueryResult {
  answer: string;
  latency_ms: number;
  sources_count: number;
  confidence: number;
}

export interface CompareResponse {
  collection_a: CollectionStats;
  collection_b: CollectionStats;
  query_a: CompareQueryResult | null;
  query_b: CompareQueryResult | null;
}

export function compareCollections(
  data: CompareRequest
): Promise<CompareResponse> {
  return request("/collections/compare", { method: "POST", body: data });
}

// ---- Smart Suggestions ----

export interface Suggestion {
  id: string;
  type: "setup" | "optimization" | "tip" | "warning";
  priority: number;
  title: string;
  description: string;
  action_label: string;
  action_href: string;
  icon: string;
}

export interface SuggestionsResponse {
  suggestions: Suggestion[];
}

export function getSuggestions(): Promise<SuggestionsResponse> {
  return request("/suggestions");
}

// ---- Analytics Dashboard ----

export interface AnalyticsDashboardLatencyTrend {
  date: string;
  avg_latency: number;
  count: number;
}

export interface AnalyticsDashboardTopQuestion {
  question: string;
  count: number;
  avg_confidence: number;
}

export interface AnalyticsDashboardConfidenceBucket {
  bucket: string;
  count: number;
}

export interface AnalyticsDashboardCollectionUsage {
  collection_name: string;
  query_count: number;
}

export interface AnalyticsDashboardData {
  total_queries: number;
  avg_latency_ms: number;
  avg_confidence: number;
  queries_today: number;
  queries_this_week: number;
  latency_trend: AnalyticsDashboardLatencyTrend[];
  top_questions: AnalyticsDashboardTopQuestion[];
  confidence_distribution: AnalyticsDashboardConfidenceBucket[];
  collection_usage: AnalyticsDashboardCollectionUsage[];
  error_rate: number;
}

export function getAnalyticsDashboard(): Promise<AnalyticsDashboardData> {
  return request("/analytics/dashboard");
}

// ---- Billing ----

export interface PlanLimits {
  max_documents: number;
  max_queries_per_month: number;
  max_collections: number;
  max_widgets: number;
}

export interface PlanInfo {
  name: string;
  display_name: string;
  price: number;
  currency: string;
  interval: string | null;
  features: string[];
  limits: PlanLimits;
}

export interface UsageItem {
  used: number;
  limit: number;
  percentage: number;
  label: string;
}

export interface UsageData {
  documents: UsageItem;
  queries: UsageItem;
  collections: UsageItem;
  widgets: UsageItem;
}

export interface SubscriptionData {
  plan: string;
  status: string;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  usage: UsageData;
  limits: PlanLimits;
}

export function getPlans(): Promise<PlanInfo[]> {
  return request("/billing/plans");
}

export function getSubscription(): Promise<SubscriptionData> {
  return request("/billing/subscription");
}

export function getUsage(): Promise<UsageData> {
  return request("/billing/usage");
}

export function createCheckout(plan: string): Promise<{ checkout_url: string }> {
  return request("/billing/checkout", { method: "POST", body: { plan } });
}

export function createBillingPortal(): Promise<{ portal_url: string }> {
  return request("/billing/portal", { method: "POST" });
}

export { ApiError };
