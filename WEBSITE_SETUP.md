# Website Setup - Quick Reference

## 🚀 Fastest Way to Get Started

### Local (Your Computer)

**Windows:**
```bash
# Double-click this file:
start_dashboard.bat

# Or run in terminal:
streamlit run src/dashboard/app.py
```

**Mac/Linux:**
```bash
# Make script executable (first time only)
chmod +x start_dashboard.sh

# Run script
./start_dashboard.sh

# Or run directly:
streamlit run src/dashboard/app.py
```

**Access:** http://localhost:8501

---

## 🌐 Deploy as Public Website

### Option 1: Streamlit Cloud (Easiest - 5 minutes)

**Perfect for:** Demos, prototypes, small teams  
**Cost:** FREE (or $20/month for private)

**Steps:**
1. Push code to GitHub
2. Go to https://streamlit.io/cloud
3. Sign in with GitHub
4. Click "New app"
5. Select your repo and `src/dashboard/app.py`
6. Add secret: `GOOGLE_API_KEY = "your_key"`
7. Deploy!

**Your URL:** `https://yourusername-ili-alignment.streamlit.app`

**Pros:**
- ✅ Free tier
- ✅ 5-minute setup
- ✅ Auto-updates from GitHub
- ✅ Built-in authentication

---

### Option 2: Google Cloud Run (Best for Production)

**Perfect for:** Production, pay-per-use  
**Cost:** ~$5-20/month (only pay when used)

**Steps:**
```bash
# 1. Install Google Cloud SDK
# Download from: https://cloud.google.com/sdk/docs/install

# 2. Login and set project
gcloud init

# 3. Build and deploy (one command!)
gcloud run deploy ili-alignment \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=your_key_here
```

**Your URL:** Provided by Cloud Run (e.g., `https://ili-alignment-xxxxx.run.app`)

**Pros:**
- ✅ Scales automatically
- ✅ Pay only for usage
- ✅ Custom domains
- ✅ Enterprise-ready

---

### Option 3: Docker (Any Platform)

**Perfect for:** Flexibility, any cloud provider

**Steps:**
```bash
# 1. Build Docker image
docker build -t ili-alignment .

# 2. Run locally to test
docker run -p 8501:8501 -e GOOGLE_API_KEY=your_key ili-alignment

# 3. Deploy to any platform:
# - AWS ECS
# - Azure Container Instances
# - DigitalOcean App Platform
# - Your own server
```

**See DEPLOYMENT_GUIDE.md for detailed instructions**

---

### Option 4: DigitalOcean (Simple & Cheap)

**Perfect for:** Small teams, learning  
**Cost:** $5-12/month

**Steps:**
1. Push code to GitHub
2. Go to https://www.digitalocean.com
3. Create account
4. Click "Create" → "Apps"
5. Connect GitHub repo
6. DigitalOcean auto-detects Dockerfile
7. Add environment variable: `GOOGLE_API_KEY`
8. Deploy!

**Your URL:** Provided by DigitalOcean

---

## 📋 Pre-Deployment Checklist

Before deploying, make sure:

- [ ] Code is pushed to GitHub
- [ ] `.env` file is in `.gitignore` (never commit API keys!)
- [ ] `requirements.txt` is up to date
- [ ] Dashboard works locally (`streamlit run src/dashboard/app.py`)
- [ ] You have your `GOOGLE_API_KEY` ready
- [ ] Sample data files are in `data/` folder

---

## 🔒 Security Setup

### 1. Never Commit API Keys

```bash
# Make sure .env is in .gitignore
echo ".env" >> .gitignore
```

### 2. Use Environment Variables

All platforms support environment variables:
- **Streamlit Cloud:** Advanced settings → Secrets
- **Cloud Run:** `--set-env-vars` flag
- **Docker:** `-e` flag or docker-compose.yml
- **DigitalOcean:** Environment variables section

### 3. Add Authentication (Optional)

For private deployments, add password protection:

```python
# Add to src/dashboard/app.py
import streamlit as st

def check_password():
    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", key="password")
        if st.session_state.get("password") == "your_password":
            st.session_state["password_correct"] = True
            st.rerun()
        return False
    return True

if not check_password():
    st.stop()

# Rest of your app...
```

---

## 🎯 Recommended Setup by Use Case

### For Quick Demo
→ **Streamlit Cloud** (5 minutes, free)

### For Production
→ **Google Cloud Run** (30 minutes, $5-20/month)

### For Learning
→ **DigitalOcean** (15 minutes, $5/month)

### For Enterprise
→ **AWS ECS** (60 minutes, $20-50/month)

---

## 🆘 Troubleshooting

### Dashboard won't start locally

```bash
# Check Python version (need 3.8+)
python --version

# Reinstall dependencies
pip install -r requirements.txt

# Try running directly
cd /path/to/project
streamlit run src/dashboard/app.py
```

### Port 8501 already in use

```bash
# Use different port
streamlit run src/dashboard/app.py --server.port 8502
```

### Module not found errors

```bash
# Make sure you're in project root
cd /path/to/ili-data-alignment-system

# Check if src is in path
python -c "import sys; print(sys.path)"
```

### Docker build fails

```bash
# Check Docker is running
docker --version

# Clean build
docker build --no-cache -t ili-alignment .
```

### Deployment fails

1. Check logs on your platform
2. Verify environment variables are set
3. Ensure Dockerfile is in project root
4. Check that `src/dashboard/app.py` exists

---

## 📞 Getting Help

### Documentation
- **Local Setup:** RUN_DASHBOARD.md
- **Full Deployment:** DEPLOYMENT_GUIDE.md
- **Testing:** TESTING_GUIDE.md
- **Features:** ADVANCED_FEATURES.md

### Platform Support
- **Streamlit:** https://discuss.streamlit.io/
- **Google Cloud:** https://cloud.google.com/support
- **DigitalOcean:** https://www.digitalocean.com/community
- **Docker:** https://forums.docker.com/

---

## 🎉 Next Steps

1. **Choose your deployment option** (see recommendations above)
2. **Test locally first** (`streamlit run src/dashboard/app.py`)
3. **Deploy to your chosen platform**
4. **Share the URL with your team**
5. **Upload your ILI data and start analyzing!**

---

## 💡 Pro Tips

1. **Start with Streamlit Cloud** - It's free and takes 5 minutes
2. **Test with sample data** - Use the files in `data/` folder
3. **Add custom domain** - Makes it look professional
4. **Enable HTTPS** - Most platforms do this automatically
5. **Monitor usage** - Check logs and metrics
6. **Backup database** - Download `ili_system.db` regularly

---

## 📊 What You'll Get

Once deployed, your website will have:

- 📤 **Upload Page** - Upload CSV files
- 🔗 **Matching Page** - View anomaly matches
- 📈 **Growth Page** - Analyze growth rates
- 🎯 **Risk Scoring** - Identify high-risk anomalies
- 📊 **Interactive Charts** - Plotly visualizations
- 💾 **Export** - Download results as CSV
- 🤖 **AI Features** - ML predictions, NLP queries (if API key set)

**All accessible from any web browser!**

---

Ready to deploy? Pick an option above and follow the steps! 🚀
