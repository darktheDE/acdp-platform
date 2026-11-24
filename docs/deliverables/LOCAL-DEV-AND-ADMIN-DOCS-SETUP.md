# Local Development Setup, Error Fixes & Admin Swagger Access

**Date**: 2026-11-24  
**Scope**: Local Dev Environment (`.env.dev`), Docker `core` Profile, Frontend Error Handling, Admin Swagger UI

---

## 1. Local vs Production Environment Separation

- **Local Development (`.env.dev` -> `.env`)**:
  - Uses `POSTGRES_MODE=local` and `POSTGRES_SSL_MODE=disable` to target the local `acdp-postgres` container (`postgres:18.7-alpine3.23`).
  - Uses `ENVIRONMENT=development` and `CORS_ORIGINS=http://localhost:3000`.
  - AI providers (`gemini-3.5-flash-lite`, `@cf/baai/bge-m3`) and Lakehouse (`Cloudflare R2`) remain cloud-backed.
- **Production**: Configured directly via **Vercel Environment Variables** (Frontend) and **Hugging Face Spaces Secrets** (Backend) with `SUPABASE_DATABASE_URL`, `QDRANT_CLUSTER_ENDPOINT`, and `ENVIRONMENT=production`.

### Up-to-Date Docker Launch Commands
```powershell
# Rebuild & pull latest base images for Web (:3000), API (:8000), PostgreSQL 18 (:5432)
docker compose --profile core up -d --build --pull always --remove-orphans

# Recreate API container after editing .env (required because restart does not reload .env)
docker compose --profile core up -d --force-recreate api
```

---

## 2. Local Account Seeding (`scripts/seed_local_users.py`)

- **Script**: [`scripts/seed_local_users.py`](../../scripts/seed_local_users.py)
- **Domain Fix**: Changed local dev emails from `@acdp.local` to `@acdp.dev` because Pydantic `EmailStr` (`email-validator`) rejects `.local` as a reserved/special-use domain.
- **Default Local Accounts** (idempotent append/update):
  - **Admin**: `admin@acdp.dev` / `adminadmin` (role: `admin`)
  - **Student**: `user@acdp.dev` / `useruser` (role: `student`)
- **Run Command**:
```powershell
Get-Content scripts/seed_local_users.py | docker exec -i acdp-api python -
```

---

## 3. Frontend Fix: React Error #31 on FastAPI 422 Responses

- **Issue**: FastAPI returns `422 Unprocessable Entity` with `detail` as an array of objects (`[{type, loc, msg, input, ctx}]`). Passing this array directly into `ApiError.detail` caused React to crash with `Minified React error #31` when rendering.
- **Fix**: Updated [`apps/web/lib/api-client.ts`](../../apps/web/lib/api-client.ts#L72-L86) to normalize `errJson.detail` into a plain `string` (handling `string`, `Array<{msg}>`, and fallback `JSON.stringify`).
- **Verification**: `npx tsc -p apps/web/tsconfig.json --noEmit` passed with exit code `0`.

---

## 4. Swagger UI & Protected Admin Docs

- **Local Dev (`ENVIRONMENT != "production"`)**:
  - [`src/acdp/api/main.py`](../../src/acdp/api/main.py) automatically enables `/docs` and `/openapi.json` when `ENVIRONMENT` is not `"production"`.
  - [`docker-compose.yml`](../../docker-compose.yml) forwards `ENVIRONMENT: ${ENVIRONMENT:-development}` to the `acdp-api` container.
  - [`apps/web/app/admin/page.tsx`](../../apps/web/app/admin/page.tsx) includes a **"Mở Swagger UI"** button that opens `${NEXT_PUBLIC_API_URL}/docs` in a new tab.
- **Production (`ENVIRONMENT == "production"`)**:
  - Public `/docs` and `/openapi.json` are automatically disabled (`None`).
  - Authenticated administrators (`role == "admin"`) can still inspect the schema via [`src/acdp/api/routers/admin.py`](../../src/acdp/api/routers/admin.py#L197-L215):
    - **Swagger UI**: `GET /api/v1/admin/docs` (requires `Authorization: Bearer <admin_jwt>`)
    - **OpenAPI Schema**: `GET /api/v1/admin/openapi.json` (used by the `/admin` portal preview)
