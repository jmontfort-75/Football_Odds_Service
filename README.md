# football-odds-service



## Stack

- **Frontend:** Next.js 14 (App Router) — TypeScript, CSS
- **Backend:** FastAPI (Python 3.11)
- **Deployment:** Docker → Docker Hub → Coolify

## Environments

| Environment | Frontend | Backend | 
|-------------|----------|---------|
| Staging | https://football-odds-service-staging.projectsin.ai | https://api.football-odds-service-staging.projectsin.ai | |
| Production | https://football-odds-service.projectsin.ai | https://api.football-odds-service.projectsin.ai | |

## Development

```bash
cp .env.example .env.local
# fill in values
npm install
npm run dev
```

## Deployment

Push to `staging` branch → builds and deploys to staging automatically.
Push to `main` branch → builds and deploys to production automatically.
