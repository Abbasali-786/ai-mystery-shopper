# 🚀 Streamlit Cloud Deployment Guide

## Quick Deploy Checklist

### ✅ Required Files (Must be in root):
- [ ] `app.py` - Main application
- [ ] `requirements.txt` - Python dependencies  
- [ ] `packages.txt` - System dependencies (for Playwright)
- [ ] `.python-version` - Set to `3.11`
- [ ] `.env.example` - API key template

### 📋 Step-by-Step Deployment

#### 1. Prepare Repository
```bash
# Upload these files to GitHub root directory:
app.py
requirements.txt
packages.txt
.python-version
.env.example
README.md
```

#### 2. Deploy on Streamlit Cloud

1. Go to **https://share.streamlit.io**
2. Click **"New app"**
3. Connect your **GitHub repository**
4. Set:
   - **Main file path:** `app.py`
   - **Python version:** Auto (uses .python-version file)
5. Click **"Deploy"**

#### 3. Configure Secrets

In Streamlit Cloud App Settings → **Secrets**, add:

```toml
GEMINI_API_KEY = "your_actual_api_key_here"
```

Get your API key from: https://aistudio.google.com/app/apikey

#### 4. Wait for Installation

**First deployment takes 3-5 minutes** because:
- Installing Python packages (~1 min)
- Installing system dependencies (~1 min)  
- **Installing Playwright browser (~2 min)** ← Important!
- Building app

**Don't worry if you see:**
- "Installing browser for first-time use..."
- Loading messages
- Progress indicators

This is **normal** and happens **only once**!

---

## 🐛 Common Issues & Solutions

### Issue 1: "Executable doesn't exist"

**Cause:** Playwright browser not installed

**Solution:**
1. ✅ Ensure `packages.txt` is in root directory
2. ✅ Wait 2-3 minutes for auto-installation
3. ✅ Check logs for "Installing browser..."
4. If still failing, **redeploy the app**

**Files to check:**
```
packages.txt (must contain system libs)
.python-version (must be 3.11)
```

### Issue 2: "greenlet build failed"

**Cause:** Python 3.13 incompatibility

**Solution:**
Create `.python-version` file with content:
```
3.11
```

### Issue 3: "API key not found"

**Solution:**
1. Go to App Settings → Secrets
2. Add `GEMINI_API_KEY = "your_key"`
3. Click "Save"
4. Restart app

### Issue 4: "429 RESOURCE_EXHAUSTED"

**Cause:** API quota exceeded (Free tier limits)

**Solution:**
- Wait 1 hour (rate limit reset)
- OR get new API key
- OR reduce max steps to 2-3

---

## 📁 Required File Structure

```
your-repo/
├── app.py                    ✅ Main app
├── requirements.txt          ✅ Python deps
├── packages.txt             ✅ System deps (CRITICAL!)
├── .python-version          ✅ Python 3.11
├── .env.example             ✅ Template
├── README.md                ✅ Documentation
├── DEPLOYMENT.md            ⚪ Optional
└── .gitignore               ⚪ Optional
```

---

## 🔍 Verify Deployment

After deployment, check:

1. **App loads** ✅
2. **No installation errors** ✅
3. **Can enter URL** ✅
4. **Analysis starts** ✅
5. **Screenshots appear** ✅

---

## 💡 Pro Tips

### Faster Deployment:
- Keep `max_steps` at 3-4 for testing
- Use simple websites first (google.com)
- Check logs if errors occur

### API Quota Management:
- Free tier: 15 req/min, 1500 req/day
- Each run = ~12 API calls
- Test locally before deploying

### Monitoring:
- Check Streamlit Cloud logs
- Watch for browser installation messages
- Monitor API usage

---

## 🆘 Still Having Issues?

### Check These:

1. **Files in root?** ✅
   ```
   ls -la
   # Should show: app.py, requirements.txt, packages.txt, .python-version
   ```

2. **packages.txt correct?** ✅
   ```
   libnss3
   libnspr4
   libatk1.0-0
   # ... (21 packages total)
   ```

3. **Python version?** ✅
   ```
   cat .python-version
   # Should show: 3.11
   ```

4. **API key set?** ✅
   - Go to App Settings → Secrets
   - Verify GEMINI_API_KEY is there

---

## 📊 Expected First Run

```
🔄 Installing browser for first-time use...
⏳ This may take 1-2 minutes
📦 Installing Playwright browsers...
✅ Browser installed successfully!
🚀 Loading: https://example.com
📸 Step 1: Analyzing...
🤖 Step 1: CLICK - Accept Cookies
✅ Analysis complete!
```

---

## 🎯 Quick Test

After deployment, test with:

- **URL:** `https://google.com`
- **Goal:** `Navigate to sign-in page`
- **Max Steps:** `3`

Should complete in ~30 seconds!

---

## 📧 Support Resources

- **Streamlit Docs:** https://docs.streamlit.io
- **Playwright Docs:** https://playwright.dev
- **Gemini API:** https://ai.google.dev

---

**Built with ❤️ by Team Code_Cracker**

*For local deployment, see DEPLOYMENT.md*
