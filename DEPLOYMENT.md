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

**สร้างโดย**: AI Product Visualizer Team
**อัพเดทล่าสุด**: 2025-10-18
