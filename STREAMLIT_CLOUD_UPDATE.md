# 🚀 Streamlit Cloud Auto-Update Guide

## ✅ Yes, Your Streamlit URL Will Auto-Update!

If you've deployed your app to **Streamlit Cloud** (share.streamlit.io or streamlit.io), it will **automatically update** when you push to GitHub.

---

## 🔄 How Streamlit Cloud Auto-Deployment Works

### **Automatic Deployment** (Default Behavior):
1. ✅ **Connected to GitHub**: Your Streamlit Cloud app is linked to your GitHub repo
2. ✅ **Watches Main Branch**: It monitors the `main` branch for changes
3. ✅ **Auto-Deploys**: When you push to `main`, Streamlit Cloud automatically:
   - Detects the new commit
   - Pulls the latest code
   - Rebuilds the app
   - Deploys the new version
   - Your URL stays the same, but content updates!

### **Deployment Process**:
```
You push to GitHub → Streamlit Cloud detects → Rebuilds → Deploys → URL updates
```

---

## ⏱️ Update Timeline

- **Detection**: Usually within 1-2 minutes of push
- **Rebuild**: Takes 2-5 minutes (depends on dependencies)
- **Deploy**: New version goes live automatically
- **Total**: ~3-7 minutes from push to live update

---

## 🔍 How to Check if Auto-Update is Enabled

1. **Go to Streamlit Cloud Dashboard**: https://share.streamlit.io
2. **Select Your App**
3. **Check Settings**:
   - ✅ "Auto-redeploy" should be **ON**
   - ✅ "Branch" should be set to **`main`**
   - ✅ "Repository" should match your GitHub repo

---

## 🛠️ Manual Redeploy (If Needed)

If auto-update doesn't work:

1. **Streamlit Cloud Dashboard**:
   - Go to your app
   - Click "⋮" (three dots) menu
   - Select "Redeploy"

2. **Or via Command** (if using Streamlit CLI):
   ```bash
   streamlit deploy
   ```

---

## ⚠️ Important Notes

### **What Gets Updated**:
- ✅ All Python code changes
- ✅ All configuration changes
- ✅ All documentation updates
- ✅ New dependencies (if `requirements.txt` changes)

### **What Doesn't Auto-Update**:
- ❌ **Environment Variables** (`.env` file):
  - Must be set manually in Streamlit Cloud dashboard
  - Go to: App Settings → Secrets → Add secrets
  - Add: `OPENAI_API_KEY=your_key_here`

- ❌ **Database Files**:
  - SQLite databases (`.db` files) are not in git
  - Will be created fresh on first run
  - **You may need to re-run data ingestion** after deployment

- ❌ **ChromaDB Files**:
  - Vector embeddings are not in git (too large)
  - Will be created fresh on first run
  - **You may need to re-run RAG embedding creation** after deployment

---

## 📋 Post-Deployment Checklist

After pushing to GitHub, verify:

1. ✅ **App rebuilds automatically** (check Streamlit Cloud dashboard)
2. ✅ **Environment variables are set** (OPENAI_API_KEY in secrets)
3. ✅ **Database is initialized** (run data ingestion if needed)
4. ✅ **RAG embeddings created** (run RAG system if needed)
5. ✅ **App works correctly** (test a few queries)

---

## 🔧 Setting Up Environment Variables in Streamlit Cloud

1. Go to: https://share.streamlit.io
2. Select your app
3. Click "⚙️ Settings" → "Secrets"
4. Add:
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   AUTH_USERNAME=admin
   AUTH_PASSWORD=your-secure-password
   ```

---

## 🚨 Troubleshooting

### **App Not Updating?**
- Check Streamlit Cloud dashboard for build errors
- Verify branch is set to `main`
- Check if auto-redeploy is enabled
- Manually trigger redeploy if needed

### **App Crashes After Update?**
- Check build logs in Streamlit Cloud
- Verify all dependencies in `requirements.txt`
- Check environment variables are set
- Verify database files exist (may need to re-run ingestion)

### **Missing Data After Update?**
- Database files (`.db`) are not in git
- You need to run data ingestion after deployment:
  ```python
  # In Streamlit Cloud, add to app.py or run separately
  from src.init_databases import ensure_databases_exist
  ensure_databases_exist()
  ```

---

## ✅ Summary

**Your Streamlit URL will automatically update** when you push to GitHub, but:

1. ✅ Code changes → Auto-update ✅
2. ⚠️ Environment variables → Manual setup required
3. ⚠️ Database files → May need re-initialization
4. ⚠️ ChromaDB files → May need re-creation

**Best Practice**: Set up a startup script in your app that checks and initializes databases if they don't exist.

---

**Your app should be updating now!** Check your Streamlit Cloud dashboard to see the deployment status. 🚀

