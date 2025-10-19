# 🚀 Cloud Deployment Guide

## ✅ Ready to Deploy!

โปรเจคนี้พร้อม deploy บน Cloud แล้ว มีไฟล์ครบ:
- ✅ `requirements.txt` - Python dependencies
- ✅ `packages.txt` - System packages (ffmpeg)
- ✅ `.streamlit/config.toml` - Streamlit configuration
- ✅ `.gitignore` - ไม่ push API keys และไฟล์ output

---

## 🌟 วิธีที่ 1: Streamlit Community Cloud (แนะนำ - ฟรี!)

### ขั้นตอน Deploy:

1. **Push โค้ดขึ้น GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit - AI Product Visualizer"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```

2. **ไปที่ Streamlit Community Cloud**
   - เปิด https://share.streamlit.io
   - Login ด้วย GitHub account
   - คลิก "New app"

3. **เลือก Repository และ Branch**
   - Repository: เลือก repo ที่ push ไว้
   - Branch: main
   - Main file path: `main.py`

4. **ตั้งค่า Secrets (API Keys)**

   คลิก "Advanced settings" → "Secrets" แล้วใส่:

   ```toml
   OPENAI_API_KEY = "sk-proj-..."
   REPLICATE_API_TOKEN = "r8_..."
   GEMINI_API_KEY = "AIzaSy..."
   KIE_API_KEY = "kie_..."
   IMGBB_API_KEY = "..."
   ```

5. **Deploy!**
   - คลิก "Deploy"
   - รอประมาณ 2-5 นาที
   - เสร็จแล้วจะได้ URL สำหรับเข้าใช้งาน

### 📝 หมายเหตุ:
- ✅ **ฟรี** สำหรับ public repositories
- ✅ Auto-redeploy เมื่อ push code ใหม่
- ✅ HTTPS และ custom domain รองรับ
- ⚠️ Sleep mode หลัง idle 7 วัน (จะ wake up อัตโนมัติเมื่อมีคนเข้า)

---

## 🐳 วิธีที่ 2: Google Cloud Run (สำหรับ Production)

### 1. สร้าง Dockerfile

สร้างไฟล์ `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Create necessary directories
RUN mkdir -p results/images results/videos data upload_images

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run streamlit
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 2. Build และ Deploy

```bash
# Build image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/ai-product-visualizer

# Deploy to Cloud Run
gcloud run deploy ai-product-visualizer \
  --image gcr.io/YOUR_PROJECT_ID/ai-product-visualizer \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=$OPENAI_API_KEY,REPLICATE_API_TOKEN=$REPLICATE_API_TOKEN,GEMINI_API_KEY=$GEMINI_API_KEY,KIE_API_KEY=$KIE_API_KEY,IMGBB_API_KEY=$IMGBB_API_KEY
```

---

## 🔧 วิธีที่ 3: Railway / Render

### Railway:
1. ไปที่ https://railway.app
2. "New Project" → "Deploy from GitHub repo"
3. เลือก repo
4. Railway จะ auto-detect Streamlit
5. ตั้งค่า Environment Variables (API keys)
6. Deploy!

### Render:
1. ไปที่ https://render.com
2. "New" → "Web Service"
3. Connect GitHub repo
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `streamlit run main.py --server.port=$PORT --server.address=0.0.0.0`
6. ตั้งค่า Environment Variables
7. Deploy!

---

## 🔑 Environment Variables Required

ทุก platform ต้องตั้งค่า:

```
OPENAI_API_KEY=sk-proj-...
REPLICATE_API_TOKEN=r8_...
GEMINI_API_KEY=AIzaSy...
KIE_API_KEY=kie_...
IMGBB_API_KEY=...
```

---

## ✅ ตรวจสอบก่อน Deploy

- [ ] Push code ขึ้น GitHub แล้ว
- [ ] ไม่มี API keys ใน code (ใช้ environment variables เท่านั้น)
- [ ] มีไฟล์ requirements.txt และ packages.txt
- [ ] ทดสอบ local แล้วทำงานได้
- [ ] เตรียม API keys ทั้งหมดไว้แล้ว

---

## 🎯 แนะนำ

**สำหรับ Beginners**: ใช้ **Streamlit Community Cloud** (ฟรี + ง่ายที่สุด)

**สำหรับ Production**: ใช้ **Google Cloud Run** หรือ **Railway** (เสถียรกว่า + ไม่มี sleep mode)

---

## 📞 หากมีปัญหา

1. เช็ค logs ใน platform dashboard
2. ตรวจสอบ API keys ตั้งค่าถูกต้องหรือไม่
3. ดู requirements.txt ว่า dependencies ครบหรือยัง

---

## 📊 Monitoring และ Logging

### Streamlit Community Cloud
```python
# เพิ่มใน main.py เพื่อ track errors
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

try:
    # Your code here
except Exception as e:
    logging.error(f"Error occurred: {str(e)}")
    st.error(f"เกิดข้อผิดพลาด: {str(e)}")
```

- ดู logs: Dashboard → App → Manage app → Logs
- Real-time monitoring ใน terminal

### Google Cloud Run
```bash
# ดู logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=ai-product-visualizer" --limit 50

# Setup alerts
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Error Rate" \
  --condition-threshold-value=10
```

---

## 🐛 Troubleshooting แบบละเอียด

### ปัญหา: App ไม่ขึ้น (500 Error)

**สาเหตุที่พบบ่อย:**

1. **API Keys ไม่ถูกต้อง**
   ```python
   # เพิ่ม validation ใน main.py
   import os

   required_keys = ["OPENAI_API_KEY", "KIE_API_KEY", "GEMINI_API_KEY"]
   missing_keys = [key for key in required_keys if not os.getenv(key)]

   if missing_keys:
       st.error(f"⚠️ Missing API keys: {', '.join(missing_keys)}")
       st.stop()
   ```

2. **Dependencies ขาดหาย**
   - เช็ค `requirements.txt` มี version pinning
   - ลอง `pip install -r requirements.txt` local ก่อน

3. **Memory เกิน**
   ```python
   # ใช้ caching ลด memory
   @st.cache_data(ttl=3600)
   def load_heavy_model():
       return model
   ```

### ปัญหา: FFmpeg ไม่ทำงาน

**แก้ไข:**
```bash
# ใน packages.txt ต้องมี
ffmpeg
libsm6
libxext6
```

**ทดสอบ:**
```python
import subprocess
result = subprocess.run(['ffmpeg', '-version'], capture_output=True)
st.write(result.stdout.decode())
```

### ปัญหา: การสร้างวิดีโอช้า

**Optimization:**
```python
# ใช้ queue system สำหรับ batch processing
from queue import Queue
import threading

video_queue = Queue()

def process_videos():
    while True:
        task = video_queue.get()
        # Process video
        video_queue.task_done()

# Start background thread
threading.Thread(target=process_videos, daemon=True).start()
```

### ปัญหา: Session State หาย

**แก้ไข:**
```python
# ใช้ persistent storage
import json

def save_state(state_dict):
    with open('session_state.json', 'w') as f:
        json.dump(state_dict, f)

def load_state():
    try:
        with open('session_state.json', 'r') as f:
            return json.load(f)
    except:
        return {}
```

---

## 💰 เปรียบเทียบราคา

| Platform | Free Tier | Paid Plan | Best For |
|----------|-----------|-----------|----------|
| **Streamlit Cloud** | ✅ Unlimited public apps | $20/mo (Private apps) | Demos, Personal Projects |
| **Railway** | $5 free credit | $0.000463/GB-hour | Small to Medium Apps |
| **Render** | 750 hrs/mo free | $7/mo (Starter) | Always-on Apps |
| **Google Cloud Run** | 2M requests/mo | Pay-per-use | High Traffic Apps |
| **Heroku** | ❌ No free tier | $7/mo (Eco) | Enterprise Apps |

**คำแนะนำ:**
- 💚 **ใช้ฟรี**: Streamlit Cloud (public repo)
- 💼 **Production เล็ก**: Render Starter ($7/mo)
- 🚀 **Production ใหญ่**: Google Cloud Run (pay-per-use)

---

## 🌐 Custom Domain Setup

### Streamlit Community Cloud (Paid Plan)
1. Settings → Custom subdomain
2. ใส่ `your-app-name` จะได้ `your-app-name.streamlit.app`

### Cloudflare + Render/Railway
1. **ใน Render/Railway**
   - ไปที่ Settings → Custom Domain
   - เพิ่ม `app.yourdomain.com`
   - จดค่า CNAME ที่ได้

2. **ใน Cloudflare**
   - DNS → Add record
   - Type: CNAME
   - Name: app
   - Target: [ค่าที่ได้จาก Render/Railway]
   - Proxy status: Proxied (🟠)

3. **Enable SSL**
   - Cloudflare: SSL/TLS → Full (strict)
   - จะได้ HTTPS อัตโนมัติ

---

## 🔄 CI/CD Setup (Auto-deploy)

### GitHub Actions + Streamlit Cloud

สร้าง `.github/workflows/deploy.yml`:

```yaml
name: Auto Deploy to Streamlit

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest

    - name: Run tests
      run: pytest tests/

    - name: Notify on success
      if: success()
      run: echo "✅ Tests passed! Streamlit Cloud will auto-deploy."
```

### GitHub Actions + Google Cloud Run

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Setup Cloud SDK
      uses: google-github-actions/setup-gcloud@v1
      with:
        service_account_key: ${{ secrets.GCP_SA_KEY }}
        project_id: ${{ secrets.GCP_PROJECT_ID }}

    - name: Build and Deploy
      run: |
        gcloud builds submit --tag gcr.io/${{ secrets.GCP_PROJECT_ID }}/ai-product-visualizer
        gcloud run deploy ai-product-visualizer \
          --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/ai-product-visualizer \
          --platform managed \
          --region asia-southeast1 \
          --allow-unauthenticated
```

---

## 💾 Backup Strategy

### 1. Code Backup (Git)
```bash
# Always push to GitHub
git add .
git commit -m "Daily backup"
git push origin main

# Tag important releases
git tag -a v1.0.0 -m "Production release"
git push --tags
```

### 2. Data Backup

**สร้างไฟล์ `backup.py`:**

```python
import shutil
import datetime
import os

def backup_data():
    """Backup data และ results folders"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{timestamp}"

    # Backup folders
    folders_to_backup = ['data', 'results', 'upload_images']

    for folder in folders_to_backup:
        if os.path.exists(folder):
            shutil.copytree(folder, f"backups/{backup_name}/{folder}")

    print(f"✅ Backup created: {backup_name}")

if __name__ == "__main__":
    backup_data()
```

**Schedule backup (Linux/Mac):**
```bash
# Add to crontab
0 2 * * * cd /path/to/project && python backup.py
```

### 3. Database Backup (ถ้ามี)
```python
import sqlite3
import shutil

def backup_database():
    """Backup SQLite database"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2('data/database.db', f'backups/database_{timestamp}.db')
```

---

## 🔒 Security Best Practices

### 1. API Keys Protection

**❌ อย่าทำ:**
```python
OPENAI_API_KEY = "sk-proj-abc123..."  # Hard-coded
```

**✅ ทำแบบนี้:**
```python
import os
from dotenv import load_dotenv

load_dotenv()  # Load from .env file (local only)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # From environment
```

### 2. Rate Limiting

```python
import streamlit as st
from datetime import datetime, timedelta

# Simple rate limiting
if 'last_request_time' not in st.session_state:
    st.session_state.last_request_time = {}

def rate_limit(user_id, max_requests=10, window_minutes=60):
    """Limit requests per user"""
    now = datetime.now()

    if user_id not in st.session_state.last_request_time:
        st.session_state.last_request_time[user_id] = []

    # Remove old requests
    st.session_state.last_request_time[user_id] = [
        t for t in st.session_state.last_request_time[user_id]
        if now - t < timedelta(minutes=window_minutes)
    ]

    # Check limit
    if len(st.session_state.last_request_time[user_id]) >= max_requests:
        return False

    st.session_state.last_request_time[user_id].append(now)
    return True
```

### 3. Input Validation

```python
import re

def validate_input(text, max_length=1000):
    """Validate user input"""
    # Check length
    if len(text) > max_length:
        raise ValueError(f"Input too long (max {max_length} characters)")

    # Check for malicious patterns
    dangerous_patterns = [
        r'<script',
        r'javascript:',
        r'onerror=',
        r'eval\(',
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            raise ValueError("Potentially malicious input detected")

    return text
```

### 4. HTTPS Only

```toml
# .streamlit/config.toml
[server]
enableXsrfProtection = true
enableCORS = false

[browser]
gatherUsageStats = false
```

---

## 📈 Performance Optimization

### 1. Caching Strategies

```python
import streamlit as st

# Cache data loading (1 hour)
@st.cache_data(ttl=3600)
def load_templates():
    """Cache product templates"""
    return pd.read_csv('data/templates.csv')

# Cache resource (persist across reruns)
@st.cache_resource
def load_ai_model():
    """Cache AI model (only load once)"""
    return pipeline("text-generation", model="gpt2")

# Clear cache button
if st.sidebar.button("🔄 Clear Cache"):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.success("Cache cleared!")
```

### 2. Lazy Loading

```python
def lazy_load_images():
    """Load images only when needed"""
    if 'images' not in st.session_state:
        st.session_state.images = None

    if st.button("Load Images") and st.session_state.images is None:
        with st.spinner("Loading..."):
            st.session_state.images = load_large_dataset()
```

### 3. Optimize Video Processing

```python
# Use lower quality for preview
def create_preview_video(images, quality='low'):
    """Create preview video with lower quality"""
    if quality == 'low':
        return create_video(images, fps=15, resolution=(640, 360))
    else:
        return create_video(images, fps=30, resolution=(1920, 1080))
```

### 4. Background Processing

```python
import concurrent.futures

def process_multiple_products(products):
    """Process multiple products in parallel"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(process_product, p) for p in products]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    return results
```

---

## 📱 Mobile Optimization

```python
import streamlit as st

# Detect mobile
def is_mobile():
    """Detect if user is on mobile device"""
    return st.session_state.get('mobile', False)

# Responsive layout
if is_mobile():
    st.write("📱 Mobile view")
    col1, = st.columns(1)
else:
    st.write("💻 Desktop view")
    col1, col2, col3 = st.columns(3)
```

**CSS สำหรับ Mobile:**
```python
st.markdown("""
<style>
@media (max-width: 768px) {
    .stButton > button {
        width: 100%;
        margin-bottom: 10px;
    }
    .stTextInput > div > div > input {
        font-size: 16px !important;
    }
}
</style>
""", unsafe_allow_html=True)
```

---

## 🎓 Best Practices Checklist

### Pre-deployment
- [ ] ทดสอบทุก feature ใน local environment
- [ ] เช็ค error handling ทุก function
- [ ] ใส่ loading states สำหรับ async operations
- [ ] Validate user inputs
- [ ] ใส่ rate limiting
- [ ] เตรียม fallback สำหรับ API failures
- [ ] Test บน mobile device

### Post-deployment
- [ ] Monitor logs ใน 24 ชั่วโมงแรก
- [ ] ทดสอบ performance ด้วย real users
- [ ] Setup error alerting
- [ ] เตรียม backup plan
- [ ] Document API usage และ costs
- [ ] Setup analytics (optional)

### Maintenance
- [ ] Update dependencies ทุกเดือน
- [ ] Review และ optimize costs
- [ ] Backup data ทุกสัปดาห์
- [ ] Monitor API rate limits
- [ ] Review และ respond to errors
- [ ] Test disaster recovery plan

---

## 🆘 Emergency Contacts

### หาก app crash
1. เช็ค status: https://status.streamlit.io
2. ดู logs ใน platform dashboard
3. Rollback ไป commit ก่อนหน้า:
   ```bash
   git revert HEAD
   git push origin main
   ```

### หาก API keys หลุด
1. **Revoke keys ทันที** ที่ provider dashboard
2. Generate keys ใหม่
3. Update ใน environment variables
4. Redeploy app
5. Monitor unusual activity

### หาก costs สูงผิดปกติ
1. เช็ค usage dashboard
2. Enable cost alerts:
   ```bash
   # Google Cloud
   gcloud billing budgets create \
     --billing-account=BILLING_ACCOUNT_ID \
     --display-name="Monthly Budget" \
     --budget-amount=100USD
   ```
3. Review และ optimize API calls

---

## 🎯 Quick Start Commands

```bash
# Development
streamlit run main.py

# Test
pytest tests/

# Backup
python backup.py

# Deploy (Streamlit Cloud)
git push origin main  # Auto-deploy

# Deploy (Google Cloud Run)
gcloud run deploy

# View logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# Rollback
git revert HEAD && git push
```

---

## 📚 Resources

- [Streamlit Docs](https://docs.streamlit.io)
- [Google Cloud Run Docs](https://cloud.google.com/run/docs)
- [Railway Docs](https://docs.railway.app)
- [Render Docs](https://render.com/docs)
- [FFmpeg Guide](https://ffmpeg.org/documentation.html)

---

**สร้างโดย**: AI Product Visualizer Team
**อัพเดทล่าสุด**: 2025-10-19
**Version**: 2.0 - Extended Guide
