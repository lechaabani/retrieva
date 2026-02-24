import type { HttpClient } from "../client.js";
import type {
  Collection,
  CollectionListResponse,
  CreateCollectionBody,
  UpdateCollectionBody,
} from "../types.js";

export class CollectionsResource {
  private readonly client: HttpClient;

  constructor(client: HttpClient) {
    this.client = client;
  }

  /**
   * List all collections the authenticated user has access to.
   */
  async list(): Promise<Collection[]> {
    const res = await this.client.get<CollectionListResponse | Collection[]>(
      "/api/v1/collections",
    );
    // Support both { collections: [...] } and plain [...] response shapes.
    return Array.isArray(res) ? res : res.collections;
  }

  /**
   * Retrieve a single collection by its ID.
   */
  async get(id: string): Promise<Collection> {
    return this.client.get<Collection>(`/api/v1/collections/${encodeURIComponent(id)}`);
  }

  /**
   * Create a new collection.
   */
  async create(body: CreateCollectionBody): Promise<Collection> {
    return this.client.post<Collection>("/api/v1/collections", body);
  }

  /**
   * Update an existing collection.
   */
  async update(id: string, body: UpdateCollectionBody): Promise<Collection> {
    return this.client.put<Collection>(
      `/api/v1/collections/${encodeURIComponent(id)}`,
      body,
    );
  }

  /**
   * Delete a collection by its ID.
   */
  async delete(id: string): Promise<void> {
    await this.client.delete<void>(`/api/v1/collections/${encodeURIComponent(id)}`);
  }
}
