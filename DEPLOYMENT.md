# 🚀 Deployment Guide - Streamlit Cloud

## 📋 Prerequisites

1. GitHub account
2. Streamlit Cloud account (free at share.streamlit.io)
3. Google Gemini API key

---

## 🔧 Step-by-Step Deployment

### 1. Prepare Repository

```bash
# Create a new GitHub repository
# Upload these files:
- app.py
- requirements.txt
- packages.txt
- .python-version
- .env.example
- README.md
```

### 2. Configure Streamlit Cloud

1. Go to https://share.streamlit.io
2. Click "New app"
3. Select your repository
4. Main file path: `app.py`
5. Click "Deploy"

### 3. Set Environment Variables

In Streamlit Cloud settings:

1. Go to App Settings → Secrets
2. Add your API key:

```toml
GEMINI_API_KEY = "your_actual_api_key_here"
```

3. Save and redeploy

---

## 📝 Important Files Explained

### requirements.txt
```
streamlit>=1.31.0       # Web framework
playwright>=1.41.0      # Browser automation
google-genai>=0.8.0     # AI analysis
Pillow>=10.0.0          # Image processing
python-dotenv>=1.0.0    # Environment variables
```

### .python-version
```
3.11
```
**Why?** Python 3.13 has compatibility issues with greenlet/playwright.
Streamlit Cloud will use Python 3.11 instead.

### packages.txt
System packages needed by Playwright for browser automation.
These install automatically on Streamlit Cloud.

---

## 🐛 Troubleshooting

### Error: "greenlet build failed"
**Solution:** Make sure `.python-version` file contains `3.11`

### Error: "Browser not found"
**Solution:** Check `packages.txt` is in root directory

### Error: "API key not found"
**Solution:** Add `GEMINI_API_KEY` in Streamlit Cloud Secrets

### Error: "ModuleNotFoundError"
**Solution:** Clear cache and redeploy

---

## 🌐 Alternative: Deploy Locally

```bash
# 1. Clone repository
git clone <your-repo>
cd <your-repo>

# 2. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt
playwright install chromium

# 4. Set API key
cp .env.example .env
# Edit .env and add your API key

# 5. Run app
streamlit run app.py
```

---

## 🔒 Security Notes

**Never commit:**
- `.env` file with real API keys
- Any secrets or credentials

**Always:**
- Use environment variables
- Add `.env` to `.gitignore`
- Use Streamlit Cloud Secrets for deployment

---

## 📊 Streamlit Cloud Secrets Format

```toml
# In Streamlit Cloud → Settings → Secrets
GEMINI_API_KEY = "AIza..."
```

---

## ✅ Deployment Checklist

- [ ] Repository created on GitHub
- [ ] All files uploaded
- [ ] `.python-version` set to 3.11
- [ ] `packages.txt` included
- [ ] API key added to Streamlit Secrets
- [ ] App deployed successfully
- [ ] Test URL and goal settings
- [ ] Verify screenshots work
- [ ] Check AI analysis works

---

## 🎯 Quick Deploy

1. **Fork/Upload** → GitHub
2. **Connect** → Streamlit Cloud
3. **Configure** → Add API key in Secrets
4. **Deploy** → Click deploy button
5. **Test** → Try analyzing a website

---

## 📧 Support

If deployment fails:
1. Check Streamlit Cloud logs
2. Verify Python version is 3.11
3. Ensure all dependencies installed
4. Check API key is set correctly

---

**Built with ❤️ by Team Code_Cracker**
