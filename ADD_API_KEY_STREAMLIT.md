# 🔑 How to Add OpenAI API Key in Streamlit Cloud

> **Step-by-step guide to add your API key**

---

## 📋 Quick Steps (2 minutes)

### **Step 1: Go to Your App Settings**

1. Visit: https://share.streamlit.io/
2. Sign in with your GitHub account
3. Find your app: **UCL-Lead-Intelligence**
4. Click on your app name or the **"Manage app"** button (gear icon)

---

### **Step 2: Open Secrets**

1. In the app management page, look for **"Secrets"** in the left sidebar
2. Click on **"Secrets"**
3. You'll see a text editor

---

### **Step 3: Add Your API Key**

**In the text editor, paste this**:

```toml
OPENAI_API_KEY = "sk-your-actual-api-key-here"
```

**Important**:
- Replace `sk-your-actual-api-key-here` with your **actual OpenAI API key**
- Keep the quotes around the key
- Make sure there's a space before and after the `=`

**Example** (don't use this, use your own key):
```toml
OPENAI_API_KEY = "sk-proj-abc123xyz789..."
```

---

### **Step 4: Save**

1. Click **"Save"** button at the bottom
2. Streamlit Cloud will automatically redeploy your app
3. Wait 1-2 minutes for redeployment

---

### **Step 5: Test**

1. Go back to your app URL
2. Refresh the page
3. The error should be gone
4. Test a query: "How many total leads?"

---

## 🎯 Visual Guide

```
Streamlit Cloud Dashboard
  ↓
Your App (UCL-Lead-Intelligence)
  ↓
"Manage app" (gear icon) or click app name
  ↓
Left Sidebar → "Secrets"
  ↓
Text Editor → Paste your key
  ↓
Click "Save"
  ↓
Wait for redeployment (1-2 min)
  ↓
Refresh app → Should work! ✅
```

---

## 🔍 Where to Find Your OpenAI API Key

### **If you don't have one yet**:

1. Go to: https://platform.openai.com/api-keys
2. Sign in or create account
3. Click **"Create new secret key"**
4. Copy the key (starts with `sk-`)
5. **Save it somewhere safe** - you won't see it again!

### **If you already have one**:

1. Check your `.env` file locally (if you have one)
2. Or check your OpenAI account: https://platform.openai.com/api-keys
3. Create a new one if needed

---

## ⚠️ Important Notes

### **Security**:
- ✅ API keys in Streamlit Secrets are **encrypted and secure**
- ✅ Only you can see them
- ✅ Never share your API key publicly
- ✅ Never commit API keys to GitHub

### **Format**:
- Must be in TOML format
- Key name: `OPENAI_API_KEY` (all caps)
- Value: Your key in quotes
- Example: `OPENAI_API_KEY = "sk-..."`

---

## 🐛 Troubleshooting

### **Issue: "Invalid API key"**
- **Check**: Make sure you copied the entire key
- **Check**: Make sure there are quotes around the key
- **Check**: Make sure there's a space before and after `=`

### **Issue: App still shows error after saving**
- **Wait**: Give it 1-2 minutes to redeploy
- **Refresh**: Hard refresh the app page (Ctrl+R or Cmd+R)
- **Check**: Verify the key is saved in Secrets

### **Issue: Can't find Secrets option**
- **Check**: Make sure you're the app owner
- **Check**: You're in "Manage app" view, not just viewing the app

---

## ✅ Verification

**After adding the key, you should see**:
- ✅ No error message
- ✅ App loads normally
- ✅ Dashboard shows metrics
- ✅ Can ask questions
- ✅ Both modes work

---

## 📝 Quick Copy-Paste Template

Copy this and replace with your key:

```toml
OPENAI_API_KEY = "paste-your-key-here"
```

---

## 🎯 Summary

1. **Go to**: Streamlit Cloud → Your App → Manage app
2. **Click**: "Secrets" in sidebar
3. **Paste**: `OPENAI_API_KEY = "your-key-here"`
4. **Save**: Click "Save" button
5. **Wait**: 1-2 minutes for redeployment
6. **Test**: Refresh app and try a query

---

**That's it! Your app should work now! 🚀**

---

*Guide Created: November 13, 2025*  
*Status: Ready to use*






