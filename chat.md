# OddWons - Railway Deployment (Simple)

_Last updated: January 6, 2025_

The app works locally. Just need correct Railway configs.

---

## STEP 1: Fix Backend Config

**Delete `railway.toml`, create `railway.json`:**

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

**Create `nixpacks.toml`:**

```toml
[phases.setup]
nixPkgs = ["python311", "postgresql", "gcc", "libffi"]
nixLibs = ["libffi", "openssl"]

[phases.install]
cmds = [
    "pip install --upgrade pip",
    "pip install -r requirements.txt"
]

[start]
cmd = "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
```

---

## STEP 2: Fix Frontend Config

**Delete `frontend/railway.toml`, create `frontend/railway.json`:**

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "healthcheckPath": "/",
    "healthcheckTimeout": 30,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

---

## STEP 3: Fix DATABASE_URL Format

Railway gives `postgresql://` but asyncpg needs `postgresql+asyncpg://`.

**Edit `app/config.py` - add this method to Settings class:**

```python
def model_post_init(self, __context):
    """Fix Railway's DATABASE_URL format."""
    if self.database_url.startswith("postgresql://") and "+asyncpg" not in self.database_url:
        object.__setattr__(
            self, 
            'database_url', 
            self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        )
```

---

## STEP 4: Railway Dashboard Cleanup

1. Delete duplicate Postgres (keep one with data)
2. Delete duplicate Redis (keep active one)
3. Set backend service variables (use Railway references):

```
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis-SaFD.REDIS_URL}}
```

4. Set frontend service variable:
```
BACKEND_URL=https://<backend-service-url>.up.railway.app
```

---

## STEP 5: Deploy

```bash
git add .
git commit -m "Fix Railway configs"
git push
```

Railway auto-deploys on push. Done.
