# 🎨 AI Product Visualizer

โปรเจกต์สร้างภาพโฆษณาสินค้าด้วย AI และรวมเป็นวิดีโอโฆษณาแนวสั้น

## ✨ Features

- 🧠 **Dual AI Engine**: เลือกระหว่าง DALL-E 3 หรือ Stable Diffusion XL
  - **DALL-E 3**: สร้างภาพจาก prompt โดยตรง
  - **Stable Diffusion XL**: ใช้รูปสินค้าจริงเป็น reference (แม่นยำกว่า)
- 📤 **อัปโหลดรูปสินค้า**: รองรับไฟล์ .png, .jpg หลายไฟล์
- 🤖 **สร้างภาพด้วย AI**: ใช้ AI สร้างภาพนายแบบ/นางแบบถือสินค้า
- 🎬 **สร้างวิดีโอ**: รวมภาพเป็นคลิปโฆษณา 9:16 (เหมาะกับ Instagram, TikTok)
- ✏️ **แก้ไข Prompt**: ปรับแต่งและสร้างภาพใหม่ได้
- 📊 **Export Logs**: บันทึกข้อมูลทั้งหมดเป็น CSV

## 📋 Requirements

- Python 3.10+
- **OpenAI API Key** (สำหรับ DALL-E 3 mode)
- **Replicate API Token** (สำหรับ Stable Diffusion XL mode)
- **Gemini API Key** (สำหรับ Gemini modes)
- **Kie.ai API Key** (สำหรับ Kie.ai Nano Banana + Veo3)
- ffmpeg (สำหรับสร้างวิดีโอ)

## 🌐 Deploy to Hugging Face Spaces (Recommended for 24/7 Free Hosting)

**Hugging Face Spaces** ให้บริการ host Streamlit app ฟรี รัน 24/7 โดยไม่ต้องเปิดเครื่องทิ้งไว้!

### ขั้นตอนการ Deploy:

1. **สร้างบัญชี Hugging Face**
   - ไปที่ https://huggingface.co/join
   - สมัครบัญชีฟรี

2. **สร้าง New Space**
   - ไปที่ https://huggingface.co/new-space
   - ตั้งชื่อ Space (เช่น "ai-product-visualizer")
   - เลือก **Streamlit** เป็น SDK
   - เลือก **Public** (ฟรี) หรือ **Private** (ต้องจ่าย)
   - คลิก **Create Space**

3. **Upload ไฟล์ทั้งหมด**

   **วิธีที่ 1: ผ่าน Web UI (ง่ายที่สุด)**
   - คลิก "Files and versions" tab
   - คลิก "Add file" → "Upload files"
   - เลือกไฟล์ทั้งหมดใน project:
     ```
     main.py
     config.py
     prompt_generator.py
     dalle_generator.py
     kie_generator.py
     video_creator.py
     veo_video_creator.py
     sora2_video_creator.py
     automation_loop.py
     requirements.txt
     ```
   - คลิก "Commit changes to main"

   **วิธีที่ 2: ผ่าน Git (สำหรับคนที่คุ้นเคย)**
   ```bash
   # Clone Space repository
   git clone https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
   cd YOUR_SPACE_NAME

   # Copy ไฟล์ทั้งหมดเข้าไป
   cp -r /path/to/your/project/* .

   # Push ไป Hugging Face
   git add .
   git commit -m "Initial deployment"
   git push
   ```

4. **ตั้งค่า API Keys (Secrets)**
   - ไปที่ Space settings (คลิกเกียร์ด้านบน)
   - เลือก "Variables and secrets"
   - เพิ่ม Secrets ต่อไปนี้:
     ```
     OPENAI_API_KEY = your-openai-api-key
     REPLICATE_API_TOKEN = your-replicate-token
     GEMINI_API_KEY = your-gemini-api-key
     KIE_API_KEY = your-kie-api-key
     IMGBB_API_KEY = your-imgbb-api-key (optional)
     ```
   - คลิก "Save"

5. **รอ Build & Deploy**
   - Space จะ build และ deploy อัตโนมัติ
   - รอประมาณ 2-5 นาที
   - เมื่อเสร็จจะแสดง "Running" status
   - URL จะเป็น: `https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME`

6. **เข้าใช้งาน 24/7** 🎉
   - เปิด URL ของ Space
   - แชร์ URL กับทีมได้เลย!
   - รันต่อเนื่อง 24/7 ไม่ต้องเปิดเครื่องทิ้งไว้

### 💡 Tips สำหรับ Hugging Face Spaces:

- **Persistent Storage**: ไฟล์ที่สร้าง (images/videos) จะเก็บไว้ถาวร แต่มีขอบเขต 50GB
- **CPU-only**: แพ็คเกจฟรีใช้ CPU อย่างเดียว (ไม่มี GPU) แต่เพียงพอสำหรับ automation loop
- **RAM**: 16GB (มากกว่า Streamlit Cloud มาก!)
- **Auto-restart**: ถ้า app crash จะ restart อัตโนมัติ
- **Free 24/7**: รันต่อเนื่องไม่หยุด ไม่เหมือน Streamlit Cloud ที่หลับถ้าไม่มีคนใช้

### 🔧 Troubleshooting Hugging Face:

**Problem: "Application error" / Build failed**
- ตรวจสอบ requirements.txt ว่าครบถ้วน
- ดู Logs ใน "Logs" tab เพื่อหา error

**Problem: ffmpeg not found**
- เพิ่มไฟล์ `packages.txt` ในโฟลเดอร์ root:
  ```
  ffmpeg
  ```
- Space จะติดตั้ง ffmpeg อัตโนมัติ

**Problem: API Keys ไม่ทำงาน**
- ตรวจสอบว่าตั้งค่า Secrets ถูกต้อง (ไม่มีเครื่องหมายคำพูด)
- ตรวจสอบว่าชื่อ variable ตรงกับที่ใช้ใน config.py

---

## 🚀 Installation (สำหรับรันบนเครื่องตัวเอง)

1. **Clone หรือ Download โปรเจกต์**

2. **ติดตั้ง Dependencies**
```bash
pip install -r requirements.txt
```

3. **ตั้งค่า API Keys**

สร้างไฟล์ `.env` ในโฟลเดอร์โปรเจกต์:
```env
# สำหรับ DALL-E 3 Mode
OPENAI_API_KEY=your-openai-api-key-here

# สำหรับ Stable Diffusion XL Mode
REPLICATE_API_TOKEN=your-replicate-token-here
```

**วิธีรับ API Keys:**
- OpenAI: https://platform.openai.com/api-keys
- Replicate: https://replicate.com/account/api-tokens

หรือกรอกใน UI ตอนรันโปรแกรม

4. **ติดตั้ง ffmpeg** (จำเป็นสำหรับสร้างวิดีโอ)

**Windows:**
- Download จาก https://ffmpeg.org/download.html
- เพิ่ม ffmpeg ไปใน PATH

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt-get install ffmpeg
```

## 🎯 Usage

1. **รันแอปพลิเคชัน**
```bash
streamlit run main.py
```

2. **เปิดเบราว์เซอร์** ที่ `http://localhost:8501`

3. **ใช้งาน:**

   **DALL-E 3 Mode (ปกติ):**
   - กรอก OpenAI API Key
   - เลือกโหมด "DALL·E 3 (ปกติ)"
   - กรอกข้อมูล: ประเภทสินค้า, เพศ, อายุ
   - คลิก "สร้าง Prompt" → แก้ไขได้
   - คลิก "สร้างรูปจาก Prompt"

   **Stable Diffusion XL Mode (เป๊ะกว่า):**
   - กรอก Replicate API Token
   - เลือกโหมด "Stable Diffusion XL (เป๊ะกว่า)"
   - **อัปโหลดรูปสินค้าจริง** (จำเป็น)
   - กรอกข้อมูล: ประเภทสินค้า, เพศ, อายุ, ฉาก
   - คลิก "สร้าง Prompt" → แก้ไขได้
   - คลิก "สร้างรูปจาก Prompt"
   - AI จะสร้างภาพโฆษณาที่มีสินค้าเหมือนรูปอ้างอิง

   **สร้างวิดีโอ:**
   - ไปที่แท็บ "Create Video"
   - เลือกภาพที่ต้องการ
   - คลิก "สร้างคลิปจากภาพ"
   - Download วิดีโอ .mp4

   **Export Logs:**
   - คลิก "Export Logs to CSV" ในแถบด้านข้าง

## 📁 Project Structure

```
AI Product Visualizer/
├── main.py                 # Streamlit UI
├── config.py              # Configuration settings
├── prompt_generator.py    # Generate prompts for DALL-E
├── dalle_generator.py     # DALL-E API integration
├── video_creator.py       # Video creation from images
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
├── .env                  # Environment variables (create this)
├── results/
│   ├── images/          # Generated images
│   └── videos/          # Generated videos
└── data/
    └── prompts.csv      # Exported logs
```

## 🎨 Supported Product Categories

- รองเท้า (Shoes)
- เสื้อผ้า (Clothing)
- กระเป๋า (Bags)
- นาฬิกา (Watch)
- แว่นตา (Sunglasses)
- เครื่องประดับ (Jewelry)
- หมวก (Hat)
- เข็มขัด (Belt)

## ⚙️ Configuration

แก้ไขได้ในไฟล์ `config.py`:

- `DALLE_SIZE`: ขนาดภาพ (default: 1024x1792 for 9:16)
- `DALLE_QUALITY`: คุณภาพ (default: "hd")
- `VIDEO_FPS`: Frame rate (default: 24)
- `VIDEO_DURATION_PER_IMAGE`: ระยะเวลาแสดงแต่ละภาพ (default: 3 วินาที)
- `VIDEO_SIZE`: ขนาดวิดีโอ (default: 1080x1920)

## 🤖 DALL-E 3 vs Stable Diffusion XL

| Feature | DALL-E 3 | Stable Diffusion XL |
|---------|----------|---------------------|
| **Input** | Prompt เท่านั้น | Prompt + รูปสินค้าจริง |
| **Output** | ภาพสร้างใหม่ทั้งหมด | ภาพโฆษณาที่มีสินค้าเหมือนรูปอ้างอิง |
| **ความแม่นยำ** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **ความเร็ว** | เร็วกว่า | ช้ากว่าเล็กน้อย |
| **ราคา** | $0.04-0.12/image | $0.002-0.01/image |
| **API Required** | OpenAI | Replicate |
| **Use Case** | Concept ทั่วไป | ต้องการสินค้าเหมือนของจริง |

**แนะนำ:**
- ใช้ **DALL-E 3** เมื่อต้องการ concept เบื้องต้น หรือไม่มีรูปสินค้า
- ใช้ **SDXL** เมื่อมีรูปสินค้าจริง และต้องการความแม่นยำสูง

## 💡 Tips

- ภาพที่สร้างจะถูกบันทึกอัตโนมัติใน `results/images/`
- วิดีโอจะถูกบันทึกใน `results/videos/`
- สามารถ Export ข้อมูลทั้งหมดเป็น CSV ได้จากแถบด้านข้าง
- ใช้ปุ่ม "Re-generate" เพื่อสร้างภาพใหม่ด้วย prompt เดิม
- ใช้ปุ่ม "Edit Prompt" เพื่อแก้ไข prompt และสร้างใหม่
- **SDXL Mode**: อัปโหลดรูปสินค้าที่ชัดเจน background สะอาด จะได้ผลดีที่สุด

### ✍️ การเขียน Prompt ที่ดี

**Prompt ที่ปลอดภัย (Safe):**
```
Professional product photography, natural lighting, high quality,
adult person, wearing stylish shoes, full body photograph, standing naturally,
clean composition, neutral background, sharp focus, professional lighting, vertical format
```

**หลีกเลี่ยง:**
- รายละเอียดเฉพาะเจาะจงเกินไปเกี่ยวกับคน (เชื้อชาติ, อายุแน่นอน)
- คำที่อาจตีความได้หลายทาง (sexy, provocative, etc.)
- การระบุบุคคลที่มีชื่อเสียง

**แนะนำ:**
- ใช้คำที่เป็นกลาง: "person", "adult", "wearing"
- เน้นที่สินค้า: "lifestyle photograph", "product photography"
- ระบุสไตล์: "clean", "professional", "natural lighting"

## 🔧 Troubleshooting

**Problem: "OpenAI API key is required"**
- ตรวจสอบว่ากรอก API Key ในแถบด้านข้างหรือไฟล์ .env

**Problem: "Content Policy Violation" / ถูกบลอกโดย Content Filter**
- Prompt อาจมีเนื้อหาที่ละเอียดเกินไป
- วิธีแก้:
  - คลิก "สร้าง Prompt" อีกครั้งเพื่อใช้ prompt ใหม่ที่ปลอดภัยกว่า
  - แก้ไข Prompt ด้วยตนเอง ลดรายละเอียดเกี่ยวกับคน
  - ใช้คำที่เป็นกลาง เช่น "person wearing shoes" แทน "young model in stylish footwear"
  - เน้นที่สินค้ามากกว่าผู้สวมใส่

**Problem: "Error creating video"**
- ตรวจสอบว่าติดตั้ง ffmpeg แล้ว
- ลองรัน `ffmpeg -version` ใน terminal

**Problem: "Rate limit exceeded"**
- รอสักครู่แล้วลองใหม่ (OpenAI มี rate limit)
- ตรวจสอบ quota ของ API key

**Problem: "Replicate API token is required" (SDXL Mode)**
- กรอก Replicate API Token ในแถบด้านข้าง
- หรือตั้งค่าใน .env: `REPLICATE_API_TOKEN=your-token`
- สมัครได้ที่: https://replicate.com/account/api-tokens

**Problem: SDXL ภาพไม่เหมือนสินค้า**
- ตรวจสอบรูปอ้างอิงว่าชัดเจน background สะอาด
- ลองปรับ prompt ให้ระบุรายละเอียดสินค้าชัดเจนขึ้น
- ลดจำนวน objects อื่นๆ ในภาพอ้างอิง

## 📝 License

This project is for educational and commercial use.

## 🙏 Credits

- OpenAI DALL-E 3 for image generation
- Stability AI / Replicate for Stable Diffusion XL
- Streamlit for UI framework
- MoviePy for video creation
