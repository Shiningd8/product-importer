# Railway Deployment Guide

## Step-by-Step Instructions

### 1. Install Railway CLI
```bash
npm i -g @railway/cli
```

### 2. Login to Railway
```bash
railway login
```

### 3. Initialize Project
```bash
railway init
```
- Choose "New Project"
- Name it: `product-importer`

### 4. Add PostgreSQL Database
```bash
railway add postgresql
```
This will automatically create a PostgreSQL database and set `DATABASE_URL` environment variable.

### 5. Add Redis
```bash
railway add redis
```
This will automatically create a Redis instance and set `REDIS_URL` environment variable.

### 6. Set Environment Variables
```bash
railway variables set CELERY_BROKER_URL=$REDIS_URL
railway variables set CELERY_RESULT_BACKEND=$REDIS_URL
```

### 7. Deploy
```bash
railway up
```

### 8. Run Migrations
```bash
railway run alembic upgrade head
```

### 9. Add Worker Service
- Go to Railway Dashboard
- Click on your project
- Click "New" → "Empty Service"
- Name it: `worker`
- Set start command: `celery -A app.celery_app worker --loglevel=info`
- Link the same PostgreSQL and Redis services
- Deploy

Your app will be live at: `https://your-project-name.up.railway.app`

