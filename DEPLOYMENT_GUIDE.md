# ILI Data Alignment System - Deployment Guide

This guide covers multiple options for deploying the system as a website.

---

## Option 1: Streamlit Cloud (Easiest - Free)

**Best for:** Quick demos, prototypes, small teams  
**Cost:** Free for public apps, $20/month for private  
**Setup time:** 5-10 minutes

### Steps

1. **Push code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/ili-alignment.git
   git push -u origin main
   ```

2. **Sign up for Streamlit Cloud**
   - Go to https://streamlit.io/cloud
   - Sign in with GitHub
   - Click "New app"

3. **Deploy**
   - Select your repository
   - Set main file path: `src/dashboard/app.py`
   - Add secrets (for GOOGLE_API_KEY):
     - Click "Advanced settings"
     - Add secrets in TOML format:
       ```toml
       GOOGLE_API_KEY = "your_key_here"
       ```
   - Click "Deploy"

4. **Access your app**
   - Your app will be at: `https://yourusername-ili-alignment.streamlit.app`
   - Share this URL with your team

### Pros
- ✅ Easiest deployment
- ✅ Free tier available
- ✅ Automatic updates from GitHub
- ✅ Built-in authentication
- ✅ No server management

### Cons
- ❌ Limited resources (1 GB RAM on free tier)
- ❌ Public by default (unless paid)
- ❌ Streamlit branding

---

## Option 2: Docker + Cloud Platform (Recommended for Production)

**Best for:** Production deployments, enterprise use  
**Cost:** $5-50/month depending on platform  
**Setup time:** 30-60 minutes

### Step 1: Create Dockerfile

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
CMD ["streamlit", "run", "src/dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Step 2: Create .dockerignore

Create `.dockerignore`:

```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
.git
.gitignore
.pytest_cache
.coverage
htmlcov/
*.egg-info/
.env
output/
models/
*.db
```

### Step 3: Test locally

```bash
# Build image
docker build -t ili-alignment .

# Run container
docker run -p 8501:8501 -e GOOGLE_API_KEY=your_key_here ili-alignment

# Access at http://localhost:8501
```

### Step 4: Deploy to Cloud Platform

#### Option A: AWS (Elastic Container Service)

1. **Install AWS CLI**
   ```bash
   pip install awscli
   aws configure
   ```

2. **Create ECR repository**
   ```bash
   aws ecr create-repository --repository-name ili-alignment
   ```

3. **Push Docker image**
   ```bash
   # Login to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
   
   # Tag image
   docker tag ili-alignment:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/ili-alignment:latest
   
   # Push image
   docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/ili-alignment:latest
   ```

4. **Create ECS service**
   - Go to AWS ECS console
   - Create cluster
   - Create task definition (use your ECR image)
   - Create service
   - Configure load balancer
   - Add environment variables (GOOGLE_API_KEY)

5. **Access your app**
   - Use the load balancer DNS name
   - Optionally add custom domain with Route 53

**Cost:** ~$20-50/month (Fargate)

#### Option B: Google Cloud Run (Easiest Cloud Option)

1. **Install Google Cloud SDK**
   ```bash
   # Download from https://cloud.google.com/sdk/docs/install
   gcloud init
   ```

2. **Build and deploy**
   ```bash
   # Set project
   gcloud config set project YOUR_PROJECT_ID
   
   # Build image
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/ili-alignment
   
   # Deploy to Cloud Run
   gcloud run deploy ili-alignment \
     --image gcr.io/YOUR_PROJECT_ID/ili-alignment \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars GOOGLE_API_KEY=your_key_here
   ```

3. **Access your app**
   - Cloud Run provides a URL: `https://ili-alignment-xxxxx-uc.a.run.app`
   - Add custom domain if needed

**Cost:** ~$5-20/month (pay per use)

#### Option C: Azure Container Instances

1. **Install Azure CLI**
   ```bash
   # Download from https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
   az login
   ```

2. **Create container registry**
   ```bash
   az acr create --resource-group myResourceGroup --name iliregistry --sku Basic
   ```

3. **Push image**
   ```bash
   az acr login --name iliregistry
   docker tag ili-alignment iliregistry.azurecr.io/ili-alignment:latest
   docker push iliregistry.azurecr.io/ili-alignment:latest
   ```

4. **Deploy container**
   ```bash
   az container create \
     --resource-group myResourceGroup \
     --name ili-alignment \
     --image iliregistry.azurecr.io/ili-alignment:latest \
     --dns-name-label ili-alignment \
     --ports 8501 \
     --environment-variables GOOGLE_API_KEY=your_key_here
   ```

5. **Access your app**
   - URL: `http://ili-alignment.region.azurecontainer.io:8501`

**Cost:** ~$10-30/month

#### Option D: DigitalOcean App Platform (Simple)

1. **Push to GitHub** (if not already done)

2. **Create DigitalOcean account**
   - Go to https://www.digitalocean.com

3. **Create new app**
   - Click "Create" → "Apps"
   - Connect GitHub repository
   - Select branch
   - DigitalOcean auto-detects Dockerfile

4. **Configure**
   - Add environment variable: `GOOGLE_API_KEY`
   - Choose plan ($5-12/month)
   - Deploy

5. **Access your app**
   - DigitalOcean provides URL
   - Add custom domain if needed

**Cost:** $5-12/month

---

## Option 3: Traditional VPS (Full Control)

**Best for:** Custom requirements, full control  
**Cost:** $5-20/month  
**Setup time:** 1-2 hours

### Steps

1. **Get a VPS**
   - DigitalOcean Droplet ($5/month)
   - AWS EC2 t2.micro ($8/month)
   - Linode ($5/month)
   - Vultr ($5/month)

2. **SSH into server**
   ```bash
   ssh root@your-server-ip
   ```

3. **Install dependencies**
   ```bash
   # Update system
   apt update && apt upgrade -y
   
   # Install Python
   apt install python3.10 python3-pip -y
   
   # Install nginx (reverse proxy)
   apt install nginx -y
   
   # Install supervisor (process manager)
   apt install supervisor -y
   ```

4. **Clone repository**
   ```bash
   cd /opt
   git clone https://github.com/yourusername/ili-alignment.git
   cd ili-alignment
   ```

5. **Install Python dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

6. **Create .env file**
   ```bash
   echo "GOOGLE_API_KEY=your_key_here" > .env
   ```

7. **Configure Supervisor**
   
   Create `/etc/supervisor/conf.d/ili-alignment.conf`:
   ```ini
   [program:ili-alignment]
   directory=/opt/ili-alignment
   command=/usr/local/bin/streamlit run src/dashboard/app.py --server.port=8501 --server.address=0.0.0.0
   autostart=true
   autorestart=true
   stderr_logfile=/var/log/ili-alignment.err.log
   stdout_logfile=/var/log/ili-alignment.out.log
   environment=GOOGLE_API_KEY="your_key_here"
   ```

8. **Start application**
   ```bash
   supervisorctl reread
   supervisorctl update
   supervisorctl start ili-alignment
   ```

9. **Configure Nginx**
   
   Create `/etc/nginx/sites-available/ili-alignment`:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

10. **Enable site**
    ```bash
    ln -s /etc/nginx/sites-available/ili-alignment /etc/nginx/sites-enabled/
    nginx -t
    systemctl restart nginx
    ```

11. **Add SSL (optional but recommended)**
    ```bash
    apt install certbot python3-certbot-nginx -y
    certbot --nginx -d your-domain.com
    ```

12. **Access your app**
    - HTTP: `http://your-domain.com`
    - HTTPS: `https://your-domain.com`

---

## Option 4: Heroku (Simple but Deprecated)

**Note:** Heroku removed free tier in 2022. Paid plans start at $7/month.

### Steps

1. **Install Heroku CLI**
   ```bash
   # Download from https://devcenter.heroku.com/articles/heroku-cli
   heroku login
   ```

2. **Create Procfile**
   
   Create `Procfile` in project root:
   ```
   web: streamlit run src/dashboard/app.py --server.port=$PORT --server.address=0.0.0.0
   ```

3. **Create setup.sh**
   
   Create `setup.sh`:
   ```bash
   mkdir -p ~/.streamlit/
   
   echo "\
   [server]\n\
   headless = true\n\
   port = $PORT\n\
   enableCORS = false\n\
   \n\
   " > ~/.streamlit/config.toml
   ```

4. **Deploy**
   ```bash
   heroku create ili-alignment
   heroku config:set GOOGLE_API_KEY=your_key_here
   git push heroku main
   ```

5. **Access your app**
   - URL: `https://ili-alignment.herokuapp.com`

**Cost:** $7/month (Eco Dynos)

---

## Comparison Table

| Option | Cost/Month | Setup Time | Difficulty | Best For |
|--------|-----------|------------|------------|----------|
| Streamlit Cloud | Free-$20 | 5 min | ⭐ Easy | Demos, prototypes |
| Google Cloud Run | $5-20 | 30 min | ⭐⭐ Medium | Production, pay-per-use |
| DigitalOcean App | $5-12 | 15 min | ⭐⭐ Medium | Small teams |
| AWS ECS | $20-50 | 60 min | ⭐⭐⭐ Hard | Enterprise |
| VPS (DigitalOcean) | $5-20 | 120 min | ⭐⭐⭐ Hard | Full control |
| Heroku | $7+ | 20 min | ⭐⭐ Medium | Quick deploy |

---

## Recommended Approach

### For Quick Demo
**Use Streamlit Cloud** - Deploy in 5 minutes, free tier available

### For Production
**Use Google Cloud Run** - Scalable, pay-per-use, easy to manage

### For Enterprise
**Use AWS ECS** - Full control, enterprise features, compliance

### For Learning
**Use VPS** - Learn server management, full control

---

## Security Considerations

### 1. Environment Variables
Never commit `.env` file or API keys to Git:
```bash
# Add to .gitignore
echo ".env" >> .gitignore
```

### 2. Authentication
Add authentication to Streamlit:

```python
# In src/dashboard/app.py
import streamlit as st

def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        return True

if check_password():
    # Your app code here
    st.title("ILI Data Alignment System")
```

### 3. HTTPS
Always use HTTPS in production:
- Streamlit Cloud: Automatic
- Cloud platforms: Usually automatic
- VPS: Use Let's Encrypt (certbot)

### 4. Database Security
If using SQLite in production:
- Store database file outside web root
- Regular backups
- Consider PostgreSQL for multi-user

---

## Monitoring & Maintenance

### Health Checks
Add health check endpoint:

```python
# In src/dashboard/app.py
import streamlit as st

# Streamlit has built-in health check at /_stcore/health
# No additional code needed
```

### Logging
Configure logging:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### Backups
Backup database regularly:

```bash
# Cron job for daily backups
0 2 * * * cp /opt/ili-alignment/ili_system.db /backups/ili_system_$(date +\%Y\%m\%d).db
```

---

## Custom Domain

### Add Custom Domain

1. **Buy domain** (Namecheap, GoDaddy, Google Domains)

2. **Configure DNS**
   - Add A record pointing to your server IP
   - Or CNAME record pointing to cloud platform URL

3. **Update platform settings**
   - Streamlit Cloud: Add custom domain in settings
   - Cloud Run: Map custom domain in console
   - VPS: Update nginx config

4. **Add SSL**
   - Most platforms: Automatic
   - VPS: Use certbot

---

## Scaling Considerations

### For High Traffic

1. **Use load balancer**
   - AWS: Application Load Balancer
   - GCP: Cloud Load Balancing
   - Azure: Load Balancer

2. **Add caching**
   - Redis for session data
   - CDN for static assets

3. **Database**
   - Migrate from SQLite to PostgreSQL
   - Use managed database service

4. **Horizontal scaling**
   - Run multiple instances
   - Use container orchestration (Kubernetes)

---

## Cost Optimization

### Tips to Reduce Costs

1. **Use spot instances** (AWS, GCP)
2. **Auto-scaling** - Scale down during off-hours
3. **Reserved instances** - Commit for 1-3 years
4. **Optimize Docker image** - Use slim base images
5. **CDN** - Cache static assets
6. **Compression** - Enable gzip

---

## Next Steps

1. **Choose deployment option** based on your needs
2. **Test locally** with Docker
3. **Deploy to staging** environment
4. **Test thoroughly**
5. **Deploy to production**
6. **Monitor and maintain**

---

## Support

For deployment issues:
- Streamlit: https://discuss.streamlit.io/
- Docker: https://forums.docker.com/
- Cloud platforms: Check their documentation

For application issues:
- See TESTING_GUIDE.md
- Check logs
- Review error messages
