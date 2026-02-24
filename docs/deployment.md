# Deployment Guide

This guide covers deploying Retrieva in production environments, from Docker Compose to Kubernetes, along with security, scaling, and operational considerations.

## Docker Compose Deployment

Docker Compose is the simplest way to deploy Retrieva. It is suitable for single-server deployments and small-to-medium workloads.

### Prerequisites

- Docker >= 24.0
- Docker Compose >= 2.20
- At least 4 GB RAM and 2 CPU cores
- Persistent storage for databases

### Steps

1. Clone the repository and configure:

```bash
git clone https://github.com/your-org/retrieva.git
cd retrieva
cp config.example.yaml config.yaml
```

2. Create a production `.env` file:

```bash
# Application
RETRIEVA_ENVIRONMENT=production
RETRIEVA_DEBUG=false

# Secrets
OPENAI_API_KEY=sk-your-production-key
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Database
POSTGRES_USER=retrieva
POSTGRES_PASSWORD=$(openssl rand -hex 16)
POSTGRES_DB=retrieva

# Ports (optional)
API_PORT=8000
```

3. Start all services:

```bash
docker-compose up -d
```

4. Run database migrations:

```bash
docker-compose exec api alembic upgrade head
```

5. Verify the deployment:

```bash
curl http://localhost:8000/health
```

### Service Architecture

```
                   +-------------------+
                   |   Load Balancer   |
                   |   (nginx/caddy)   |
                   +--------+----------+
                            |
              +-------------+-------------+
              |                           |
     +--------v--------+       +----------v--------+
     |    API Server    |       |    Dashboard      |
     |    (FastAPI)     |       |    (Next.js)      |
     |    Port 8000     |       |    Port 3000      |
     +--------+---------+       +-------------------+
              |
    +---------+---------+
    |         |         |
+---v---+ +--v----+ +--v------+
|Postgres| |Qdrant | | Redis   |
| :5432  | | :6333 | | :6379   |
+--------+ +-------+ +----+----+
                           |
                    +------v------+
                    |   Celery    |
                    |   Worker    |
                    +-------------+
```

## Environment Variables

All configuration can be set via environment variables. See the [Configuration Reference](./configuration.md) for the full list.

### Required for Production

| Variable            | Description                              |
|---------------------|------------------------------------------|
| `OPENAI_API_KEY`    | OpenAI API key (or `ANTHROPIC_API_KEY`)  |
| `JWT_SECRET_KEY`    | Secret for signing JWT tokens            |
| `POSTGRES_PASSWORD` | PostgreSQL password                      |
| `DATABASE_URL`      | Full database connection string          |

### Optional

| Variable                     | Default                | Description                    |
|------------------------------|------------------------|--------------------------------|
| `RETRIEVA_ENVIRONMENT`       | `development`          | Runtime environment            |
| `RETRIEVA_DEBUG`             | `false`                | Enable debug mode              |
| `RETRIEVA_LOG_LEVEL`         | `INFO`                 | Logging level                  |
| `API_PORT`                   | `8000`                 | API server port                |
| `QDRANT_API_KEY`             | --                     | Qdrant Cloud API key           |
| `REDIS_URL`                  | `redis://localhost:6379/0` | Redis connection string    |
| `CELERY_BROKER_URL`          | Same as `REDIS_URL`    | Celery broker URL              |
| `CELERY_RESULT_BACKEND`      | `redis://localhost:6379/1` | Celery result backend      |

## SSL/TLS Setup

### Using a Reverse Proxy (Recommended)

Place nginx or Caddy in front of the API server.

**nginx example** (`/etc/nginx/sites-available/retrieva`):

```nginx
server {
    listen 443 ssl;
    server_name api.retrieva.example.com;

    ssl_certificate     /etc/ssl/certs/retrieva.crt;
    ssl_certificate_key /etc/ssl/private/retrieva.key;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Caddy example** (`Caddyfile`):

```
api.retrieva.example.com {
    reverse_proxy localhost:8000
}
```

Caddy automatically provisions and renews TLS certificates via Let's Encrypt.

## Kubernetes Deployment

For larger-scale deployments, Kubernetes provides automatic scaling, self-healing, and rolling updates.

### Basic Manifests

**Namespace:**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: retrieva
```

**API Deployment:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: retrieva-api
  namespace: retrieva
spec:
  replicas: 2
  selector:
    matchLabels:
      app: retrieva-api
  template:
    metadata:
      labels:
        app: retrieva-api
    spec:
      containers:
        - name: api
          image: your-registry/retrieva:latest
          ports:
            - containerPort: 8000
          envFrom:
            - secretRef:
                name: retrieva-secrets
            - configMapRef:
                name: retrieva-config
          resources:
            requests:
              memory: "512Mi"
              cpu: "500m"
            limits:
              memory: "1Gi"
              cpu: "1000m"
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 30
---
apiVersion: v1
kind: Service
metadata:
  name: retrieva-api
  namespace: retrieva
spec:
  selector:
    app: retrieva-api
  ports:
    - port: 80
      targetPort: 8000
  type: ClusterIP
```

**Worker Deployment:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: retrieva-worker
  namespace: retrieva
spec:
  replicas: 2
  selector:
    matchLabels:
      app: retrieva-worker
  template:
    metadata:
      labels:
        app: retrieva-worker
    spec:
      containers:
        - name: worker
          image: your-registry/retrieva:latest
          command:
            - celery
            - -A
            - workers.celery_app
            - worker
            - --loglevel=info
            - --concurrency=2
          envFrom:
            - secretRef:
                name: retrieva-secrets
          resources:
            requests:
              memory: "1Gi"
              cpu: "500m"
            limits:
              memory: "2Gi"
              cpu: "1000m"
```

**Secrets:**

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: retrieva-secrets
  namespace: retrieva
type: Opaque
stringData:
  OPENAI_API_KEY: "sk-your-key"
  JWT_SECRET_KEY: "your-secret"
  DATABASE_URL: "postgresql+asyncpg://user:pass@postgres:5432/retrieva"
  REDIS_URL: "redis://redis:6379/0"
```

## Scaling Considerations

### Horizontal Scaling

| Component   | Scaling Strategy                          | Notes                           |
|-------------|-------------------------------------------|---------------------------------|
| API Server  | Add replicas behind a load balancer       | Stateless; scale freely         |
| Workers     | Add replicas for higher ingestion throughput| Scale based on queue depth     |
| PostgreSQL  | Read replicas for query load              | Single primary for writes       |
| Qdrant      | Distributed mode with sharding            | See Qdrant docs for clustering  |
| Redis       | Redis Sentinel or Redis Cluster           | For HA message broker           |

### Performance Tuning

- **Database pool size**: Increase `DB_POOL_MAX_SIZE` for high concurrency
- **Worker concurrency**: Adjust `--concurrency` flag based on CPU cores
- **Embedding batch size**: Increase `INGESTION_BATCH_SIZE` for throughput
- **Qdrant gRPC**: Enable `QDRANT_PREFER_GRPC=true` for faster vector operations

## Backup and Restore

### PostgreSQL

**Backup:**

```bash
docker-compose exec postgres pg_dump -U retrieva retrieva > backup.sql
```

**Restore:**

```bash
docker-compose exec -T postgres psql -U retrieva retrieva < backup.sql
```

### Qdrant

**Snapshot:**

```bash
curl -X POST http://localhost:6333/collections/your_collection/snapshots
```

**Restore:** Download the snapshot and use the Qdrant restore API.

### Redis

Redis is used for caching and task queues. Data is ephemeral and does not require backup. Tasks in-flight will be retried automatically.

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

Returns the status of all dependencies (database, vector store, Redis).

### Logging

Retrieva outputs structured JSON logs. Configure log level via `RETRIEVA_LOG_LEVEL`.

```bash
# View API logs
docker-compose logs -f api

# View worker logs
docker-compose logs -f worker
```

### Metrics

Enable Prometheus metrics export in `config.yaml`:

```yaml
analytics:
  enabled: true
  export:
    provider: prometheus
    port: 9090
```

Key metrics to monitor:

- **Query latency** (p50, p95, p99)
- **Ingestion throughput** (documents/min)
- **Queue depth** (pending Celery tasks)
- **Vector store performance** (search latency, collection sizes)
- **Error rates** (4xx, 5xx responses)

### Alerting Recommendations

| Metric                        | Warning Threshold | Critical Threshold |
|-------------------------------|-------------------|--------------------|
| Query p95 latency             | > 3s              | > 10s              |
| Error rate (5xx)              | > 1%              | > 5%               |
| Celery queue depth            | > 100             | > 1000             |
| Disk usage (Postgres/Qdrant)  | > 70%             | > 90%              |
| Memory usage                  | > 80%             | > 95%              |
