# 🚀 Deployment Guide

## Streamlit Cloud (Recommended)

### 1. Push to GitHub

```bash
git add .
git commit -m "Deploy to Streamlit Cloud"
git push origin main
```

### 2. Deploy

1. Go to https://share.streamlit.io/
2. Click "New app"
3. Connect GitHub repository
4. Select branch: `main`
5. Main file: `app.py`
6. Click "Deploy"

### 3. Add API Key

In Streamlit Cloud → App Settings → Secrets:

```toml
OPENAI_API_KEY = "sk-your-key-here"
```

### 4. Wait for Deployment

Takes 2-3 minutes. App will be live at `https://your-app.streamlit.app`

## Alternative: Render

1. Go to https://render.com
2. New Web Service → Connect GitHub
3. Configure:
   - Build: `pip install -r requirements.txt`
   - Start: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
4. Add environment variable: `OPENAI_API_KEY`
5. Deploy

## Post-Deployment

- Test queries work
- Check database initialization
- Monitor API usage
- Share URL with stakeholders

## Troubleshooting

**App won't start**
- Check logs in deployment dashboard
- Verify `requirements.txt` is correct
- Check environment variables

**Database errors**
- Databases auto-create on first run
- Check file permissions
- Verify data files are accessible

## Cost

- **Streamlit Cloud**: FREE
- **OpenAI API**: ~$15-50/month (depends on usage)
