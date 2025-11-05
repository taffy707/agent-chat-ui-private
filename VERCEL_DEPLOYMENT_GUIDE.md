# Vercel Deployment Guide - Agent Chat UI

**Date:** November 5, 2025
**Status:** In Progress - HTTP/HTTPS Issue Needs Resolution

---

## Issues Found & Fixes Applied

### ✅ Issue 1: CORS Blocking Document API (FIXED)

**Problem:** Document API was only configured to accept requests from `localhost`, blocking Vercel domains.

**Solution Applied:**

- Updated `/document-api/main.py` to allow all origins temporarily
- Rebuilt and redeployed to Cloud Run (revision: document-api-00003-468)
- **Status:** FIXED ✅

**Verification:**

```bash
curl https://document-api-169798107925.us-central1.run.app/health
# Should return 200 OK
```

---

### ⚠️ Issue 2: HTTP/HTTPS Mixed Content Blocking (NEEDS FIX)

**Problem:**

- Your Vercel site uses HTTPS: `https://your-app.vercel.app`
- Your LangGraph server uses HTTP: `http://136.116.156.246:8123`
- Modern browsers **block HTTP requests from HTTPS pages** for security

**Error in Browser Console:**

```
Mixed Content: The page at 'https://your-app.vercel.app' was loaded over HTTPS,
but requested an insecure XMLHttpRequest endpoint 'http://136.116.156.246:8123'.
This request has been blocked; the content must be served over HTTPS.
```

**Solutions (Choose One):**

#### Option A: Enable HTTPS for Your LangGraph Server (Recommended)

**Using Cloudflare Tunnel (Free & Easy):**

1. Install cloudflared:

   ```bash
   # macOS
   brew install cloudflare/cloudflare/cloudflared

   # Linux
   wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
   sudo dpkg -i cloudflared-linux-amd64.deb
   ```

2. Authenticate with Cloudflare:

   ```bash
   cloudflared tunnel login
   ```

3. Create a tunnel:

   ```bash
   cloudflared tunnel create langgraph-server
   ```

4. Configure the tunnel (create `config.yml`):

   ```yaml
   tunnel: <TUNNEL-ID>
   credentials-file: /path/to/.cloudflared/<TUNNEL-ID>.json

   ingress:
     - hostname: langgraph.yourdomain.com
       service: http://localhost:8123
     - service: http_status:404
   ```

5. Route DNS:

   ```bash
   cloudflared tunnel route dns <TUNNEL-ID> langgraph.yourdomain.com
   ```

6. Run the tunnel:
   ```bash
   cloudflared tunnel run langgraph-server
   ```

**Result:** Your LangGraph server accessible at `https://langgraph.yourdomain.com`

---

#### Option B: Deploy LangGraph to Cloud Run (Automatic HTTPS)

**Advantages:**

- Automatic HTTPS
- Auto-scaling
- Same infrastructure as Document API
- No server maintenance

**Steps:**

1. **Create Dockerfile for LangGraph** (if not exists):

   ```dockerfile
   FROM python:3.11-slim

   WORKDIR /app

   # Copy requirements and install
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   # Copy LangGraph application
   COPY . .

   # Expose port
   EXPOSE 8080

   # Run LangGraph server
   CMD ["langgraph", "serve", "--host", "0.0.0.0", "--port", "8080"]
   ```

2. **Build and push to GCR:**

   ```bash
   cd /path/to/langgraph/server
   gcloud builds submit --tag gcr.io/metatask-461115/langgraph-server
   ```

3. **Deploy to Cloud Run:**

   ```bash
   gcloud run deploy langgraph-server \
       --image gcr.io/metatask-461115/langgraph-server \
       --platform managed \
       --region us-central1 \
       --allow-unauthenticated \
       --memory 1Gi \
       --timeout 300 \
       --max-instances 5
   ```

4. **Get URL:**

   ```bash
   gcloud run services describe langgraph-server \
       --region us-central1 \
       --format "value(status.url)"

   # Example output: https://langgraph-server-169798107925.us-central1.run.app
   ```

5. **Update Vercel environment variables:**
   ```
   NEXT_PUBLIC_API_URL=https://langgraph-server-169798107925.us-central1.run.app
   ```

---

#### Option C: Use Nginx Reverse Proxy with Let's Encrypt

**For existing VPS/dedicated server:**

1. **Install Nginx:**

   ```bash
   sudo apt-get update
   sudo apt-get install nginx certbot python3-certbot-nginx
   ```

2. **Configure Nginx** (`/etc/nginx/sites-available/langgraph`):

   ```nginx
   server {
       server_name langgraph.yourdomain.com;

       location / {
           proxy_pass http://localhost:8123;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }
   }
   ```

3. **Enable site:**

   ```bash
   sudo ln -s /etc/nginx/sites-available/langgraph /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

4. **Get SSL certificate:**
   ```bash
   sudo certbot --nginx -d langgraph.yourdomain.com
   ```

**Result:** HTTPS enabled at `https://langgraph.yourdomain.com`

---

## Current Environment Variables for Vercel

### What to Set in Vercel Dashboard

Go to: **Vercel Project → Settings → Environment Variables**

```bash
# Your self-hosted LangGraph server (needs HTTPS!)
NEXT_PUBLIC_API_URL=http://136.116.156.246:8123  # ⚠️ Change to HTTPS URL
NEXT_PUBLIC_ASSISTANT_ID=retrieval_graph

# Document API (already working with HTTPS)
NEXT_PUBLIC_DOCUMENT_API_URL=https://document-api-169798107925.us-central1.run.app
```

**Important:** Once you enable HTTPS for LangGraph, update `NEXT_PUBLIC_API_URL` to the HTTPS URL.

---

## Vercel Deployment Steps

### Step 1: Push Code to GitHub

```bash
git add -A
git commit -m "fix: Update CORS configuration for production deployment"
git push origin main
```

### Step 2: Import to Vercel

1. Go to [vercel.com](https://vercel.com)
2. Click **"Import Project"**
3. Select your GitHub repository: `taffy707/agent-chat-ui-private`
4. Vercel will auto-detect Next.js

### Step 3: Configure Environment Variables

In Vercel dashboard, add:

| Name                           | Value                                                   | Environments                     |
| ------------------------------ | ------------------------------------------------------- | -------------------------------- |
| `NEXT_PUBLIC_API_URL`          | `https://langgraph.yourdomain.com` (after HTTPS setup)  | Production, Preview, Development |
| `NEXT_PUBLIC_ASSISTANT_ID`     | `retrieval_graph`                                       | Production, Preview, Development |
| `NEXT_PUBLIC_DOCUMENT_API_URL` | `https://document-api-169798107925.us-central1.run.app` | Production, Preview, Development |

**Note:** Select all three environments (Production, Preview, Development) for each variable.

### Step 4: Deploy

Click **"Deploy"** - Vercel will:

1. Install dependencies (`pnpm install`)
2. Build your Next.js app (`pnpm build`)
3. Deploy to CDN
4. Provide a URL like `https://agent-chat-ui-private.vercel.app`

### Step 5: Verify Deployment

1. **Visit your Vercel URL**
2. **Open Browser DevTools** (F12) → Console tab
3. **Look for errors:**
   - ✅ No errors = Everything working!
   - ❌ Mixed content error = Need to enable HTTPS for LangGraph
   - ❌ CORS error = Need to whitelist Vercel domain in Document API

---

## Testing Checklist

After deployment, test these features:

- [ ] Frontend loads without errors
- [ ] Can create/view knowledge base collections
- [ ] Can upload documents to Document API
- [ ] Documents appear in the UI after upload
- [ ] Can chat with LangGraph agent
- [ ] Agent responses stream correctly
- [ ] Can view chat history
- [ ] No mixed content warnings in browser console

---

## Debugging Common Issues

### Issue: "Mixed Content" Error

**Symptom:** Browser console shows mixed content blocking

**Solution:** Follow Option A, B, or C above to enable HTTPS for LangGraph

---

### Issue: "CORS" Error

**Symptom:**

```
Access to XMLHttpRequest at 'https://document-api...' from origin 'https://your-app.vercel.app'
has been blocked by CORS policy
```

**Solution:**

1. Get your exact Vercel URL (e.g., `https://agent-chat-ui-abc123.vercel.app`)
2. Update `document-api/main.py`:
   ```python
   allow_origins=[
       "http://localhost:3000",
       "https://your-app.vercel.app",  # Add your actual Vercel URL
   ]
   ```
3. Rebuild and redeploy Document API

---

### Issue: Environment Variables Not Working

**Symptom:** App can't connect to APIs

**Solution:**

1. Verify variables are set in Vercel dashboard
2. Make sure they're selected for "Production" environment
3. Redeploy: Vercel → Deployments → Click "..." → Redeploy

---

### Issue: LangGraph Server Returns 404

**Symptom:** All requests to LangGraph fail

**Solution:**

1. Verify LangGraph server is running: `curl http://136.116.156.246:8123/threads`
2. Check if port 8123 is accessible from internet (not blocked by firewall)
3. Verify `NEXT_PUBLIC_ASSISTANT_ID=retrieval_graph` matches your graph name

---

## Production Checklist

Before going live:

- [ ] HTTPS enabled for LangGraph server
- [ ] Document API CORS restricted to specific Vercel domain
- [ ] All environment variables set in Vercel
- [ ] Custom domain configured (optional)
- [ ] SSL certificate valid
- [ ] All features tested on production URL
- [ ] Error monitoring set up (Sentry, LogRocket, etc.)
- [ ] Analytics configured (if needed)

---

## Current Status

### ✅ What's Working

1. **Document API:** Fully deployed on Cloud Run with HTTPS
   - URL: https://document-api-169798107925.us-central1.run.app
   - CORS: Configured to allow all origins (temporarily)
   - Database: Cloud SQL with proper schema
   - Storage: Google Cloud Storage bucket configured

### ⚠️ What Needs Attention

1. **LangGraph Server:** Needs HTTPS

   - Current: `http://136.116.156.246:8123` (HTTP only)
   - Required: HTTPS URL for Vercel compatibility
   - **Action Required:** Choose and implement Option A, B, or C above

2. **CORS Security:** Currently allowing all origins
   - **Recommendation:** Restrict to specific Vercel domain in production
   - Update `document-api/main.py` with your exact Vercel URL

---

## Quick Start (After HTTPS Setup)

Once you've enabled HTTPS for LangGraph:

1. **Update Vercel Environment Variables:**

   ```
   NEXT_PUBLIC_API_URL=https://your-langgraph-https-url
   ```

2. **Trigger Redeploy in Vercel:**

   - Go to Vercel dashboard
   - Click "Deployments"
   - Click "..." on latest deployment
   - Click "Redeploy"

3. **Test Everything:**
   - Visit your Vercel URL
   - Open DevTools Console (F12)
   - Upload a document
   - Chat with agent
   - Verify no errors

---

## Need Help?

**Common Questions:**

**Q: Which HTTPS option should I choose?**
A:

- Have a VPS/server? → Option C (Nginx + Let's Encrypt)
- Want easiest setup? → Option A (Cloudflare Tunnel)
- Want same infrastructure? → Option B (Cloud Run)

**Q: How much will this cost?**
A:

- Vercel: Free tier (generous limits)
- Cloudflare Tunnel: Free
- Cloud Run: ~$5-15/month (with your credits = free for years)
- Document API: Already deployed (~$10-25/month = free with credits)

**Q: Can I test locally first?**
A: Yes! Everything works locally with HTTP. The HTTPS requirement only applies to production Vercel deployment.

---

## Next Steps

1. **Choose an HTTPS option** for LangGraph (A, B, or C)
2. **Implement HTTPS setup**
3. **Update Vercel environment variables** with HTTPS URL
4. **Redeploy and test**
5. **Restrict CORS** to your specific Vercel domain

---

**Document API Status:** ✅ Deployed and configured
**LangGraph HTTPS:** ⚠️ Needs setup
**Vercel Deployment:** ⏳ Ready after HTTPS setup
