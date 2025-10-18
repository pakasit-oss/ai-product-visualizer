"""
Configuration file for AI Product Visualizer
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Directory configurations
RESULTS_DIR = BASE_DIR / "results"
IMAGES_DIR = RESULTS_DIR / "images"
VIDEOS_DIR = RESULTS_DIR / "videos"
DATA_DIR = BASE_DIR / "data"
UPLOAD_IMAGES_DIR = BASE_DIR / "upload_images"

# Create directories if they don't exist
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# CSV file path
PROMPTS_CSV = DATA_DIR / "prompts.csv"

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DALLE_MODEL = "dall-e-3"
DALLE_SIZE = "1024x1792"  # 9:16 aspect ratio (ลดจาก 1024x1792 เพื่อความเร็ว)
DALLE_QUALITY = "standard"  # เปลี่ยนจาก hd เป็น standard เพื่อลดเวลา
DALLE_STYLE = "natural"

# Replicate API Configuration (for Stable Diffusion XL)
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# Use gemini-1.5-pro for better compatibility (gemini-1.5-flash has API version issues)
GEMINI_VISION_MODEL = "gemini-1.5-pro"  # Multimodal model for vision
GEMINI_PRO_MODEL = "gemini-1.5-pro"  # Stable and compatible
GEMINI_FLASH_MODEL = "gemini-1.5-pro"  # Changed from flash to pro for stability

# Imagen API Configuration (Google's Image Generation)
IMAGEN_MODEL = "imagen-3.0-generate-001"  # Latest Imagen model

# Kie.ai API Configuration (Nano Banana + Veo3)
KIE_API_KEY = os.getenv("KIE_API_KEY", "")
KIE_NANO_BANANA_MODEL = "google/nano-banana-edit"
KIE_VEO3_MODEL = "veo3"

# imgbb API Configuration (for auto-uploading images)
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY", "")

# AI Engine Options
AI_ENGINES = [
    "Kie.ai Nano Banana (แนะนำสุด! ไม่มี Content Filter)",
    "SDXL + ControlNet (ตรงปก 100%)",
    "Stable Diffusion XL (เป๊ะกว่า)",
    "Gemini + SDXL Hybrid (วิเคราะห์ + สร้างภาพ)",
    "Gemini Imagen (ใช้ AI ล่าสุด)",
    "Gemini Pro Vision (วิเคราะห์อย่างเดียว)",
    "DALL·E 3 (Fallback)"
]

# Product categories (Thai language support)
PRODUCT_CATEGORIES = [
    "รองเท้า (Shoes)",
    "เสื้อผ้า (Clothing)",
    "กระเป๋า (Bags)",
    "นาฬิกา (Watch)",
    "แว่นตา (Sunglasses)",
    "เครื่องประดับ (Jewelry)",
    "หมวก (Hat)",
    "เข็มขัด (Belt)",
]

# Gender options
GENDER_OPTIONS = [
    "ชาย (Male)",
    "หญิง (Female)",
    "Unisex",
]

# Age ranges
AGE_RANGES = [
    "18-25",
    "26-35",
    "36-50",
    "50+",
]

# Photo styles
PHOTO_STYLES = [
    "iPhone Candid (แนะนำ - ธรรมชาติที่สุด)",
    "Professional Studio",
    "Minimal Clean",
    "Lifestyle Natural",
    "Fashion Editorial"
]

# Locations/Settings
LOCATIONS = [
    "Minimal Background (แนะนำ - เน้นสินค้า)",
    "Thai Cafe",
    "Urban Street",
    "Modern Studio",
    "Outdoor Natural",
    "Home Interior",
    "Shopping Mall"
]

# Camera angles
CAMERA_ANGLES = [
    "Waist Down (เอวลงมา - แนะนำสำหรับรองเท้า/กางเกง)",
    "Full Body",
    "Close-up Product Focus",
    "Mid Shot (เอวขึ้นไป)"
]

# Video configuration
VIDEO_FPS = 24
VIDEO_DURATION_PER_IMAGE = 2  # seconds (ลดจาก 3 เหลือ 2 เพื่อความเร็ว - สำหรับ MoviePy)
VIDEO_SIZE = (1080, 1920)  # 9:16 aspect ratio
SORA2_VIDEO_DURATION = 10  # วินาที สำหรับ Sora 2 / Veo3 (ถ้า API รองรับ)

# Allowed image extensions
ALLOWED_EXTENSIONS = [".png", ".jpg", ".jpeg"]
