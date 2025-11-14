# 🚀 Deployment Guide - Streamlit Cloud

> **Step-by-step guide to deploy your Lead Intelligence AI**

---

## 📋 Pre-Deployment Checklist

- [x] Code complete and tested
- [x] Requirements.txt exists
- [ ] Git repository initialized
- [ ] GitHub account ready
- [ ] Streamlit Cloud account ready
- [ ] OpenAI API key ready

---

## 🎯 Option 1: Streamlit Cloud (Recommended - Free & Easy)

### **Step 1: Initialize Git Repository**

```bash
cd "/Users/amberuser/Desktop/Whitelabel RAG UCL/WhiteLabel Lead Intelligence"
git init
git add .
git commit -m "Initial commit - UCL Lead Intelligence AI"
```

### **Step 2: Create GitHub Repository**

1. Go to https://github.com/new
2. Create a new repository (e.g., `ucl-lead-intelligence`)
3. **Don't** initialize with README (we already have files)
4. Copy the repository URL

### **Step 3: Push to GitHub**

```bash
git remote add origin https://github.com/YOUR_USERNAME/ucl-lead-intelligence.git
git branch -M main
git push -u origin main
```

### **Step 4: Deploy to Streamlit Cloud**

1. Go to https://share.streamlit.io/
2. Click "New app"
3. Connect your GitHub account
4. Select repository: `ucl-lead-intelligence`
5. Branch: `main`
6. Main file path: `app.py`
7. Click "Deploy!"

### **Step 5: Add Environment Variables**

1. In Streamlit Cloud, go to your app settings
2. Click "Secrets"
3. Add your OpenAI API key:

```toml
OPENAI_API_KEY = "sk-your-key-here"
```

### **Step 6: Configure App**

1. App URL: `https://your-app-name.streamlit.app`
2. Wait for deployment (2-3 minutes)
3. Your app is live! 🎉

---

## 🎯 Option 2: Render (More Control)

### **Step 1-3: Same as above (Git + GitHub)**

### **Step 4: Deploy to Render**

1. Go to https://render.com
2. Sign up/login
3. Click "New +" → "Web Service"
4. Connect GitHub repository
5. Configure:
   - **Name**: `ucl-lead-intelligence`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
6. Add environment variable: `OPENAI_API_KEY`
7. Click "Create Web Service"
8. Wait for deployment (5-10 minutes)

---

## 🎯 Option 3: Railway (Simple & Fast)

### **Step 1-3: Same as above (Git + GitHub)**

### **Step 4: Deploy to Railway**

1. Go to https://railway.app
2. Sign up/login
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway auto-detects Streamlit
6. Add environment variable: `OPENAI_API_KEY`
7. Deploy automatically!

---

## ⚙️ Configuration Files Needed

### **1. Update .gitignore**

Make sure databases are excluded but data files can be included if needed.

### **2. Create .streamlit/config.toml** (Optional)

For Streamlit Cloud configuration:

```toml
[server]
headless = true
port = 8501

[browser]
gatherUsageStats = false
```

### **3. Verify requirements.txt**

Make sure all dependencies are listed.

---

## 🔐 Environment Variables

### **Required**:
- `OPENAI_API_KEY` - Your OpenAI API key

### **Optional** (for production):
- `DATABASE_URL` - If using external database
- `CHROMA_DB_PATH` - If using external vector DB

---

## 📊 Post-Deployment

### **1. Test Your App**

- Visit your app URL
- Test both modes (Detailed & Aggregate)
- Verify queries work
- Check dashboard loads

### **2. Monitor**

- Check Streamlit Cloud logs
- Monitor API usage
- Track errors
- Watch costs

### **3. Share**

- Share URL with stakeholders
- Add to bookmarks
- Set up monitoring alerts

---

## 🐛 Troubleshooting

### **Issue: App won't start**
- Check logs in Streamlit Cloud
- Verify `requirements.txt` is correct
- Check environment variables

### **Issue: API errors**
- Verify `OPENAI_API_KEY` is set
- Check API key is valid
- Monitor API usage limits

### **Issue: Database errors**
- Databases are created on first run
- Check file permissions
- Verify data files are accessible

---

## 💰 Cost Estimates

### **Streamlit Cloud**: FREE
- Unlimited apps
- 1GB RAM per app
- Free tier sufficient for POC

### **OpenAI API**: ~$15-50/month
- Depends on usage
- ~100 queries/day = ~$15/month
- ~1000 queries/day = ~$50/month

### **Total**: ~$15-50/month

---

## ✅ Deployment Checklist

- [ ] Git repository initialized
- [ ] Code pushed to GitHub
- [ ] Streamlit Cloud account created
- [ ] App deployed
- [ ] Environment variables set
- [ ] App tested
- [ ] URL shared with stakeholders

---

## 🚀 Quick Start Commands

```bash
# Initialize Git
git init
git add .
git commit -m "Initial commit"

# Connect to GitHub (replace with your URL)
git remote add origin https://github.com/YOUR_USERNAME/ucl-lead-intelligence.git
git branch -M main
git push -u origin main

# Then deploy via Streamlit Cloud web interface
```

---

**Ready to deploy! Follow the steps above! 🚀**

