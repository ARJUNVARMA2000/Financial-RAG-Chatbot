# 🚀 Railway Deployment Guide

Complete step-by-step guide to deploy the Financial RAG Chatbot to Railway with FastAPI backend and Streamlit frontend.

---

## Prerequisites

### 1. Railway Account Setup

1. **Create Railway Account**
   - Visit https://railway.app
   - Sign up with GitHub (recommended) or email
   - You'll get $5 free credit/month for testing

2. **Install Railway CLI (Optional but Recommended)**
   ```bash
   npm i -g @railway/cli
   ```
   - Useful for uploading data and accessing terminal
   - Login: `railway login`

### 2. Repository Preparation

1. **Push Code to GitHub**
   - Ensure all code is committed and pushed to GitHub
   - Railway will deploy from your GitHub repository

2. **Verify .gitignore**
   - Ensure `.env` is in `.gitignore` (API keys should never be committed)
   - Verify `data/indexes/` is gitignored (indexes are built per environment)

---

## Deployment Steps

### Step 1: Deploy Backend (FastAPI)

1. **Create New Project**
   - Go to https://railway.app/dashboard
   - Click **"New Project"**
   - Select **"Deploy from GitHub repo"**
   - Choose your repository
   - Railway will auto-detect Python

2. **Configure Backend Service**
   - **Service Name:** `financial-rag-backend` (or your choice)
   - Railway will automatically detect it's a Python project

3. **Set Build and Start Commands**
   - Railway should auto-detect, but verify:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
   - Or Railway will use `Procfile` if present

4. **Add Persistent Volume for Data**
   - Go to your service → **"Variables"** tab
   - Click **"Volumes"** section
   - Click **"Add Volume"**
   - **Mount Path:** `/app/data`
   - **Name:** `data-volume`
   - This persists ChromaDB indexes and raw documents across deployments

5. **Configure Environment Variables**
   - Go to **"Variables"** tab
   - Add the following environment variables:

   ```


6. **Deploy and Get Backend URL**
   - Railway will automatically build and deploy
   - Once deployed, go to **"Settings"** → **"Networking"**
   - Generate a public domain or use the provided one
   - **Copy the URL:** `https://your-backend-name.up.railway.app`
   - Save this URL for frontend configuration

---
financial-rag-chatbot-production.up.railway.app

### Step 2: Deploy Frontend (Streamlit)

1. **Create Second Service**
   - In the same Railway project, click **"New"** → **"GitHub Repo"**
   - Select the **same repository** as backend
   - This creates a second service in the same project

2. **Configure Frontend Service**
   - **Service Name:** `financial-rag-frontend`
   - Railway will auto-detect Python

3. **Set Build and Start Commands**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `streamlit run frontend/streamlit_app.py --server.port $PORT --server.address 0.0.0.0`
   - Or Railway will use `Procfile.frontend` if configured

4. **Configure Environment Variables**
   - Go to **"Variables"** tab
   - Add:
   ```
   FIN_RAG_API_BASE=https://your-backend-name.up.railway.app
   ```
   - Replace with your actual backend URL from Step 1

5. **Deploy and Get Frontend URL**
   - Railway will build and deploy
   - Go to **"Settings"** → **"Networking"**
   - Generate a public domain
   - **Copy the URL:** `https://your-frontend-name.up.railway.app`

---

### Step 3: Update Backend CORS

1. **Update Backend Environment Variable**
   - Go back to **Backend service** → **"Variables"** tab
   - Update `FRONTEND_URL` to your frontend URL:
   ```
   FRONTEND_URL=https://your-frontend-name.up.railway.app
   ```
   - Railway will automatically redeploy when environment variables change

2. **Verify CORS Configuration**
   - The backend code in `backend/app/main.py` reads `FRONTEND_URL` from environment
   - It allows both the production URL and localhost for development

---

## Data Migration

You need to upload your documents and build the index on Railway. Choose one method:

### Option A: Build Index on Railway (Recommended)

1. **Access Railway Terminal**
   - Go to your backend service
   - Click **"Deployments"** → Select latest deployment → **"View Logs"**
   - Or use Railway CLI: `railway run` (after `railway link`)

2. **Upload Documents**
   - Use Railway CLI to upload files:
   ```bash
   railway link  # Link to your project
   railway run  # Get shell access
   ```
   - Or use Railway's web terminal if available
   - Upload documents to `/app/data/raw/<TICKER>/` directory

3. **Build Index**
   ```bash
   python scripts/build_index.py --ticker AMZN --period Q3-2025
   ```
   - Indexes will be saved to `/app/data/indexes/chroma/` (persistent volume)

### Option B: Upload Pre-built Index

1. **Build Index Locally**
   ```bash
   python scripts/build_index.py --ticker AMZN --period Q3-2025
   ```

2. **Upload to Railway**
   - Use Railway CLI or web interface
   - Upload entire `data/` directory to the mounted volume at `/app/data`

### Option C: Use Railway CLI for File Transfer

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and link project
railway login
railway link

# Upload data directory (from local machine)
railway run --service financial-rag-backend
# Then use scp, rsync, or Railway's file upload feature
```

---

## Verification

### 1. Backend Health Check
- Visit: `https://your-backend-name.up.railway.app/health`
- Should return: `{"status": "healthy"}`

### 2. Backend API Documentation
- Visit: `https://your-backend-name.up.railway.app/docs`
- Should show Swagger UI with all endpoints

### 3. Frontend Access
- Visit: `https://your-frontend-name.up.railway.app`
- Should show Streamlit chat interface

### 4. Test End-to-End
- In the frontend, ask a question like: "What was AWS revenue in Q3 2025?"
- Verify it connects to backend and returns results with citations

---

## Configuration Files Reference

### Procfile (Backend)
```
web: uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
```

### Procfile.frontend (Frontend)
```
web: streamlit run frontend/streamlit_app.py --server.port $PORT --server.address 0.0.0.0
```

### railway.json (Optional)
Railway can use this for additional configuration, but auto-detection usually works.

---

## Environment Variables Summary

### Backend Service
- `OPENAI_API_KEY` - Required
- `OPENAI_BASE_URL` - Optional (leave empty for default)
- `OPENAI_CHAT_MODEL` - Default: `gpt-4.1-mini`
- `OPENAI_EMBEDDING_MODEL` - Default: `text-embedding-3-large`
- `OPENROUTER_API_KEY` - Optional (for multi-model evaluation)
- `OPENROUTER_BASE_URL` - Default: `https://openrouter.ai/api/v1`
- `FRONTEND_URL` - Your frontend Railway URL
- `PORT` - Automatically set by Railway (don't override)

### Frontend Service
- `FIN_RAG_API_BASE` - Your backend Railway URL
- `PORT` - Automatically set by Railway

---

## Troubleshooting

### Backend Issues

**Problem:** Backend won't start
- **Solution:** Check logs in Railway dashboard
- Verify all environment variables are set
- Ensure `requirements.txt` is correct

**Problem:** CORS errors in browser
- **Solution:** Verify `FRONTEND_URL` in backend matches exact frontend URL
- Check that frontend URL doesn't have trailing slash
- Ensure CORS middleware is configured correctly

**Problem:** ChromaDB not persisting data
- **Solution:** Verify volume is mounted at `/app/data`
- Check that `data/indexes/chroma/` directory exists
- Ensure volume is attached to backend service

### Frontend Issues

**Problem:** Frontend can't connect to backend
- **Solution:** Verify `FIN_RAG_API_BASE` is set correctly
- Check backend URL is accessible (visit `/health` endpoint)
- Ensure backend CORS allows frontend URL

**Problem:** Streamlit not starting
- **Solution:** Check logs for errors
- Verify `requirements.txt` includes `streamlit`
- Ensure start command uses `--server.address 0.0.0.0`

### Data Issues

**Problem:** No documents found
- **Solution:** Verify documents are in `/app/data/raw/<TICKER>/`
- Check volume is mounted correctly
- Rebuild index: `python scripts/build_index.py --ticker <TICKER> --period <PERIOD>`

**Problem:** Index not found
- **Solution:** Build index on Railway using terminal
- Verify ChromaDB directory exists in volume
- Check file permissions

---

## Updating Deployment

### Code Updates
- Push changes to GitHub
- Railway automatically redeploys on push (if enabled)
- Or manually trigger deployment from Railway dashboard

### Environment Variable Updates
- Go to service → **"Variables"** tab
- Update variables
- Railway automatically redeploys

### Data Updates
- Access Railway terminal
- Run indexing script: `python scripts/build_index.py --ticker <TICKER> --period <PERIOD>`
- Data persists in volume across deployments

---

## Cost Considerations

- **Free Tier:** $5 credit/month
- **Pricing:** Pay-as-you-go after free tier
- **Tips:**
  - Use Railway's sleep feature for development (services sleep after inactivity)
  - Monitor usage in Railway dashboard
  - Consider using Railway's "Pause" feature when not in use

---

## Security Best Practices

1. **Never commit API keys** - Use Railway environment variables
2. **Use Railway's private networking** - Services in same project can communicate privately
3. **Set up domain restrictions** - Configure CORS to only allow your frontend domain
4. **Monitor logs** - Check Railway logs regularly for errors or suspicious activity
5. **Rotate API keys** - Regularly update your OpenAI/OpenRouter API keys

---

## Next Steps

After successful deployment:

1. **Set up custom domains** (optional) - Use your own domain instead of Railway subdomain
2. **Configure monitoring** - Set up alerts for service health
3. **Optimize performance** - Monitor response times and optimize queries
4. **Scale resources** - Adjust Railway service resources if needed

---

## Support

- **Railway Docs:** https://docs.railway.app
- **Railway Discord:** https://discord.gg/railway
- **Project Issues:** Check GitHub repository issues

---

For local development setup, see [SETUP_GUIDE.md](SETUP_GUIDE.md).

