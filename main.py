"""
AI Product Visualizer - Streamlit Application
Main UI for generating product visualization images and videos
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
from PIL import Image
import os
import random

# Import local modules
import config
from prompt_generator import PromptGenerator
from dalle_generator import DALLEGenerator
from kie_generator import KieGenerator
from veo_video_creator import Veo3VideoCreator
from sora2_video_creator import Sora2VideoCreator

# Import VideoCreator with optional moviepy support
try:
    from video_creator import VideoCreator
    VIDEO_CREATOR_AVAILABLE = True
except ImportError as e:
    VIDEO_CREATOR_AVAILABLE = False
    VideoCreator = None
    print(f"VideoCreator not available: {e}")


# Page configuration
st.set_page_config(
    page_title="AI Product Visualizer",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'generated_images' not in st.session_state:
    st.session_state.generated_images = []

if 'gallery_images' not in st.session_state:
    st.session_state.gallery_images = []

if 'prompts_data' not in st.session_state:
    st.session_state.prompts_data = []

if 'video_path' not in st.session_state:
    st.session_state.video_path = None

if 'generated_videos' not in st.session_state:
    st.session_state.generated_videos = []

if 'current_prompt' not in st.session_state:
    st.session_state.current_prompt = ""

if 'prompt_generated' not in st.session_state:
    st.session_state.prompt_generated = False

if 'ai_engine' not in st.session_state:
    st.session_state.ai_engine = "DALL·E 3 (ปกติ)"

if 'uploaded_reference_images' not in st.session_state:
    st.session_state.uploaded_reference_images = []

if 'saved_openai_key' not in st.session_state:
    st.session_state.saved_openai_key = ""

if 'saved_replicate_token' not in st.session_state:
    st.session_state.saved_replicate_token = ""

if 'saved_gemini_key' not in st.session_state:
    st.session_state.saved_gemini_key = ""

if 'saved_kie_key' not in st.session_state:
    st.session_state.saved_kie_key = ""

if 'saved_imgbb_key' not in st.session_state:
    st.session_state.saved_imgbb_key = ""


def load_saved_api_keys():
    """Load saved API keys from .env.local file"""
    env_file = Path(".env.local")
    if env_file.exists():
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('OPENAI_API_KEY='):
                        st.session_state.saved_openai_key = line.split('=', 1)[1].strip('"').strip("'")
                    elif line.startswith('REPLICATE_API_TOKEN='):
                        st.session_state.saved_replicate_token = line.split('=', 1)[1].strip('"').strip("'")
                    elif line.startswith('GEMINI_API_KEY='):
                        st.session_state.saved_gemini_key = line.split('=', 1)[1].strip('"').strip("'")
                    elif line.startswith('KIE_API_KEY='):
                        st.session_state.saved_kie_key = line.split('=', 1)[1].strip('"').strip("'")
                    elif line.startswith('IMGBB_API_KEY='):
                        st.session_state.saved_imgbb_key = line.split('=', 1)[1].strip('"').strip("'")
        except Exception as e:
            print(f"Error loading API keys: {e}")


def save_api_keys(openai_key, replicate_token, gemini_key, kie_key, imgbb_key):
    """Save API keys to .env.local file"""
    env_file = Path(".env.local")
    try:
        with open(env_file, 'w') as f:
            if openai_key:
                f.write(f'OPENAI_API_KEY="{openai_key}"\n')
            if replicate_token:
                f.write(f'REPLICATE_API_TOKEN="{replicate_token}"\n')
            if gemini_key:
                f.write(f'GEMINI_API_KEY="{gemini_key}"\n')
            if kie_key:
                f.write(f'KIE_API_KEY="{kie_key}"\n')
            if imgbb_key:
                f.write(f'IMGBB_API_KEY="{imgbb_key}"\n')
        st.session_state.saved_openai_key = openai_key
        st.session_state.saved_replicate_token = replicate_token
        st.session_state.saved_gemini_key = gemini_key
        st.session_state.saved_kie_key = kie_key
        st.session_state.saved_imgbb_key = imgbb_key
        return True
    except Exception as e:
        print(f"Error saving API keys: {e}")
        return False


def initialize_generators():
    """Initialize all generators"""
    try:
        prompt_gen = PromptGenerator()
        dalle_gen = DALLEGenerator()
        video_creator = VideoCreator()
        return prompt_gen, dalle_gen, video_creator
    except Exception as e:
        st.error(f"Error initializing generators: {str(e)}")
        return None, None, None


def generate_random_prompt_settings(product_category: str, gender: str, age_range: str):
    """
    Generate random prompt settings that match product, gender, and age

    Args:
        product_category: Product category
        gender: Gender
        age_range: Age range

    Returns:
        Dict with random photo_style, location, camera_angle
    """
    # Filter locations and styles based on product category
    if "รองเท้า" in product_category or "Shoes" in product_category:
        suitable_locations = [
            "Minimal Background (แนะนำ - เน้นสินค้า)",
            "Modern Cafe (ร้านกาแฟโมเดิร์น)",
            "Urban Street (ถนนเมือง)",
            "Beach (ชายหาด)",
            "Shopping Mall (ห้างสรรพสินค้า)",
            "Park (สวนสาธารณะ)",
            "Rooftop (ดาดฟ้า)"
        ]
        suitable_angles = [
            "Waist Down (เอวลงมา - แนะนำสำหรับรองเท้า/กางเกง)",
            "Full Body (ทั้งตัว)",
            "Low Angle (มุมต่ำ - เน้นรองเท้า)"
        ]
    elif "กระเป๋า" in product_category or "Bag" in product_category:
        suitable_locations = [
            "Minimal Background (แนะนำ - เน้นสินค้า)",
            "Modern Cafe (ร้านกาแฟโมเดิร์น)",
            "Shopping Mall (ห้างสรรพสินค้า)",
            "Hotel Lobby (ล็อบบี้โรงแรม)",
            "Airport (สนามบิน)",
            "Office (ออฟฟิศ)"
        ]
        suitable_angles = [
            "Upper Body (ครึ่งตัวบน)",
            "Close Up (ใกล้ชิด)",
            "Full Body (ทั้งตัว)"
        ]
    else:
        # Default for other products
        suitable_locations = config.LOCATIONS
        suitable_angles = config.CAMERA_ANGLES

    # Filter photo styles based on age range
    if "18-25" in age_range or "26-35" in age_range:
        suitable_styles = [
            "iPhone Candid (แนะนำ - ธรรมชาติที่สุด)",
            "Street Style (สไตล์ถนน)",
            "Casual Lifestyle (ไลฟ์สไตล์สบายๆ)",
            "Urban Modern (โมเดิร์นเมือง)"
        ]
    elif "36-45" in age_range or "46+" in age_range:
        suitable_styles = [
            "Professional Portrait (พอร์ตเทรตมืออาชีพ)",
            "Business Casual (ธุรกิจสบายๆ)",
            "Lifestyle Magazine (นิตยสารไลฟ์สไตล์)",
            "Elegant Minimal (มินิมอลหรูหรา)"
        ]
    else:
        suitable_styles = config.PHOTO_STYLES

    # Random select
    return {
        'photo_style': random.choice(suitable_styles),
        'location': random.choice(suitable_locations),
        'camera_angle': random.choice(suitable_angles)
    }


def one_click_generation(images_per_product=3, video_method="Sora 2"):
    """
    One click to generate multiple images and videos automatically

    Args:
        images_per_product: Number of images to generate per product (with different prompts)
        video_method: "Sora 2" or "Veo3"
    """

    st.info(f"🚀 เริ่มต้น One Click Generation... (สร้าง {images_per_product} รูป/สินค้า + {images_per_product} คลิป/สินค้า)")

    # ตรวจสอบว่ามีรูปอัปโหลดหรือไม่ (เช็คทั้ง uploaded และ batch)
    uploaded_images = st.session_state.uploaded_reference_images if st.session_state.uploaded_reference_images else []
    batch_images = st.session_state.batch_products if 'batch_products' in st.session_state else []

    # ใช้รูปจาก batch ถ้าไม่มีรูปที่อัปโหลดปกติ
    reference_images = uploaded_images if uploaded_images else batch_images

    if not reference_images or len(reference_images) == 0:
        st.error("❌ กรุณาอัปโหลดรูปสินค้าก่อน!")
        st.info("💡 ใช้ตัวอัปโหลดด้านบน หรือกดปุ่ม '📂 โหลดสินค้าจากโฟลเดอร์'")
        return

    # อัปเดต uploaded_reference_images ให้เป็นรูปที่จะใช้
    st.session_state.uploaded_reference_images = reference_images

    # Get settings from session state or use defaults
    product_category = st.session_state.get('oneclick_product_category', "รองเท้า (Shoes)")
    gender = st.session_state.get('oneclick_gender', "Unisex")
    age_range = st.session_state.get('oneclick_age_range', "18-25")
    ai_engine = st.session_state.get('ai_engine', 'Kie.ai Nano Banana (แนะนำสุด! ไม่มี Content Filter)')

    # Step 1 & 2: Generate Multiple Images per Product with Random Prompts
    num_products = len(st.session_state.uploaded_reference_images)
    total_images = num_products * images_per_product

    st.info(f"""
    🎨 Step 1/3: สร้างภาพ {total_images} ภาพ
    - จำนวนสินค้า: {num_products} ชิ้น
    - รูปต่อสินค้า: {images_per_product} รูป (แต่ละรูปใช้สถานที่/สไตล์ต่างกัน)
    """)

    # เก็บจำนวนรูปเก่าไว้
    old_images_count = len(st.session_state.generated_images)

    # Track newly created images
    images_created_count = 0
    prompt_gen = PromptGenerator()

    progress_bar = st.progress(0)
    total_progress = 0

    for product_idx, ref_image_path in enumerate(st.session_state.uploaded_reference_images):

        # สร้างหลายรูปสำหรับสินค้านี้ (แต่ละรูปใช้ prompt ต่างกัน)
        for variation_idx in range(images_per_product):
            status_container = st.empty()

            try:
                # สุ่ม prompt settings ใหม่สำหรับแต่ละ variation
                random_settings = generate_random_prompt_settings(
                    product_category=product_category,
                    gender=gender,
                    age_range=age_range
                )

                photo_style = random_settings['photo_style']
                location = random_settings['location']
                camera_angle = random_settings['camera_angle']

                # Generate prompt
                generated_prompt = prompt_gen.generate_image_prompt_v2(
                    product_category=product_category,
                    gender=gender,
                    age_range=age_range,
                    photo_style=photo_style,
                    location=location,
                    camera_angle=camera_angle,
                    custom_details=""
                )

                status_container.info(f"""
                📸 สินค้าที่ {product_idx + 1}/{num_products} - รูปที่ {variation_idx + 1}/{images_per_product}
                - ไฟล์: {Path(ref_image_path).name}
                - สถานที่: {location}
                - สไตล์: {photo_style}
                """)

                # Set uploaded_reference_images to only current image
                temp_uploaded = [ref_image_path]
                original_uploaded = st.session_state.uploaded_reference_images.copy()
                st.session_state.uploaded_reference_images = temp_uploaded

                # Generate 1 image for this variation
                generate_images_from_prompt(
                    prompt=generated_prompt,
                    product_category=product_category,
                    gender=gender,
                    age_range=age_range,
                    num_images=1,
                    ai_engine=ai_engine,
                    photo_style=photo_style,
                    location=location,
                    camera_angle=camera_angle,
                    skip_display=True
                )

                # Restore uploaded_reference_images
                st.session_state.uploaded_reference_images = original_uploaded

                images_created_count += 1
                total_progress += 1
                status_container.success(f"✅ สินค้าที่ {product_idx + 1}/{num_products} - รูปที่ {variation_idx + 1}/{images_per_product} สำเร็จ!")
                progress_bar.progress(total_progress / total_images)

            except Exception as e:
                error_msg = str(e)
                status_container.error(f"❌ ข้ามรูป: {error_msg[:100]}")
                print(f"ERROR in one_click_generation: Product {product_idx + 1}, Variation {variation_idx + 1}: {error_msg}")
                # Restore uploaded_reference_images
                st.session_state.uploaded_reference_images = original_uploaded
                total_progress += 1
                progress_bar.progress(total_progress / total_images)
                continue

    progress_bar.empty()

    if images_created_count == 0:
        st.error("❌ ไม่สามารถสร้างภาพได้เลย")
        return

    st.success(f"✅ สร้างภาพเสร็จแล้ว {images_created_count}/{total_images} ภาพ!")

    # Step 2: Create Videos
    st.info(f"🎬 Step 2/3: สร้างวิดีโอด้วย {video_method} AI ({images_created_count} คลิป - มีการเคลื่อนไหว)...")

    try:
        # Use only newly created images (from old_images_count onwards)
        newly_created_images = st.session_state.generated_images[old_images_count:]

        if newly_created_images:
            # Initialize video creator and Kie.ai (for imgbb upload)
            from kie_generator import KieGenerator
            kie_gen = KieGenerator()

            # Check API keys only for AI methods
            if video_method != "Quick Video (MoviePy)":
                if not config.KIE_API_KEY:
                    st.error(f"❌ ต้องการ KIE_API_KEY เพื่อใช้ {video_method}")
                    return

                if not config.IMGBB_API_KEY:
                    st.error("❌ ต้องการ IMGBB_API_KEY เพื่ออัปโหลดภาพ")
                    return

            # Initialize correct video creator
            if video_method == "Quick Video (MoviePy)":
                from video_creator import VideoCreator
                video_creator = VideoCreator(duration_per_image=5)  # 5 seconds per image
                est_time_per_video = "instant"
                use_ai = False
            elif video_method == "Veo3":
                from veo_video_creator import Veo3VideoCreator
                video_creator = Veo3VideoCreator()
                est_time_per_video = "10-30"
                use_ai = True
            else:  # Sora 2
                from sora2_video_creator import Sora2VideoCreator
                video_creator = Sora2VideoCreator()
                est_time_per_video = "3-5"
                use_ai = True

            videos_created = 0
            video_progress = st.progress(0)

            # แสดงสถานะการสร้างวิดีโอ
            if use_ai:
                st.info(f"""
                ⏳ **กำลังสร้างวิดีโอทีละคลิป (Sequential) - รอคลิปแรกเสร็จก่อนค่อยสร้างคลิปต่อไป**
                - จำนวนรวม: {len(newly_created_images)} คลิป
                - เวลาโดยประมาณ: {len(newly_created_images) * int(est_time_per_video.split('-')[0])}-{len(newly_created_images) * int(est_time_per_video.split('-')[1])} นาที
                - สถานะ: รอ {video_method} AI สร้างวิดีโอที่มีการเคลื่อนไหว

                ⚠️ **โปรดอย่าปิดหน้าต่าง** - กำลังสร้างทีละคลิปจนครบ
                """)
            else:
                st.info(f"""
                ⚡ **กำลังสร้างวิดีโอด้วย MoviePy (รวดเร็ว!)**
                - จำนวนรวม: {len(newly_created_images)} คลิป
                - เวลาโดยประมาณ: น้อยกว่า 1 นาที (ไม่ใช้ AI)
                - สถานะ: สร้างวิดีโอแบบ slideshow ทันที
                """)

            # Create preview container for completed videos
            st.divider()
            preview_header = st.empty()
            preview_container = st.container()
            st.divider()

            # สร้างวิดีโอแยกสำหรับแต่ละภาพ (ทีละสินค้า)
            for idx, img_data in enumerate(newly_created_images):
                # แสดงสถานะปัจจุบัน
                current_status = st.empty()
                video_status = st.empty()

                try:
                    # แสดงว่ากำลังทำสินค้าไหน
                    current_status.info(f"""
                    🎬 **กำลังสร้างคลิปที่ {idx + 1}/{len(newly_created_images)}** (รอคลิปนี้เสร็จก่อนค่อยทำต่อ)
                    - ภาพที่ใช้: `{Path(img_data['path']).name}`
                    - สถานะ: กำลังเริ่มต้น...
                    """)

                    import time
                    start_time = time.time()

                    # Quick Video (MoviePy) - ไม่ต้องอัปโหลด
                    if video_method == "Quick Video (MoviePy)":
                        video_status.info(f"⚡ กำลังสร้างวิดีโอด้วย MoviePy (ทันที)...")

                        # สร้างวิดีโอจากภาพโดยตรง
                        filename = f"oneclick_quick_product{idx + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                        video_path = video_creator.create_video(
                            image_paths=[img_data['path']],
                            filename=filename
                        )

                        result = {
                            'path': str(video_path),
                            'url': None,
                            'task_id': 'moviepy_quick',
                            'prompt': 'Quick slideshow video'
                        }

                        elapsed = int(time.time() - start_time)
                        video_status.success(f"✅ MoviePy สร้างวิดีโอเสร็จแล้ว (ใช้เวลา {elapsed} วินาที)")

                    # AI Video (Sora 2 / Veo3) - ต้องอัปโหลดก่อน
                    else:
                        # Upload image to imgbb first
                        video_status.info(f"📤 ขั้นตอนที่ 1/3: อัปโหลดภาพไป imgbb...")
                        image_url = kie_gen.upload_image_to_imgbb(
                            img_data['path'],
                            config.IMGBB_API_KEY
                        )
                        video_status.success(f"✅ อัปโหลดภาพสำเร็จ")

                        # Create video prompt (motion description)
                        video_prompt = (
                            "A smooth, natural camera movement. "
                            "Subtle product showcase with gentle motion. "
                            "Professional commercial style with slight zoom and pan. "
                            "High quality, cinematic lighting."
                        )

                        # Generate video
                        if video_method == "Veo3":
                            video_status.info(f"🎬 ขั้นตอนที่ 2/3: ส่งไป Veo3 AI (รอ 10-30 นาที)...")
                        else:
                            video_status.info(f"🎬 ขั้นตอนที่ 2/3: ส่งไป Sora 2 AI (รอ 3-5 นาที)...")

                        if video_method == "Veo3":
                            result = video_creator.create_video_from_images(
                                image_urls=[image_url],
                                prompt=video_prompt,
                                filename=f"oneclick_veo3_product{idx + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                                aspect_ratio="9:16",
                                watermark=None
                            )
                        else:  # Sora 2
                            result = video_creator.create_video_from_image(
                                image_url=image_url,
                                prompt=video_prompt,
                                filename=f"oneclick_sora2_product{idx + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                                aspect_ratio="portrait",
                                remove_watermark=True
                            )

                        elapsed = int(time.time() - start_time)
                        video_status.success(f"✅ {video_method} สร้างวิดีโอเสร็จแล้ว (ใช้เวลา {elapsed} วินาที)")

                    # บันทึกข้อมูลวิดีโอ
                    video_data = {
                        'path': result['path'],
                        'method': f'{video_method} (One Click)',
                        'task_id': result.get('task_id', ''),
                        'prompt': result.get('prompt', 'N/A'),
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'filename': Path(result['path']).name,
                        'image_used': img_data['path']
                    }
                    st.session_state.generated_videos.append(video_data)

                    videos_created += 1

                    # อัปเดต progress
                    video_progress.progress((idx + 1) / len(newly_created_images))

                    # แสดงสรุปสินค้าที่เสร็จ
                    current_status.success(f"""
                    ✅ **คลิปที่ {idx + 1}/{len(newly_created_images)} เสร็จสมบูรณ์!**
                    - ไฟล์: `{Path(result['path']).name}`
                    - ใช้เวลา: {elapsed} วินาที
                    """)

                    # Show preview of completed video immediately
                    preview_header.success(f"🎬 **วิดีโอที่สร้างเสร็จแล้ว: {videos_created}/{len(newly_created_images)} คลิป**")

                    with preview_container:
                        st.subheader(f"📹 คลิปที่ {idx + 1}: {Path(result['path']).name}")

                        # Show video player
                        if Path(result['path']).exists():
                            st.video(result['path'])
                            st.caption(f"⏱️ ใช้เวลาสร้าง: {elapsed} วินาที | 🎨 ภาพต้นฉบับ: {Path(img_data['path']).name}")
                        else:
                            st.error(f"❌ ไม่พบไฟล์: {result['path']}")

                        st.divider()

                    # ถ้ายังมีสินค้าถัดไป แสดงว่ากำลังจะทำต่อ
                    if idx + 1 < len(newly_created_images):
                        st.success(f"✅ **คลิปที่ {idx + 1} เสร็จแล้ว** - เริ่มสร้างคลิปที่ {idx + 2} ต่อไป...")

                except Exception as e:
                    error_msg = str(e)
                    video_status.error(f"❌ ข้ามวิดีโอที่ {idx + 1}: {error_msg[:150]}")
                    current_status.error(f"❌ **สินค้าที่ {idx + 1} ล้มเหลว**: {error_msg[:100]}")
                    print(f"ERROR creating Sora 2 video {idx + 1}: {error_msg}")

                    # Check if it's the photorealistic people error
                    if 'photorealistic people' in error_msg.lower() or 'contains people' in error_msg.lower():
                        st.warning("🚫 **ภาพนี้มีคนจริง** - Sora 2 ไม่รองรับภาพที่มีคนจริง")
                        st.info("💡 ข้ามคลิปนี้ไป - จะสร้างคลิปถัดไปต่อ")

                    # Continue to next video
                    if idx + 1 < len(newly_created_images):
                        st.info(f"⏭️ ข้ามคลิปที่ {idx + 1} - เริ่มคลิปที่ {idx + 2} ต่อไป...")
                    continue

            video_progress.empty()

            # Update latest video path
            if videos_created > 0:
                st.session_state.video_path = st.session_state.generated_videos[-1]['path']

            # Show success message
            st.balloons()
            st.success("🎉 One Click Generation เสร็จสมบูรณ์!")
            st.info(f"""
            📊 **สรุปผลลัพธ์:**
            - ภาพที่สร้าง: {images_created_count} ภาพ
            - วิดีโอที่สร้าง: {videos_created} คลิป (สร้างทีละคลิป Sequential)
            - วิธีการ: Sora 2 AI - มีการเคลื่อนไหว
            - ดูวิดีโอทั้งหมดได้ที่แท็บ 🎞️ Video Gallery

            ✅ **ทุกคลิปถูกสร้างทีละคลิป** - รอคลิปแรกเสร็จก่อนค่อยสร้างต่อ
            """)
        else:
            st.error("❌ ไม่มีภาพที่สร้างเพื่อทำวิดีโอ")

    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดในการสร้างวิดีโอ: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return

    # Rerun to show results
    st.rerun()


def main():
    """Main application"""

    # Load saved API keys on first run
    if not st.session_state.saved_openai_key and not st.session_state.saved_replicate_token and not st.session_state.saved_gemini_key and not st.session_state.saved_kie_key and not st.session_state.saved_imgbb_key:
        load_saved_api_keys()

    # Title and header
    st.title("🎨 AI Product Visualizer")
    st.markdown("### สร้างภาพโฆษณาสินค้าด้วย AI และรวมเป็นวิดีโอโฆษณา")

    # Sidebar for API key configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Use saved keys as default value
        default_openai = st.session_state.saved_openai_key or config.OPENAI_API_KEY
        default_replicate = st.session_state.saved_replicate_token or config.REPLICATE_API_TOKEN
        default_gemini = st.session_state.saved_gemini_key or config.GEMINI_API_KEY
        default_kie = st.session_state.saved_kie_key or config.KIE_API_KEY
        default_imgbb = st.session_state.saved_imgbb_key or config.IMGBB_API_KEY

        # Kie.ai API Key input (PRIMARY - No Content Filter!)
        kie_api_key = st.text_input(
            "🚀 Kie.ai API Key (แนะนำสุด! - Nano Banana + Veo3)",
            value=default_kie,
            type="password",
            help="Kie.ai API key สำหรับ Nano Banana สร้างภาพ + Veo3 สร้างวิดีโอ (ไม่มี Content Filter!)"
        )

        if kie_api_key:
            os.environ["KIE_API_KEY"] = kie_api_key
            config.KIE_API_KEY = kie_api_key

        # imgbb API Key input (For auto-uploading images)
        imgbb_api_key = st.text_input(
            "🖼️ imgbb API Key (สำหรับอัปโหลดรูปอัตโนมัติ)",
            value=default_imgbb,
            type="password",
            help="imgbb API key สำหรับอัปโหลดรูปอัตโนมัติ (ฟรี! ขอได้ที่ https://api.imgbb.com/)"
        )

        if imgbb_api_key:
            os.environ["IMGBB_API_KEY"] = imgbb_api_key
            config.IMGBB_API_KEY = imgbb_api_key

        # Gemini API Key input (For Prompt Generation)
        gemini_api_key = st.text_input(
            "🌟 Gemini API Key (สำหรับสร้าง Prompt)",
            value=default_gemini,
            type="password",
            help="Google Gemini API key สำหรับสร้าง prompt อัจฉริยะ"
        )

        if gemini_api_key:
            os.environ["GEMINI_API_KEY"] = gemini_api_key
            config.GEMINI_API_KEY = gemini_api_key

        # OpenAI API Key input (Fallback)
        api_key = st.text_input(
            "OpenAI API Key (Fallback - DALL-E)",
            value=default_openai,
            type="password",
            help="(Optional) OpenAI API key สำหรับ DALL-E 3 เป็น fallback"
        )

        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            config.OPENAI_API_KEY = api_key

        # Replicate API Token input
        replicate_token = st.text_input(
            "Replicate API Token (SDXL)",
            value=default_replicate,
            type="password",
            help="Enter your Replicate API token for Stable Diffusion XL"
        )

        if replicate_token:
            os.environ["REPLICATE_API_TOKEN"] = replicate_token
            config.REPLICATE_API_TOKEN = replicate_token


        # Save API Keys button
        col1, col2 = st.columns([2, 1])
        with col1:
            if st.button("💾 Save API Keys", use_container_width=True):
                if save_api_keys(api_key, replicate_token, gemini_api_key, kie_api_key, imgbb_api_key):
                    st.success("✅ API Keys saved!")
                else:
                    st.error("❌ Failed to save API Keys")

        with col2:
            if st.button("🗑️ Clear", use_container_width=True):
                if save_api_keys("", "", "", "", ""):
                    st.session_state.saved_openai_key = ""
                    st.session_state.saved_replicate_token = ""
                    st.session_state.saved_gemini_key = ""
                    st.session_state.saved_kie_key = ""
                    st.session_state.saved_imgbb_key = ""
                    st.success("✅ Cleared!")
                    st.rerun()

        st.divider()

        # ============ KIE.AI CREDIT DISPLAY (PROMINENT) ============
        # แสดงเครดิต Kie.ai แบบเรียลไทม์
        if kie_api_key:  # แสดงก็ต่อเมื่อมี API key
            try:
                kie_gen_sidebar = KieGenerator()
                credit_info = kie_gen_sidebar.get_credits()

                if credit_info.get('success'):
                    credits = credit_info.get('credits', 0)
                    currency = credit_info.get('currency', 'credits')

                    # แสดงเครดิตแบบเด่นชัด พร้อมสีตามระดับ
                    if credits == 0:
                        st.error(f"### 💳 เครดิต: **{credits:,}**")
                        st.error("⚠️ **เครดิตหมด!**")
                    elif credits < 50:
                        st.error(f"### 💳 เครดิต: **{credits:,}**")
                        st.error("🚨 **เหลือน้อยมาก!**")
                    elif credits < 200:
                        st.warning(f"### 💳 เครดิต: **{credits:,}**")
                        st.warning("⚠️ **เหลือน้อย**")
                    else:
                        st.success(f"### 💳 เครดิต: **{credits:,}**")

                    # ปุ่มเติมเครดิต
                    st.link_button(
                        "💰 เติมเครดิต Kie.ai",
                        "https://kie.ai/billing",
                        use_container_width=True
                    )
                else:
                    st.info("💳 **เครดิต**: ไม่สามารถตรวจสอบได้")

            except Exception as e:
                # Silent fail หรือแสดงข้อความสั้นๆ
                st.info(f"💳 **เครดิต**: ไม่สามารถตรวจสอบได้")

            st.divider()
        # ============ END CREDIT DISPLAY ============

        # Statistics
        st.header("📊 Statistics")
        col_stat1, col_stat2 = st.columns(2)
        with col_stat1:
            st.metric("ภาพพรีวิว", len(st.session_state.generated_images))
        with col_stat2:
            st.metric("แกลเลอรี่", len(st.session_state.gallery_images))
        st.metric("Videos Created", 1 if st.session_state.video_path else 0)

        st.divider()

        # Export logs section
        st.header("📥 Export Data")
        if st.button("Export Logs to CSV", use_container_width=True):
            export_logs_to_csv()

    # Main content area
    tabs = st.tabs(["📤 Upload & Generate", "🎬 Create Video", "🔄 Auto Loop", "📷 Gallery", "🎞️ Video Gallery"])

    # Tab 1: Upload & Generate
    with tabs[0]:
        upload_and_generate_tab()

    # Tab 2: Create Video
    with tabs[1]:
        create_video_tab()

    # Tab 3: Auto Loop (NEW!)
    with tabs[2]:
        from automation_loop import create_automation_tab
        create_automation_tab()

    # Tab 4: Gallery
    with tabs[3]:
        gallery_tab()

    # Tab 5: Video Gallery
    with tabs[4]:
        video_gallery_tab()


def upload_and_generate_tab():
    """Upload images and generate new visualizations"""

    st.header("1️⃣ อัปโหลดรูปสินค้า")

    uploaded_files = st.file_uploader(
        "เลือกรูปภาพสินค้า (PNG, JPG)",
        type=['png', 'jpg', 'jpeg'],
        accept_multiple_files=True,
        key="product_images_uploader",
        help="อัปโหลดรูปสินค้าจริง → ใช้ Hybrid (Gemini วิเคราะห์ + SDXL สร้างภาพ) | ไม่อัปโหลด → ใช้ DALL-E (สร้างจากจินตนาการ)"
    )

    # AI Engine selection (manual)
    has_uploaded = uploaded_files is not None and len(uploaded_files) > 0
    has_saved = len(st.session_state.uploaded_reference_images) > 0
    has_batch_products = 'batch_products' in st.session_state and len(st.session_state.batch_products) > 0

    # Show dropdown to select AI engine
    if has_uploaded or has_saved or has_batch_products:
        # User uploaded images - show options that use reference images
        engine_options = [
            "Kie.ai Nano Banana (แนะนำสุด! ไม่มี Content Filter)",
            "SDXL + ControlNet (ตรงปก 100%)",
            "Stable Diffusion XL (เป๊ะกว่า)",
            "Gemini + SDXL Hybrid (วิเคราะห์ + สร้างภาพ)",
            "Gemini Pro Vision (วิเคราะห์อย่างเดียว)"
        ]
        default_index = 0  # Default to Kie.ai Nano Banana
    else:
        # No images uploaded
        engine_options = [
            "Gemini Imagen (ใช้ AI ล่าสุด)",
            "DALL·E 3 (Fallback)"
        ]
        default_index = 0

    ai_engine = st.selectbox(
        "🤖 เลือก AI Engine",
        options=engine_options,
        index=default_index,
        help="SDXL = เร็ว เหมือนของจริง | Hybrid = ช้า แต่วิเคราะห์ก่อน"
    )

    st.session_state.ai_engine = ai_engine

    # DEBUG: Show upload status
    st.info(f"""
    📊 **สถานะการอัปโหลด:**
    - uploaded_files: {len(uploaded_files) if uploaded_files else 0} ไฟล์
    - saved in session: {len(st.session_state.uploaded_reference_images)} ไฟล์
    - batch_products: {len(st.session_state.batch_products) if has_batch_products else 0} ไฟล์
    - AI Engine: {ai_engine}
    """)

    # Show selected engine
    if ai_engine == "Kie.ai Nano Banana (แนะนำสุด! ไม่มี Content Filter)":
        st.success("🚀 **โหมด: Kie.ai Nano Banana** - ยึดรูปสินค้า 100% + ไม่มี Content Filter (แนะนำสุด!)")
    elif ai_engine == "Gemini Imagen (แนะนำ - ใช้ AI ล่าสุด)":
        st.success("🌟 **โหมด: Gemini Imagen** - ใช้ Gemini สร้าง prompt + Imagen สร้างรูป")
    elif ai_engine == "Gemini + SDXL Hybrid (วิเคราะห์ + สร้างภาพ)":
        st.success("🔮 **โหมด: Hybrid** - ใช้ Gemini วิเคราะห์ + SDXL สร้างภาพ")
    elif ai_engine == "Gemini Pro Vision (วิเคราะห์อย่างเดียว)":
        st.success("🔮 **โหมด: Gemini Vision** - วิเคราะห์สินค้าและให้คำแนะนำ")
    elif ai_engine == "Stable Diffusion XL (เป๊ะกว่า)":
        st.success("✅ **โหมด: SDXL** - สร้างภาพที่เหมือนสินค้าต้นฉบับมาก")
    elif ai_engine == "SDXL + ControlNet (ตรงปก 100%)":
        st.success("🎯 **โหมด: SDXL + ControlNet** - ยึดรูปสินค้า 100%")
    else:
        st.info("💡 **โหมด: DALL-E** - สร้างภาพจาก prompt (Fallback)")

    if uploaded_files:
        st.success(f"อัปโหลดสำเร็จ {len(uploaded_files)} ไฟล์")

        # DEBUG: Show current state
        st.warning(f"""
        🔍 DEBUG ก่อนบันทึก:
        - ai_engine: `{ai_engine}`
        - uploaded_files: {len(uploaded_files)} ไฟล์
        - uploaded_reference_images ใน session: {len(st.session_state.uploaded_reference_images)} ไฟล์
        - รายการ: {st.session_state.uploaded_reference_images}
        """)

        # Save uploaded files to temp directory - ALWAYS SAVE FOR HYBRID MODE
        # Don't use complex logic, just save directly
        st.session_state.uploaded_reference_images = []
        st.session_state.uploaded_filenames = [f.name for f in uploaded_files]

        for uploaded_file in uploaded_files:
            image = Image.open(uploaded_file)
            # Save to temp file for all modes that need reference images
            if ai_engine != "DALL·E 3 (ปกติ)":
                temp_path = config.IMAGES_DIR / f"temp_ref_{uploaded_file.name}"
                image.save(temp_path)
                st.session_state.uploaded_reference_images.append(str(temp_path))
                st.success(f"✅ บันทึก: {temp_path}")

        # DEBUG: Show after save
        st.warning(f"""
        🔍 DEBUG หลังบันทึก:
        - บันทึกไปแล้ว: {len(st.session_state.uploaded_reference_images)} ไฟล์
        - รายการ: {st.session_state.uploaded_reference_images}
        """)

        # Display uploaded images
        cols = st.columns(min(len(uploaded_files), 4))
        for idx, uploaded_file in enumerate(uploaded_files):
            with cols[idx % 4]:
                image = Image.open(uploaded_file)
                # Create thumbnail copy for preview
                img_preview = image.copy()
                img_preview.thumbnail((400, 400))
                st.image(img_preview, width=400, caption=f"สินค้า: {uploaded_file.name}")

        # DEBUG: Show saved images count
        st.info(f"🔍 DEBUG: บันทึกรูปแล้ว {len(st.session_state.uploaded_reference_images)} ไฟล์ | โหมด: {ai_engine}")

    st.divider()

    # ========== BATCH UPLOAD SECTION ==========
    st.header("📦 Batch Upload & Auto-Generate")
    st.info("""
    💡 **วิธีใช้ Batch Mode:**
    1. วางรูปสินค้าทั้งหมดในโฟลเดอร์ `upload_images`
    2. กดปุ่ม "📂 โหลดสินค้าจากโฟลเดอร์"
    3. ตั้งค่า Style/Location/Camera Angle สำหรับทุกสินค้า
    4. กดปุ่ม "🚀 สร้างภาพทุกสินค้าอัตโนมัติ" → ระบบจะสร้างให้ทั้งหมด!
    """)

    col_batch1, col_batch2 = st.columns([2, 1])

    with col_batch1:
        if st.button("📂 โหลดสินค้าจากโฟลเดอร์ upload_images", use_container_width=True):
            batch_load_products_from_folder()

    with col_batch2:
        # Open upload_images folder button
        if st.button("📁 เปิดโฟลเดอร์ upload_images", use_container_width=True):
            import subprocess
            import os
            folder_path = os.path.abspath("upload_images")
            try:
                subprocess.Popen(f'explorer "{folder_path}"')
                st.success("เปิดโฟลเดอร์แล้ว!")
            except Exception as e:
                st.error(f"Error: {e}")

    # ========== ONE CLICK BUTTON ==========
    st.divider()

    num_uploaded_images = len(st.session_state.uploaded_reference_images)

    if num_uploaded_images > 0:
        st.success(f"✅ พบรูปสินค้า {num_uploaded_images} ไฟล์ พร้อมสร้าง!")

    st.info("💡 **One Click:** กดปุ่มเดียว → สร้างภาพหลายรูป (สุ่มสถานที่/สไตล์) → สร้างวิดีโอจากทุกรูป")

    # ONE CLICK Settings
    st.subheader("⚙️ ตั้งค่า ONE CLICK")

    col_oc1, col_oc2, col_oc3 = st.columns(3)

    with col_oc1:
        oneclick_product_category = st.selectbox(
            "ประเภทสินค้า",
            options=config.PRODUCT_CATEGORIES,
            key="oneclick_product_category_select"
        )
        st.session_state.oneclick_product_category = oneclick_product_category

    with col_oc2:
        oneclick_gender = st.selectbox(
            "เพศ",
            options=config.GENDER_OPTIONS,
            key="oneclick_gender_select"
        )
        st.session_state.oneclick_gender = oneclick_gender

    with col_oc3:
        oneclick_age_range = st.selectbox(
            "ช่วงอายุ",
            options=config.AGE_RANGES,
            key="oneclick_age_range_select"
        )
        st.session_state.oneclick_age_range = oneclick_age_range

    col_oc4, col_oc5 = st.columns(2)

    with col_oc4:
        images_per_product = st.number_input(
            "จำนวนรูป/สินค้า (แต่ละรูปสุ่มสถานที่/สไตล์ใหม่)",
            min_value=1,
            max_value=10,
            value=3,
            help="สร้างกี่รูปต่อ 1 สินค้า (แต่ละรูปจะอยู่สถานที่/สไตล์ต่างกัน)"
        )

    with col_oc5:
        video_method = st.selectbox(
            "วิธีการสร้างวิดีโอ",
            options=["Quick Video (MoviePy)", "Sora 2", "Veo3"],
            help=(
                "Quick Video = ทันที (ไม่ใช้ AI, slideshow)\n"
                "Sora 2 = เร็ว 3-5 นาที/คลิป (ไม่รองรับคน)\n"
                "Veo3 = ช้า 10-30 นาที/คลิป (รองรับคน แต่ไม่เสถียร)"
            )
        )

    # Show performance warning for Veo3
    if video_method == "Veo3":
        st.warning(
            "⚠️ **Veo3 ช้ามาก!**\n\n"
            "- ใช้เวลา **10-30 นาที** ต่อคลิป และมักมีปัญหา\n"
            "- แนะนำใช้ **Quick Video** (ทันที) หรือ **Sora 2** (3-5 นาที) แทน"
        )
    elif video_method == "Quick Video (MoviePy)":
        st.success(
            "⚡ **Quick Video - รวดเร็วที่สุด!**\n\n"
            "- สร้างวิดีโอทันที (ไม่ต้องรอ AI)\n"
            "- แสดงรูปแบบ slideshow พร้อม transition\n"
            "- เหมาะสำหรับต้องการความเร็ว"
        )

    total_outputs = num_uploaded_images * images_per_product

    # Calculate estimated time based on method
    if video_method == "Veo3":
        min_time_per_video = 10  # Veo3 takes 10-30 minutes
        max_time_per_video = 30
        time_str = f"{total_outputs * min_time_per_video}-{total_outputs * max_time_per_video} นาที"
    elif video_method == "Sora 2":
        min_time_per_video = 3   # Sora 2 takes 3-5 minutes
        max_time_per_video = 5
        time_str = f"{total_outputs * min_time_per_video}-{total_outputs * max_time_per_video} นาที"
    else:  # Quick Video
        time_str = "ทันที (ไม่เกิน 30 วินาที)"

    st.info(f"📊 จะได้รวม: **{total_outputs} รูป** + **{total_outputs} คลิป** (ใช้เวลาประมาณ {time_str})")

    if st.button("⚡ ONE CLICK - สร้างทั้งหมดอัตโนมัติ", type="primary", use_container_width=True, key="oneclick_btn"):
        one_click_generation(images_per_product=images_per_product, video_method=video_method)

    st.divider()

    # Show loaded products
    if 'batch_products' in st.session_state and len(st.session_state.batch_products) > 0:
        st.success(f"✅ โหลดสินค้าแล้ว {len(st.session_state.batch_products)} รายการ")

        # Display loaded products in grid
        st.subheader("🛍️ สินค้าที่พร้อมสร้าง")
        batch_cols = st.columns(min(len(st.session_state.batch_products), 5))
        for idx, product_path in enumerate(st.session_state.batch_products[:5]):
            with batch_cols[idx]:
                try:
                    img = Image.open(product_path)
                    img_preview = img.copy()
                    img_preview.thumbnail((200, 200))
                    st.image(img_preview, caption=Path(product_path).name, use_column_width=True)
                except Exception as e:
                    st.error(f"Error: {e}")

        if len(st.session_state.batch_products) > 5:
            st.caption(f"... และอีก {len(st.session_state.batch_products) - 5} รายการ")

        st.divider()

    # Form for product information (ใช้ร่วมกันทั้ง Single และ Batch Mode)
    st.header("2️⃣ ตั้งค่าการสร้างภาพ")

    col1, col2, col3 = st.columns(3)

    with col1:
        product_category = st.selectbox(
            "ประเภทสินค้า",
            options=config.PRODUCT_CATEGORIES,
            help="เลือกประเภทของสินค้า"
        )

    with col2:
        gender = st.selectbox(
            "เพศของนายแบบ/นางแบบ",
            options=config.GENDER_OPTIONS,
            help="เลือกเพศของนายแบบ/นางแบบ"
        )

    with col3:
        age_range = st.selectbox(
            "ช่วงอายุ",
            options=config.AGE_RANGES,
            help="เลือกช่วงอายุของนายแบบ/นางแบบ"
        )

    st.divider()

    # Photo style settings
    st.subheader("📸 สไตล์ภาพและมุมกล้อง")

    col_style1, col_style2, col_style3 = st.columns(3)

    with col_style1:
        photo_style = st.selectbox(
            "สไตล์ภาพ",
            options=config.PHOTO_STYLES,
            help="เลือกสไตล์การถ่ายภาพ"
        )

    with col_style2:
        location = st.selectbox(
            "สถานที่/ฉากหลัง",
            options=config.LOCATIONS,
            help="เลือกสถานที่ถ่ายภาพ"
        )

    with col_style3:
        camera_angle = st.selectbox(
            "มุมกล้อง",
            options=config.CAMERA_ANGLES,
            help="เลือกมุมกล้อง (แนะนำ: Waist Down สำหรับรองเท้า/กางเกง)"
        )

    # Additional details
    custom_details = st.text_area(
        "รายละเอียดเพิ่มเติม (Optional)",
        placeholder="เช่น urban background, luxury setting, outdoor scene, etc.",
        help="เพิ่มรายละเอียดพิเศษสำหรับ prompt"
    )

    st.divider()

    # Generate Prompt button
    st.header("3️⃣ สร้าง Prompt")

    col_btn1, col_btn2 = st.columns([3, 1])

    with col_btn1:
        if st.button("📝 สร้าง Prompt", type="secondary", use_container_width=True):
            # Generate prompt based on selected AI engine
            prompt_gen = PromptGenerator()

            # Use V2 (No Face, Product Focus) for image generation
            generated_prompt = prompt_gen.generate_image_prompt_v2(
                product_category=product_category,
                gender=gender,
                age_range=age_range,
                photo_style=photo_style,
                location=location,
                camera_angle=camera_angle,
                custom_details=custom_details
            )

            st.session_state.current_prompt = generated_prompt
            st.session_state.prompt_generated = True
            st.rerun()

    with col_btn2:
        if st.button("🔄 Clear", use_container_width=True):
            st.session_state.current_prompt = ""
            st.session_state.prompt_generated = False
            st.rerun()

    # Display and edit prompt
    if st.session_state.prompt_generated or st.session_state.current_prompt:
        st.subheader("✏️ แก้ไข Prompt")
        edited_prompt = st.text_area(
            "Prompt สำหรับสร้างภาพ (สามารถแก้ไขได้)",
            value=st.session_state.current_prompt,
            height=150,
            key="prompt_editor",
            help="แก้ไข prompt ตามต้องการก่อนสร้างภาพ"
        )
        # Update session state with edited prompt
        st.session_state.current_prompt = edited_prompt

        # Show character count
        st.caption(f"📊 ความยาว Prompt: {len(edited_prompt)} ตัวอักษร")

        st.divider()

        # Generate image button
        st.header("4️⃣ สร้างภาพ")

        # Show different limits based on engine
        if st.session_state.ai_engine == "Stable Diffusion XL (เป๊ะกว่า)":
            max_images = 4
            default_images = 2
            help_text = "SDXL แนะนำ 2-4 ภาพต่อครั้ง (ใช้เวลานานกว่า DALL-E)"
        else:
            max_images = 5
            default_images = 1
            help_text = "DALL-E สามารถสร้าง 1-5 ภาพต่อครั้ง"

        # Multi-generation mode for better quality
        col_num1, col_num2 = st.columns([2, 1])
        with col_num1:
            num_images = st.selectbox(
                "จำนวนภาพที่สร้าง (สร้างหลายภาพแล้วเลือกที่ดีที่สุด)",
                options=[1, 2, 3, 4],
                index=0,
                help="สร้างหลายภาพพร้อมกัน แล้วเลือกภาพที่ออกมาดีที่สุด (แนะนำ 2-3 ภาพ)"
            )
        with col_num2:
            if num_images > 1:
                st.info(f"💡 จะสร้าง {num_images} ภาพ")

        # Advanced settings (optional)
        with st.expander("⚙️ ตั้งค่าขั้นสูง (Optional)"):
            col_a, col_b = st.columns(2)
            with col_a:
                use_seed = st.checkbox("ล็อก Seed (ภาพซ้ำได้)", value=False)
                if use_seed:
                    seed_value = st.number_input("Seed", min_value=0, max_value=999999, value=42)
                else:
                    seed_value = None
            with col_b:
                prompt_strength = st.slider(
                    "ความแรงของ Reference (ต่ำ = ยึดรูปต้นฉบับมาก)",
                    min_value=0.15,
                    max_value=0.3,
                    value=0.20,
                    step=0.01,
                    help="0.15-0.25 = ยึด reference มากที่สุด (แนะนำ 0.20)"
                )

            st.caption("💡 **คำแนะนำ:** ถ้าสินค้าออกมาไม่เหมือนต้นฉบับ ลด Prompt Strength เหลือ 0.15-0.18")

        if st.button("🎨 สร้างรูปจาก Prompt", type="primary", use_container_width=True):
            # DEBUG: Show validation info
            st.write("---")
            st.write(f"🔍 DEBUG - ข้อมูลตอนกดปุ่ม:")
            st.write(f"- AI Engine: `{st.session_state.ai_engine}`")
            st.write(f"- GEMINI_API_KEY: {'✅ มี' if config.GEMINI_API_KEY else '❌ ไม่มี'}")
            st.write(f"- REPLICATE_API_TOKEN: {'✅ มี' if config.REPLICATE_API_TOKEN else '❌ ไม่มี'}")
            st.write(f"- uploaded_reference_images: {len(st.session_state.uploaded_reference_images)} ไฟล์")
            st.write(f"- รายการไฟล์: {st.session_state.uploaded_reference_images}")
            st.write("---")

            # Validate based on AI engine
            if st.session_state.ai_engine == "Kie.ai Nano Banana (แนะนำสุด! ไม่มี Content Filter)":
                if not config.KIE_API_KEY:
                    st.error("❌ กรุณากรอก Kie.ai API Key ในแถบด้านข้าง")
                    return
                if not config.IMGBB_API_KEY:
                    st.error("❌ กรุณากรอก imgbb API Key ในแถบด้านข้าง (สำหรับอัปโหลดรูปอัตโนมัติ)")
                    st.info("💡 ขอ API Key ฟรีได้ที่: https://api.imgbb.com/")
                    return
                if not config.GEMINI_API_KEY:
                    st.error("❌ กรุณากรอก Gemini API Key ในแถบด้านข้าง (สำหรับสร้าง prompt)")
                    return
                if not st.session_state.uploaded_reference_images:
                    st.error("❌ กรุณาอัปโหลดรูปสินค้าอ้างอิงสำหรับ Kie.ai Mode")
                    return

            elif st.session_state.ai_engine == "Gemini Imagen (แนะนำ - ใช้ AI ล่าสุด)":
                if not config.GEMINI_API_KEY:
                    st.error("❌ กรุณากรอก Gemini API Key ในแถบด้านข้าง")
                    return

            elif st.session_state.ai_engine == "Gemini + SDXL Hybrid (วิเคราะห์ + สร้างภาพ)":
                if not config.GEMINI_API_KEY:
                    st.error("❌ กรุณากรอก Gemini API Key ในแถบด้านข้าง")
                    return
                if not config.REPLICATE_API_TOKEN:
                    st.error("❌ กรุณากรอก Replicate API Token ในแถบด้านข้าง")
                    return
                if not st.session_state.uploaded_reference_images:
                    st.error("❌ กรุณาอัปโหลดรูปสินค้าอ้างอิงสำหรับ Hybrid Mode")
                    st.error(f"🐛 DEBUG: len(uploaded_reference_images) = {len(st.session_state.uploaded_reference_images)}")
                    return
                    
            elif st.session_state.ai_engine == "Gemini Pro Vision (วิเคราะห์อย่างเดียว)":
                if not config.GEMINI_API_KEY:
                    st.error("❌ กรุณากรอก Gemini API Key ในแถบด้านข้าง")
                    return
                if not st.session_state.uploaded_reference_images:
                    st.error("❌ กรุณาอัปโหลดรูปสินค้าอ้างอิงสำหรับ Gemini Vision Mode")
                    return
                    
            elif st.session_state.ai_engine == "Stable Diffusion XL (เป๊ะกว่า)":
                if not config.REPLICATE_API_TOKEN:
                    st.error("❌ กรุณากรอก Replicate API Token ในแถบด้านข้าง")
                    return

                if not st.session_state.uploaded_reference_images:
                    st.error("❌ กรุณาอัปโหลดรูปสินค้าอ้างอิงสำหรับ SDXL Mode")
                    return
            else:
                if not config.OPENAI_API_KEY:
                    st.error("❌ กรุณากรอก OpenAI API Key ในแถบด้านข้าง")
                    return

            if not st.session_state.current_prompt.strip():
                st.error("❌ กรุณาสร้าง Prompt ก่อน")
                return

            # DEBUG: Show prompt being sent
            with st.expander("🔍 DEBUG: Prompt ที่จะส่งไป AI"):
                st.code(st.session_state.current_prompt, language="text")
                st.caption(f"ความยาว: {len(st.session_state.current_prompt)} ตัวอักษร")
                st.caption(f"AI Engine: {st.session_state.ai_engine}")

            # Get advanced settings
            advanced_params = {
                'seed': seed_value if use_seed else None,
                'prompt_strength': prompt_strength if st.session_state.ai_engine == "Stable Diffusion XL (เป๊ะกว่า)" else None
            }

            generate_images_from_prompt(
                st.session_state.current_prompt,
                product_category,
                gender,
                age_range,
                num_images,
                ai_engine=st.session_state.ai_engine,
                advanced_params=advanced_params,
                photo_style=photo_style,
                location=location,
                camera_angle=camera_angle
            )

        # ========== BATCH GENERATION SECTION (ถ้ามีสินค้าโหลดมาแล้ว) ==========
        if 'batch_products' in st.session_state and len(st.session_state.batch_products) > 0:
            st.divider()
            st.header("🚀 Batch Auto-Generate")
            st.info(f"📦 พบสินค้าที่โหลดมา {len(st.session_state.batch_products)} รายการ - พร้อมสร้างแบบ Auto!")

            col_batch1, col_batch2 = st.columns([2, 1])

            with col_batch1:
                num_images_per_product = st.selectbox(
                    "จำนวนภาพต่อสินค้า (Batch Mode)",
                    options=[1, 2, 3, 4],
                    index=0,
                    help="แต่ละสินค้าจะสร้างภาพกี่ภาพ"
                )

            with col_batch2:
                st.metric("รวมภาพทั้งหมด", len(st.session_state.batch_products) * num_images_per_product)

            if st.button("🚀 สร้างภาพทุกสินค้าอัตโนมัติ", type="primary", use_container_width=True):
                batch_generate_all_products(
                    product_category=product_category,
                    gender=gender,
                    age_range=age_range,
                    photo_style=photo_style,
                    location=location,
                    camera_angle=camera_angle,
                    custom_details=custom_details,
                    num_images_per_product=num_images_per_product,
                    ai_engine=st.session_state.ai_engine
                )


def generate_images_from_prompt(prompt, product_category, gender, age_range, num_images, ai_engine="DALL·E 3 (ปกติ)", advanced_params=None, photo_style=None, location=None, camera_angle=None, skip_display=False):
    """Generate images using selected AI engine from given prompt

    Args:
        skip_display: If True, skip displaying images (used in batch processing)
    """

    # Initialize generators
    _, dalle_gen, _ = initialize_generators()

    if not dalle_gen:
        st.error("Failed to initialize generator. Please check your API key.")
        return

    # Generate images
    progress_bar = st.progress(0)
    status_text = st.empty()

    print(f"Starting loop: Will generate {num_images} image(s)")

    for i in range(num_images):
        try:
            print(f"Loop iteration {i+1}/{num_images}")

            if ai_engine == "Kie.ai Nano Banana (แนะนำสุด! ไม่มี Content Filter)":
                status_text.text(f"🚀 กำลังสร้างภาพด้วย Kie.ai Nano Banana ที่ {i+1} จาก {num_images}...")

                # Get reference image
                ref_image = st.session_state.uploaded_reference_images[i % len(st.session_state.uploaded_reference_images)]
                print(f"Using reference image: {ref_image}")

                # DEBUG: Print prompt to console
                print("="*80)
                print("[DEBUG] KIE.AI NANO BANANA Generation")
                print("="*80)
                print(prompt)
                print("="*80)

                # Initialize Kie.ai generator
                kie_gen = KieGenerator()

                # Extract English name from product_category for ASCII-safe filename
                english_name = product_category.split('(')[1].split(')')[0].strip().lower().replace(' ', '_')

                # Auto-upload and generate image with Kie.ai Nano Banana
                # Images will be automatically uploaded to imgbb
                status_text.text(f"📤 กำลังอัปโหลดรูปสินค้าอัตโนมัติ...")

                result = kie_gen.generate_image(
                    prompt=prompt,
                    reference_image_paths=[ref_image],  # Local path - will auto-upload
                    filename_prefix=f"kie_{english_name}",
                    image_size="9:16",
                    imgbb_api_key=config.IMGBB_API_KEY
                )

                print(f"Kie.ai generation {i+1} completed successfully")

                # Store in session state
                image_data = {
                    'path': result['path'],
                    'url': result['url'],
                    'prompt': prompt,
                    'revised_prompt': prompt,
                    'product_category': product_category,
                    'gender': gender,
                    'age_range': age_range,
                    'photo_style': photo_style,
                    'location': location,
                    'camera_angle': camera_angle,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'ai_engine': 'Kie.ai Nano Banana',
                    'task_id': result.get('task_id', '')
                }

            elif ai_engine == "Gemini Imagen (แนะนำ - ใช้ AI ล่าสุด)":
                status_text.text(f"🌟 กำลังสร้างภาพด้วย Gemini Imagen ที่ {i+1} จาก {num_images}...")

                print("="*80)
                print("[DEBUG] GEMINI IMAGEN Generation")
                print("="*80)
                print(prompt)
                print("="*80)

                # Generate with Gemini Imagen
                english_name = product_category.split('(')[1].split(')')[0].strip().lower().replace(' ', '_')

                result = dalle_gen.generate_image(
                    prompt=prompt,
                    filename_prefix=f"imagen_{english_name}"
                )

                print(f"Gemini Imagen generation {i+1} completed successfully")

                # Store in session state
                image_data = {
                    'path': result['path'],
                    'url': result.get('url', ''),
                    'prompt': prompt,
                    'revised_prompt': result.get('revised_prompt', prompt),
                    'product_category': product_category,
                    'gender': gender,
                    'age_range': age_range,
                    'photo_style': photo_style,
                    'location': location,
                    'camera_angle': camera_angle,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'ai_engine': 'Gemini Imagen'
                }

            elif ai_engine == "Gemini + SDXL Hybrid (วิเคราะห์ + สร้างภาพ)":
                status_text.text(f"🔮 กำลังวิเคราะห์ด้วย Gemini + สร้างภาพด้วย SDXL ที่ {i+1} จาก {num_images}...")

                # Get reference image
                ref_image = st.session_state.uploaded_reference_images[i % len(st.session_state.uploaded_reference_images)]
                print(f"Using reference image: {ref_image}")

                # DEBUG: Print prompt to console
                print("="*80)
                print("[DEBUG] HYBRID: Gemini Analysis + SDXL Generation")
                print("="*80)
                print(prompt)
                print("="*80)

                # Generate image with Hybrid approach
                # Extract English name from product_category for ASCII-safe filename
                english_name = product_category.split('(')[1].split(')')[0].strip().lower().replace(' ', '_')

                result = dalle_gen.generate_with_gemini_analysis_then_sdxl(
                    prompt=prompt,
                    reference_image_path=ref_image,
                    filename_prefix=f"hybrid_{english_name}"
                )

                print(f"Hybrid generation {i+1} completed successfully")

                # Store in session state
                image_data = {
                    'path': result['path'],
                    'url': result['url'],
                    'prompt': result.get('prompt', prompt),
                    'revised_prompt': result.get('prompt', prompt),
                    'product_category': product_category,
                    'gender': gender,
                    'age_range': age_range,
                    'photo_style': photo_style,
                    'location': location,
                    'camera_angle': camera_angle,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'ai_engine': 'Gemini + SDXL Hybrid',
                    'analysis': result.get('analysis', ''),
                    'analysis_file': result.get('analysis_file', '')
                }

            elif ai_engine == "Gemini Pro Vision (วิเคราะห์อย่างเดียว)":
                status_text.text(f"🔮 กำลังวิเคราะห์ด้วย Gemini Vision ที่ {i+1} จาก {num_images}...")

                # Get reference image
                ref_image = st.session_state.uploaded_reference_images[i % len(st.session_state.uploaded_reference_images)]
                print(f"Using reference image: {ref_image}")

                # DEBUG: Print prompt to console
                print("="*80)
                print("[DEBUG] GEMINI VISION ANALYSIS")
                print("="*80)
                print(prompt)
                print("="*80)

                # Generate analysis with Gemini Pro Vision
                # Extract English name from product_category for ASCII-safe filename
                english_name = product_category.split('(')[1].split(')')[0].strip().lower().replace(' ', '_')

                result = dalle_gen.generate_with_gemini_vision(
                    prompt=prompt,
                    reference_image_path=ref_image,
                    filename_prefix=f"gemini_{english_name}"
                )

                print(f"Analysis {i+1} completed successfully")

                # Store in session state
                image_data = {
                    'path': result['path'],
                    'url': result['url'],
                    'prompt': prompt,
                    'revised_prompt': prompt,  # Gemini Vision doesn't revise prompt
                    'product_category': product_category,
                    'gender': gender,
                    'age_range': age_range,
                    'photo_style': photo_style,
                    'location': location,
                    'camera_angle': camera_angle,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'ai_engine': 'Gemini Vision Analysis',
                    'analysis': result.get('analysis', ''),
                    'analysis_file': result.get('analysis_file', '')
                }

            elif ai_engine == "Stable Diffusion XL (เป๊ะกว่า)":
                status_text.text(f"🔄 กำลังสร้างภาพด้วย SDXL ที่ {i+1} จาก {num_images}...")

                # Get reference image
                ref_image = st.session_state.uploaded_reference_images[i % len(st.session_state.uploaded_reference_images)]
                print(f"Using reference image: {ref_image}")

                # DEBUG: Print prompt to console
                print("="*80)
                print("[DEBUG] PROMPT ที่ส่งไป SDXL")
                print("="*80)
                print(prompt)
                print("="*80)

                # Generate image with SDXL Smart (Simple img2img)
                # Extract English name from product_category for ASCII-safe filename
                english_name = product_category.split('(')[1].split(')')[0].strip().lower().replace(' ', '_')

                # Pass advanced params if available
                seed = advanced_params.get('seed') if advanced_params else None
                prompt_str = advanced_params.get('prompt_strength', 0.20) if advanced_params else 0.20

                # For multi-generation: use different seeds for variety
                actual_seed = seed if seed is not None else (42 + i * 123)

                result = dalle_gen.generate_with_sdxl_simple(
                    prompt=prompt,
                    reference_image_path=ref_image,
                    filename_prefix=f"sdxl_{english_name}",
                    seed=actual_seed,
                    prompt_strength=prompt_str
                )

                print(f"Image {i+1} generated successfully")

                # Store in session state
                image_data = {
                    'path': result['path'],
                    'url': result['url'],
                    'prompt': prompt,
                    'revised_prompt': prompt,  # SDXL doesn't revise prompt
                    'product_category': product_category,
                    'gender': gender,
                    'age_range': age_range,
                    'photo_style': photo_style,
                    'location': location,
                    'camera_angle': camera_angle,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'ai_engine': 'SDXL'
                }

            else:
                status_text.text(f"🎨 กำลังสร้างภาพด้วย DALL-E ที่ {i+1} จาก {num_images}...")

                # Generate image with DALL-E
                result = dalle_gen.generate_image(
                    prompt=prompt,
                    filename_prefix=f"dalle_{product_category.split('(')[0].strip()}"
                )

                # Store in session state
                image_data = {
                    'path': result['path'],
                    'url': result['url'],
                    'prompt': prompt,
                    'revised_prompt': result.get('revised_prompt', prompt),
                    'product_category': product_category,
                    'gender': gender,
                    'age_range': age_range,
                    'photo_style': photo_style,
                    'location': location,
                    'camera_angle': camera_angle,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'ai_engine': 'DALL-E'
                }

            st.session_state.generated_images.append(image_data)
            st.session_state.prompts_data.append(image_data)

            progress_bar.progress((i + 1) / num_images)

        except Exception as e:
            error_msg = str(e)

            # Check if it's a content filter error
            if "content_policy_violation" in error_msg or "content filter" in error_msg.lower():
                st.error(f"❌ ภาพที่ {i+1}: ถูกบลอกโดย Content Filter ของ OpenAI")
                st.warning(
                    "💡 **คำแนะนำ:** ลองแก้ไข Prompt โดย:\n"
                    "- ลดรายละเอียดเกี่ยวกับคน\n"
                    "- ใช้คำที่เป็นกลางมากขึ้น\n"
                    "- เน้นที่สินค้ามากกว่าผู้สวมใส่\n"
                    "- หลีกเลี่ยงคำที่อาจละเอียดเกินไป"
                )
            else:
                st.error(f"Error generating image {i+1}: {error_msg}")

    status_text.text("✅ สร้างภาพเสร็จสิ้น!")
    progress_bar.empty()
    status_text.empty()

    if not skip_display:
        st.success(f"สร้างภาพสำเร็จ {num_images} ภาพ!")
        # Display newly generated images
        display_generated_images()
        # Show latest images gallery
        show_latest_images_gallery()


def show_latest_images_gallery(n=20):
    """Show latest generated images from folder"""
    from pathlib import Path
    import os
    import subprocess

    st.subheader("📸 แกลเลอรีภาพล่าสุด")

    # Get latest images from folder
    images_path = Path("results/images")
    if not images_path.exists():
        st.info("ยังไม่มีภาพในโฟลเดอร์")
        return

    # Get latest n images (exclude temp files)
    all_image_files = sorted(
        [p for p in images_path.glob("*.png") if not p.name.startswith("temp_")],
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    if not all_image_files:
        st.info("ยังไม่มีภาพที่สร้าง")
        return

    total_in_folder = len(all_image_files)
    image_files = all_image_files[:n]

    # Info and button
    col_info, col_btn = st.columns([2, 1])
    with col_info:
        st.info(f"📊 **พบภาพทั้งหมด {total_in_folder} ภาพ** | แสดง {len(image_files)} ภาพล่าสุด")
    with col_btn:
        import time
        gallery_btn_key = f"open_gallery_folder_{int(time.time() * 1000)}"
        if st.button("📂 เปิดโฟลเดอร์ภาพ", key=gallery_btn_key):
            folder_path = os.path.abspath("results/images")
            try:
                subprocess.Popen(f'explorer "{folder_path}"')
                st.success("เปิดโฟลเดอร์แล้ว!")
            except Exception as e:
                st.error(f"ไม่สามารถเปิดโฟลเดอร์: {e}")

    # Display in grid (4 columns for better view)
    cols_per_row = 4
    for i in range(0, len(image_files), cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            idx = i + j
            if idx < len(image_files):
                img_path = image_files[idx]
                with cols[j]:
                    try:
                        st.image(str(img_path), caption=img_path.name, use_column_width=True)
                    except Exception as e:
                        st.error(f"Error: {e}")


def display_generated_images():
    """Display generated images with controls"""

    if not st.session_state.generated_images:
        st.info("ยังไม่มีภาพที่สร้าง")
        return

    # Number of recent images to show
    RECENT_LIMIT = 5

    # Auto-archive old images if more than RECENT_LIMIT
    if len(st.session_state.generated_images) > RECENT_LIMIT:
        images_to_archive = st.session_state.generated_images[:-RECENT_LIMIT]
        st.session_state.gallery_images.extend(images_to_archive)
        st.session_state.generated_images = st.session_state.generated_images[-RECENT_LIMIT:]
        # Don't show message, just archive silently

    total_images = len(st.session_state.generated_images)
    gallery_count = len(st.session_state.gallery_images)

    st.subheader(f"🖼️ ภาพที่สร้างล่าสุด")

    # Info and buttons row
    col_info, col_folder = st.columns([3, 1])

    with col_info:
        st.info(f"📊 **ภาพพรีวิว:** {total_images} ภาพ | **แกลเลอรี่:** {gallery_count} ภาพ")

    with col_folder:
        import subprocess
        import os
        import time
        folder_key = f"open_all_images_folder_{int(time.time() * 1000)}"
        if st.button("📁 เปิดโฟลเดอร์", key=folder_key):
            folder_path = os.path.abspath("results/images")
            try:
                subprocess.Popen(f'explorer "{folder_path}"')
                st.success("เปิดโฟลเดอร์แล้ว!")
            except Exception as e:
                st.error(f"Error: {e}")

    # Show recent images
    recent_images = st.session_state.generated_images
    st.caption(f"แสดง {len(recent_images)} ภาพล่าสุด (ภาพทั้งหมดดูได้ในแท็บ 📷 Gallery)")

    # Show latest image only
    img_data = recent_images[-1]
    idx = 0  # Always 0 for latest image

    with st.container():
        col1, col2 = st.columns([1, 2])

        with col1:
            # Display image
            try:
                image = Image.open(img_data['path'])
                st.image(image, use_column_width=True)
            except Exception as e:
                st.error(f"Error loading image: {e}")

        with col2:
            # Display info
            st.markdown(f"**Product:** {img_data['product_category']}")
            st.markdown(f"**Gender:** {img_data['gender']}")
            st.markdown(f"**Age Range:** {img_data['age_range']}")
            st.markdown(f"**Created:** {img_data['timestamp']}")

            # Show prompt
            with st.expander("View Prompt"):
                st.text(img_data['prompt'])

            # Action buttons
            col_a, col_b = st.columns(2)

            with col_a:
                if st.button(f"🔄 Re-generate", key=f"regen_{idx}"):
                    regenerate_image(img_data)

            with col_b:
                if st.button(f"✏️ Edit Prompt", key=f"edit_{idx}"):
                    st.session_state[f'editing_{idx}'] = True

            # Edit prompt section
            if st.session_state.get(f'editing_{idx}', False):
                new_prompt = st.text_area(
                    "Edit Prompt",
                    value=img_data['prompt'],
                    key=f"prompt_edit_{idx}"
                )
                if st.button("Generate with New Prompt", key=f"gen_new_{idx}"):
                    generate_from_edited_prompt(new_prompt, img_data)
                    st.session_state[f'editing_{idx}'] = False
                    st.rerun()

            st.divider()


def regenerate_image(img_data):
    """Regenerate an image with the same prompt"""

    _, dalle_gen, _ = initialize_generators()

    if not dalle_gen:
        st.error("Failed to initialize generator")
        return

    with st.spinner("กำลังสร้างภาพใหม่..."):
        try:
            result = dalle_gen.regenerate_image(
                prompt=img_data['prompt'],
                filename_prefix="regenerated"
            )

            # Add to session state
            new_image_data = {
                **img_data,
                'path': result['path'],
                'url': result['url'],
                'revised_prompt': result['revised_prompt'],
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            st.session_state.generated_images.append(new_image_data)
            st.session_state.prompts_data.append(new_image_data)

            st.success("สร้างภาพใหม่สำเร็จ!")
            st.rerun()

        except Exception as e:
            st.error(f"Error: {str(e)}")


def generate_from_edited_prompt(new_prompt, original_img_data):
    """Generate image from edited prompt"""

    _, dalle_gen, _ = initialize_generators()

    if not dalle_gen:
        st.error("Failed to initialize generator")
        return

    with st.spinner("กำลังสร้างภาพจาก prompt ใหม่..."):
        try:
            result = dalle_gen.generate_image(
                prompt=new_prompt,
                filename_prefix="edited"
            )

            # Add to session state
            new_image_data = {
                **original_img_data,
                'path': result['path'],
                'url': result['url'],
                'prompt': new_prompt,
                'revised_prompt': result['revised_prompt'],
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            st.session_state.generated_images.append(new_image_data)
            st.session_state.prompts_data.append(new_image_data)

            st.success("สร้างภาพจาก prompt ใหม่สำเร็จ!")

        except Exception as e:
            st.error(f"Error: {str(e)}")


def create_video_tab():
    """Create video from images"""

    st.header("🎬 สร้างคลิปวิดีโอโฆษณา")

    # Show Kie.ai credits at the top
    if config.KIE_API_KEY and config.KIE_API_KEY.strip():
        from kie_generator import KieGenerator
        kie_gen = KieGenerator()

        # Initialize credits in session state
        if 'kie_credits' not in st.session_state:
            st.session_state.kie_credits = None

        # Auto-load credits on first visit
        if st.session_state.kie_credits is None:
            try:
                credits_info = kie_gen.get_credits()
                st.session_state.kie_credits = credits_info
            except Exception as e:
                # Don't show error if it's 404 (endpoint not available)
                if '404' in str(e):
                    st.session_state.kie_credits = {'success': False, 'error': 'Credits API not available', 'silent': True}
                else:
                    st.session_state.kie_credits = {'success': False, 'error': str(e)}

        col_credit1, col_credit2, col_credit3 = st.columns([2, 1, 1])

        with col_credit1:
            # Show credits
            if st.session_state.kie_credits is not None:
                credits_info = st.session_state.kie_credits
                if credits_info.get('success'):
                    credits = credits_info.get('credits', 0)
                    # Format credits - ถ้าเป็นเลขจำนวนเต็ม ไม่แสดงทศนิยม
                    if isinstance(credits, (int, float)):
                        if credits == int(credits):
                            credits_formatted = f"{int(credits):,}"
                        else:
                            credits_formatted = f"{credits:,.2f}"
                    else:
                        credits_formatted = str(credits)

                    # แสดงเครดิตแบบเด่นชัด
                    st.success(f"💰 **เครดิตคงเหลือ: {credits_formatted} credits**")
                else:
                    # Don't show error if it's silent (404)
                    if not credits_info.get('silent'):
                        st.warning(f"⚠️ ไม่สามารถดึงข้อมูลเครดิต: {credits_info.get('error', 'Unknown error')}")
                    else:
                        st.info("💰 **เครดิต:** ไม่สามารถดึงข้อมูลได้ (API ไม่รองรับ)")
            else:
                st.info("💰 **เครดิต:** กำลังโหลด...")

        with col_credit2:
            if st.button("🔄 Refresh เครดิต", use_container_width=True):
                try:
                    with st.spinner("กำลังดึงข้อมูลเครดิต..."):
                        credits_info = kie_gen.get_credits()
                        st.session_state.kie_credits = credits_info
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")

        with col_credit3:
            # Button to top up credits
            st.markdown("""
            <a href="https://kie.ai/billing" target="_blank">
                <button style="
                    width: 100%;
                    padding: 0.5rem 1rem;
                    background-color: #FF4B4B;
                    color: white;
                    border: none;
                    border-radius: 0.5rem;
                    cursor: pointer;
                    font-size: 1rem;
                    font-weight: 500;
                ">💳 เติมเครดิต</button>
            </a>
            """, unsafe_allow_html=True)

        st.divider()
    else:
        st.warning("⚠️ กรุณากรอก Kie.ai API Key ในแถบด้านข้างเพื่อดูเครดิตคงเหลือ")
        st.divider()

    # Video generation method selection
    video_method = st.radio(
        "🎥 เลือกวิธีการสร้างวิดีโอ",
        options=[
            "Sora 2 (OpenAI - ให้ภาพเคลื่อนไหว AI)",
            "Veo3 (Google AI - ให้คนในภาพเคลื่อนไหว)"
        ],
        help="Sora 2 = OpenAI image-to-video (1 ภาพ) | Veo3 = Google AI image-to-video แบบ cinematic (1 ภาพ)"
    )

    if video_method.startswith("Sora 2"):
        create_sora2_video_section()
    elif video_method.startswith("Veo3"):
        create_veo3_video_section()


def display_image_selector_sora2(images, key_prefix):
    """Helper function to display image selector for Sora2 (single image)"""
    if not images:
        return None

    st.caption(f"แสดง {len(images)} ภาพ")

    # Create dropdown with image names
    image_options = []
    for idx, img_data in enumerate(images):
        img_name = Path(img_data['path']).name
        timestamp = img_data.get('timestamp', '')
        image_options.append(f"{idx+1}. {img_name} ({timestamp})")

    selected_option = st.selectbox(
        "เลือกภาพที่ต้องการสร้างวิดีโอ",
        options=image_options,
        key=f"{key_prefix}_select"
    )

    # Get selected index
    selected_idx = int(selected_option.split('.')[0]) - 1
    selected_img_data = images[selected_idx]
    selected_image_path = selected_img_data['path']

    # Show preview
    col_preview1, col_preview2, col_preview3 = st.columns([1, 2, 1])
    with col_preview2:
        st.image(str(selected_image_path), caption=Path(selected_image_path).name, width=200)
        st.caption(f"🏷️ {selected_img_data.get('product_category', 'N/A')}")
        st.caption(f"🕐 {selected_img_data.get('timestamp', 'N/A')}")

    return selected_image_path


def create_sora2_video_section():
    """Create video using Sora 2 (OpenAI image-to-video)"""
    st.subheader("🎬 Sora 2 AI Video Generation (OpenAI)")

    # Show info about available images
    total_images = len(st.session_state.generated_images) + len(st.session_state.gallery_images)
    if total_images > 0:
        st.info(f"📊 มีภาพทั้งหมด {total_images} ภาพ (ล่าสุด: {len(st.session_state.generated_images)} | แกลเลอรี่: {len(st.session_state.gallery_images)})")
    else:
        st.info("📝 สามารถสร้างวิดีโอได้โดยใส่ URL ของภาพที่อัปโหลดไว้ที่ hosting service")

    # Sora 2 limitations
    st.warning("⚠️ **สำคัญ:** Sora 2 ใช้ภาพ 1 ภาพในการสร้างวิดีโอ (image-to-video)")
    st.error("🚫 **ข้อจำกัด Sora 2:** ไม่สามารถใช้ภาพที่มีคนจริง (photorealistic people) ได้")
    st.info("💡 **แนะนำ:** ถ้าภาพมีคน ให้ใช้ **Veo3** แทน (เลือกที่ด้านบน)")

    # Image selection method
    col_method1, col_method2 = st.columns(2)
    with col_method1:
        image_method = st.radio(
            "เลือกวิธีการใส่ภาพ",
            options=["📂 เลือกจากภาพที่สร้างแล้ว", "🌐 ใส่ URL เอง"],
            key="sora2_image_method"
        )

    # Initialize image_url
    image_url = ""
    selected_image_path = None

    if image_method == "📂 เลือกจากภาพที่สร้างแล้ว":
        # Try to get images from folder first
        from pathlib import Path
        images_path = Path("results/images")
        folder_images = []

        if images_path.exists():
            image_files = sorted(
                [p for p in images_path.glob("*.png") if not p.name.startswith("temp_")],
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            # Convert folder images to dict format
            for img_path in image_files[:50]:  # Limit to 50 latest images
                folder_images.append({
                    'path': str(img_path),
                    'product_category': 'N/A',
                    'timestamp': datetime.fromtimestamp(img_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                })

        # Combine all sources
        all_gallery_images = st.session_state.generated_images + st.session_state.gallery_images + folder_images

        if all_gallery_images:
            # Add filter tabs
            tab_filter1, tab_filter2, tab_filter3, tab_filter4 = st.tabs(["📸 ทั้งหมด", "🆕 ล่าสุด", "🗂️ เก็บแล้ว", "📁 จากโฟลเดอร์"])

            with tab_filter1:
                selected_image_path = display_image_selector_sora2(all_gallery_images, "sora2_all")

            with tab_filter2:
                if st.session_state.generated_images:
                    selected_image_path = display_image_selector_sora2(st.session_state.generated_images, "sora2_recent")
                else:
                    st.info("ยังไม่มีภาพล่าสุด")
                    selected_image_path = None

            with tab_filter3:
                if st.session_state.gallery_images:
                    selected_image_path = display_image_selector_sora2(st.session_state.gallery_images, "sora2_archived")
                else:
                    st.info("ยังไม่มีภาพที่เก็บแล้ว")
                    selected_image_path = None

            with tab_filter4:
                if folder_images:
                    selected_image_path = display_image_selector_sora2(folder_images, "sora2_folder")
                else:
                    st.info("ยังไม่มีภาพในโฟลเดอร์ results/images")
                    selected_image_path = None

            if selected_image_path:
                st.info("💡 ระบบจะอัปโหลดภาพนี้ไปที่ imgbb อัตโนมัติเมื่อกดสร้างวิดีโอ")
        else:
            st.warning("⚠️ ไม่พบภาพในแกลเลอรี่และโฟลเดอร์ กรุณาสร้างภาพก่อน หรือใช้วิธี 'ใส่ URL เอง'")

    else:
        # Manual URL input
        st.info("📝 กรุณาอัปโหลดภาพที่สร้างไปที่ hosting service (เช่น imgbb.com, imgur.com) แล้วใส่ URL ด้านล่าง")
        image_url = st.text_input(
            "🌐 URL ของภาพ (สำหรับ Sora 2)",
            key="sora2_img_url",
            help="ใส่ URL ของภาพที่ต้องการใช้สร้างวิดีโอ (ต้อง public accessible)"
        )

    # Option to generate video prompt
    col_vprompt1, col_vprompt2 = st.columns([3, 1])

    with col_vprompt1:
        st.subheader("📝 Prompt สำหรับวิดีโอ")

    with col_vprompt2:
        if st.button("🎬 สร้าง Video Prompt", key="sora2_gen_prompt", use_container_width=True):
            # Get product info from latest generated image if available
            if st.session_state.generated_images:
                latest = st.session_state.generated_images[-1]
                product_cat = latest.get('product_category', 'รองเท้า (Shoes)')
                gender_val = latest.get('gender', 'หญิง (Female)')
                age_val = latest.get('age_range', '18-25')
            else:
                product_cat = "รองเท้า (Shoes)"
                gender_val = "หญิง (Female)"
                age_val = "18-25"

            # Generate video prompt
            from prompt_generator import PromptGenerator
            prompt_gen = PromptGenerator()

            # Use Minimal Background as default for video
            default_location = "Minimal Background (แนะนำ - เน้นสินค้า)"

            video_prompt_generated = prompt_gen.generate_video_prompt(
                product_category=product_cat,
                gender=gender_val,
                age_range=age_val,
                location=default_location
            )

            st.session_state['sora2_video_prompt'] = video_prompt_generated
            st.rerun()

    # Video prompt text area
    default_sora2_prompt = st.session_state.get('sora2_video_prompt',
        "A woman is standing in a natural pose, wearing stylish shoes. She gently lifts one foot with toes touching the ground, pointing slightly down to highlight the footwear. After a brief pause, she slowly starts walking forward in a relaxed, smooth motion. The camera stays low and focused only on her legs and shoes — no face shown.")

    video_prompt = st.text_area(
        "แก้ไข prompt สำหรับวิดีโอ (อธิบายการเคลื่อนไหว)",
        value=default_sora2_prompt,
        height=150,
        help="อธิบายว่าต้องการให้วิดีโอมีการเคลื่อนไหวอย่างไร"
    )

    # Video settings
    st.subheader("⚙️ ตั้งค่าวิดีโอ")

    col1, col2, col3 = st.columns(3)

    with col1:
        aspect_ratio = st.selectbox(
            "อัตราส่วนภาพ",
            options=["portrait", "landscape"],
            index=0,
            help="portrait = 9:16 (มือถือ) | landscape = 16:9 (จอกว้าง)"
        )

    with col2:
        remove_watermark = st.checkbox(
            "ลบ Watermark",
            value=True,
            help="ลบ watermark ออกจากวิดีโอ"
        )

    with col3:
        video_filename = st.text_input(
            "ชื่อไฟล์วิดีโอ",
            value=f"sora2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        )

    # Create video button
    if st.button("🎬 สร้างวิดีโอด้วย Sora 2", type="primary", use_container_width=True):
        if not config.KIE_API_KEY:
            st.error("❌ กรุณากรอก Kie.ai API Key ในแถบด้านข้าง (Sora 2 ใช้ผ่าน Kie.ai)")
            return

        # Check if we have image (either URL or selected from folder)
        if not image_url.strip() and not selected_image_path:
            st.error("❌ กรุณาเลือกภาพหรือใส่ URL ของภาพ")
            return

        if not video_prompt.strip():
            st.error("❌ กรุณากรอก Prompt สำหรับวิดีโอ")
            return

        # If selected from folder, upload to imgbb first
        final_image_url = image_url
        if selected_image_path and not image_url:
            if not config.IMGBB_API_KEY:
                st.error("❌ กรุณากรอก imgbb API Key ในแถบด้านข้าง (สำหรับอัปโหลดรูปอัตโนมัติ)")
                st.info("💡 ขอ API Key ฟรีได้ที่: https://api.imgbb.com/")
                return

            with st.spinner("📤 กำลังอัปโหลดภาพไปที่ imgbb..."):
                try:
                    from kie_generator import KieGenerator
                    kie_gen = KieGenerator()
                    final_image_url = kie_gen.upload_image_to_imgbb(
                        str(selected_image_path),
                        config.IMGBB_API_KEY
                    )
                    st.success(f"✅ อัปโหลดภาพสำเร็จ!")
                except Exception as e:
                    st.error(f"❌ ไม่สามารถอัปโหลดภาพ: {str(e)}")
                    return

        # Start timer
        import time
        start_time = time.time()
        start_datetime = datetime.now()

        st.info(f"⏰ เริ่มสร้างเมื่อ: {start_datetime.strftime('%H:%M:%S')}")

        with st.spinner("กำลังสร้างวิดีโอด้วย Sora 2... (อาจใช้เวลาหลายนาที)"):
            try:
                sora_creator = Sora2VideoCreator()

                result = sora_creator.create_video_from_image(
                    image_url=final_image_url,
                    prompt=video_prompt,
                    filename=video_filename,
                    aspect_ratio=aspect_ratio,
                    remove_watermark=remove_watermark
                )

                # Calculate elapsed time
                end_time = time.time()
                elapsed_seconds = int(end_time - start_time)
                elapsed_minutes = elapsed_seconds // 60
                elapsed_secs = elapsed_seconds % 60

                if elapsed_minutes > 0:
                    elapsed_str = f"{elapsed_minutes} นาที {elapsed_secs} วินาที"
                else:
                    elapsed_str = f"{elapsed_secs} วินาที"

                st.session_state.video_path = result['path']

                # บันทึกข้อมูลวิดีโอลง list
                video_data = {
                    'path': result['path'],
                    'method': 'Sora 2',
                    'task_id': result.get('task_id', ''),
                    'prompt': video_prompt,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'filename': Path(result['path']).name,
                    'elapsed_time': elapsed_str
                }
                st.session_state.generated_videos.append(video_data)

                st.success(f"✅ สร้างวิดีโอด้วย Sora 2 สำเร็จ! (ใช้เวลา {elapsed_str})")
                st.info(f"📝 Task ID: {result['task_id']}")
                st.info(f"🌐 Image URL: {final_image_url}")

                # Refresh credits after video creation
                st.session_state.kie_credits = None
                st.rerun()

            except Exception as e:
                # Calculate elapsed time even on error
                end_time = time.time()
                elapsed_seconds = int(end_time - start_time)
                elapsed_minutes = elapsed_seconds // 60
                elapsed_secs = elapsed_seconds % 60

                if elapsed_minutes > 0:
                    elapsed_str = f"{elapsed_minutes} นาที {elapsed_secs} วินาที"
                else:
                    elapsed_str = f"{elapsed_secs} วินาที"

                error_msg = str(e)
                st.error(f"❌ Sora 2 Error: {error_msg}")
                st.warning(f"⏱️ ใช้เวลาไปก่อน error: {elapsed_str}")

                # Provide helpful suggestions based on error
                if "photorealistic people" in error_msg.lower() or "contains people" in error_msg.lower():
                    st.warning("🚫 **ภาพนี้มีคนจริง** - Sora 2 ไม่รองรับภาพที่มีคนจริง")
                    st.info("💡 **แนะนำ 2 วิธี:**")
                    st.markdown("""
                    1. **ใช้ Veo3 แทน** - รองรับภาพที่มีคนได้ และเจนภาพเคลื่อนไหวจริง (เลือกที่เมนูด้านบน)
                    2. **ใช้ภาพอื่น** - เลือกภาพที่ไม่มีคน (เช่น ภาพสินค้าอย่างเดียว)
                    """)
                elif "invalid image" in error_msg.lower() or "image format" in error_msg.lower():
                    st.info("💡 ลองตรวจสอบ URL ของภาพว่าสามารถเข้าถึงได้ และเป็นไฟล์ภาพที่ถูกต้อง")
                else:
                    st.info("💡 ลองใช้ **Veo3** แทน หรือติดต่อ support ของ Kie.ai")

    # Display latest video only
    if st.session_state.generated_videos:
        st.divider()
        total_videos = len(st.session_state.generated_videos)
        st.subheader("✅ วิดีโอล่าสุด")
        st.caption(f"วิดีโอทั้งหมด {total_videos} คลิปดูได้ในแท็บ 🎬 Video Gallery")

        # Show latest video
        latest_video = st.session_state.generated_videos[-1]

        # จำกัดขนาดวิดีโอให้เล็กลงและจัดกึ่งกลาง
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            st.video(str(latest_video['path']))
            st.caption(f"📁 {latest_video['filename']}")
            st.caption(f"⚙️ {latest_video['method']} | 🕐 {latest_video['timestamp']}")
            if 'elapsed_time' in latest_video:
                st.caption(f"⏱️ ใช้เวลา: {latest_video['elapsed_time']}")

        # Download button
        with open(latest_video['path'], 'rb') as video_file:
            video_bytes = video_file.read()
            st.download_button(
                label="📥 ดาวน์โหลดวิดีโอนี้",
                data=video_bytes,
                file_name=latest_video['filename'],
                mime="video/mp4",
                use_container_width=True
            )

        st.info(f"📂 วิดีโอทั้งหมดบันทึกที่: `results/videos/`")



def create_veo3_video_section():
    """Create video using Veo3 AI"""
    st.subheader("🎬 Veo3 AI Video Generation")

    # Explain Veo3 capabilities
    st.info("""
    ✨ **Veo3 ใช้ AI เจนภาพเคลื่อนไหว** (แบบเดียวกับ Sora 2)
    - รับภาพ **1 ภาพ** แล้ว Google AI จะ**สร้างวิดีโอที่คนในภาพเคลื่อนไหว**
    - คนในภาพจะเคลื่อนไหว พูด หรือแสดงอารมณ์ได้จริงแบบ cinematic
    - **ไม่ใช่**ต่อหลายภาพเป็นสไลด์โชว์ แต่ AI จะ**เจนเฟรมใหม่**ให้เคลื่อนไหว
    """)

    st.info("""
    ⏱️ **Veo3 ใช้เวลา 3-5 นาที** (หลังจากเพิ่มประสิทธิภาพ)
    💡 **หรือใช้ Sora 2** สำหรับภาพที่ไม่มีคน (เร็วและมั่นคงกว่า)
    """)

    st.success("""
    💡 **วิธีใช้:** เลือก 1 ภาพ → ใส่ prompt บรรยาย → AI เจนเป็นวิดีโอเคลื่อนไหว (3-5 นาที)
    """)

    # Show info about available images
    total_images = len(st.session_state.generated_images) + len(st.session_state.gallery_images)
    if total_images > 0:
        st.info(f"📊 มีภาพทั้งหมด {total_images} ภาพ (ล่าสุด: {len(st.session_state.generated_images)} | แกลเลอรี่: {len(st.session_state.gallery_images)})")
    else:
        st.info("📝 สามารถสร้างวิดีโอได้โดยใส่ URL ของภาพที่อัปโหลดไว้ที่ hosting service")

    # Veo3 accepts 1 image (image-to-video)
    st.warning("⚠️ **สำคัญ:** Veo3 รับภาพ **1 ภาพ** แล้วเจนเป็นวิดีโอที่คนในภาพเคลื่อนไหว (แบบเดียวกับ Sora 2)")

    # Image selection method
    col_method1, col_method2 = st.columns(2)
    with col_method1:
        image_method = st.radio(
            "เลือกวิธีการใส่ภาพ",
            options=["📂 เลือกจากภาพที่สร้างแล้ว", "🌐 ใส่ URL เอง"],
            key="veo3_image_method"
        )

    # Initialize variables
    image_urls = []
    selected_image_paths = []

    if image_method == "📂 เลือกจากภาพที่สร้างแล้ว":
        # Try to get images from folder first
        from pathlib import Path
        images_path = Path("results/images")
        folder_images = []

        if images_path.exists():
            image_files = sorted(
                [p for p in images_path.glob("*.png") if not p.name.startswith("temp_")],
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            # Convert folder images to dict format
            for img_path in image_files[:50]:  # Limit to 50 latest images
                folder_images.append({
                    'path': str(img_path),
                    'product_category': 'N/A',
                    'timestamp': datetime.fromtimestamp(img_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                })

        # Combine all sources
        all_gallery_images = st.session_state.generated_images + st.session_state.gallery_images + folder_images

        if all_gallery_images:
            # Add filter tabs
            tab_filter1, tab_filter2, tab_filter3, tab_filter4 = st.tabs(["📸 ทั้งหมด", "🆕 ล่าสุด", "🗂️ เก็บแล้ว", "📁 จากโฟลเดอร์"])

            with tab_filter1:
                selected_image_path = display_image_selector_sora2(all_gallery_images, "veo3_all")
                selected_image_paths = [selected_image_path] if selected_image_path else []

            with tab_filter2:
                if st.session_state.generated_images:
                    selected_image_path = display_image_selector_sora2(st.session_state.generated_images, "veo3_recent")
                    selected_image_paths = [selected_image_path] if selected_image_path else []
                else:
                    st.info("ยังไม่มีภาพล่าสุด")
                    selected_image_paths = []

            with tab_filter3:
                if st.session_state.gallery_images:
                    selected_image_path = display_image_selector_sora2(st.session_state.gallery_images, "veo3_archived")
                    selected_image_paths = [selected_image_path] if selected_image_path else []
                else:
                    st.info("ยังไม่มีภาพที่เก็บแล้ว")
                    selected_image_paths = []

            with tab_filter4:
                if folder_images:
                    selected_image_path = display_image_selector_sora2(folder_images, "veo3_folder")
                    selected_image_paths = [selected_image_path] if selected_image_path else []
                else:
                    st.info("ยังไม่มีภาพในโฟลเดอร์ results/images")
                    selected_image_paths = []

            if selected_image_paths:
                st.info("💡 ระบบจะอัปโหลดภาพนี้ไปที่ imgbb อัตโนมัติเมื่อกดสร้างวิดีโอ")
        else:
            st.warning("⚠️ ไม่พบภาพในแกลเลอรี่และโฟลเดอร์ กรุณาสร้างภาพก่อน หรือใช้วิธี 'ใส่ URL เอง'")

    else:
        # Manual URL input (single image only)
        st.info("📝 กรุณาอัปโหลดภาพที่สร้างไปที่ hosting service (เช่น imgbb.com, imgur.com) แล้วใส่ URL ด้านล่าง")

        url = st.text_input(
            "🌐 URL ของภาพ",
            key=f"veo_img_url_single",
            help="ใส่ URL ของภาพ 1 ภาพที่จะให้ AI เจนให้เคลื่อนไหว"
        )
        if url:
            image_urls.append(url)

    # Option to generate video prompt
    col_vprompt1, col_vprompt2 = st.columns([3, 1])

    with col_vprompt1:
        st.subheader("📝 Prompt สำหรับวิดีโอ")

    with col_vprompt2:
        if st.button("🎬 สร้าง Video Prompt", use_container_width=True):
            # Get product info from latest generated image if available
            if st.session_state.generated_images:
                latest = st.session_state.generated_images[-1]
                product_cat = latest.get('product_category', 'รองเท้า (Shoes)')
                gender_val = latest.get('gender', 'หญิง (Female)')
                age_val = latest.get('age_range', '18-25')
            else:
                product_cat = "รองเท้า (Shoes)"
                gender_val = "หญิง (Female)"
                age_val = "18-25"

            # Generate video prompt
            from prompt_generator import PromptGenerator
            prompt_gen = PromptGenerator()

            # Use Minimal Background as default for video
            default_location = "Minimal Background (แนะนำ - เน้นสินค้า)"

            video_prompt_generated = prompt_gen.generate_video_prompt(
                product_category=product_cat,
                gender=gender_val,
                age_range=age_val,
                location=default_location
            )

            st.session_state['video_prompt'] = video_prompt_generated
            st.rerun()

    # Video prompt text area
    default_video_prompt = st.session_state.get('video_prompt',
        "Smooth transitions between product showcase images in a modern Thai cafe setting, professional commercial style, cinematic lighting, 9:16 vertical format")

    video_prompt = st.text_area(
        "แก้ไข prompt สำหรับวิดีโอ (หรือกดปุ่มด้านบนเพื่อสร้างอัตโนมัติ)",
        value=default_video_prompt,
        height=150,
        help="อธิบายว่าต้องการให้วิดีโอเป็นอย่างไร"
    )

    # Video settings
    col1, col2 = st.columns(2)
    with col1:
        video_filename = st.text_input(
            "ชื่อไฟล์วิดีโอ",
            value=f"veo3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        )
    with col2:
        watermark = st.text_input(
            "Watermark (ถ้ามี)",
            value="",
            help="ข้อความที่จะแสดงเป็น watermark"
        )

    # Create video button
    if st.button("🎬 สร้างวิดีโอด้วย Veo3", type="primary", use_container_width=True):
        if not config.KIE_API_KEY:
            st.error("❌ กรุณากรอก Kie.ai API Key ในแถบด้านข้าง")
            return

        # Check if we have exactly 1 image
        if len(image_urls) < 1 and len(selected_image_paths) < 1:
            st.error("❌ กรุณาเลือกภาพ 1 ภาพ หรือใส่ URL ของภาพ")
            return

        # Ensure only 1 image is used
        if len(image_urls) > 1:
            st.warning("⚠️ Veo3 รองรับเฉพาะภาพเดียว - จะใช้ภาพแรกเท่านั้น")
            image_urls = [image_urls[0]]

        if len(selected_image_paths) > 1:
            st.warning("⚠️ Veo3 รองรับเฉพาะภาพเดียว - จะใช้ภาพแรกเท่านั้น")
            selected_image_paths = [selected_image_paths[0]]

        if not video_prompt.strip():
            st.error("❌ กรุณากรอก Prompt สำหรับวิดีโอ")
            return

        # If selected from folder, upload to imgbb first
        final_image_urls = image_urls.copy() if image_urls else []

        if selected_image_paths and len(final_image_urls) == 0:
            if not config.IMGBB_API_KEY:
                st.error("❌ กรุณากรอก imgbb API Key ในแถบด้านข้าง (สำหรับอัปโหลดรูปอัตโนมัติ)")
                st.info("💡 ขอ API Key ฟรีได้ที่: https://api.imgbb.com/")
                return

            with st.spinner(f"📤 กำลังอัปโหลดภาพไปที่ imgbb..."):
                try:
                    from kie_generator import KieGenerator
                    kie_gen = KieGenerator()

                    # Upload single image
                    img_path = selected_image_paths[0]
                    st.text(f"อัปโหลดภาพ...")
                    uploaded_url = kie_gen.upload_image_to_imgbb(
                        str(img_path),
                        config.IMGBB_API_KEY
                    )
                    final_image_urls.append(uploaded_url)

                    st.success(f"✅ อัปโหลดภาพสำเร็จ!")
                except Exception as e:
                    st.error(f"❌ ไม่สามารถอัปโหลดภาพ: {str(e)}")
                    return

        # Start timer
        import time
        start_time = time.time()
        start_datetime = datetime.now()

        st.info(f"⏰ เริ่มสร้างเมื่อ: {start_datetime.strftime('%H:%M:%S')}")

        # Create progress placeholder
        progress_placeholder = st.empty()
        status_placeholder = st.empty()

        # Progress callback function
        def update_progress(elapsed, remaining_str, status_method):
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            if minutes > 0:
                time_str = f"{minutes} นาที {seconds} วินาที"
            else:
                time_str = f"{seconds} วินาที"

            progress_placeholder.info(f"⏰ กำลังสร้างวิดีโอ... ใช้เวลาไป: **{time_str}** {remaining_str}")
            status_placeholder.caption(f"📡 สถานะ: {status_method}")

        try:
            veo_creator = Veo3VideoCreator()

            # Pass progress callback
            result = veo_creator.create_video_from_images(
                image_urls=final_image_urls,
                prompt=video_prompt,
                filename=video_filename,
                aspect_ratio="9:16",
                watermark=watermark if watermark else None,
                progress_callback=update_progress
            )

            # Clear progress placeholders
            progress_placeholder.empty()
            status_placeholder.empty()

            # Calculate elapsed time
            end_time = time.time()
            elapsed_seconds = int(end_time - start_time)
            elapsed_minutes = elapsed_seconds // 60
            elapsed_secs = elapsed_seconds % 60

            if elapsed_minutes > 0:
                elapsed_str = f"{elapsed_minutes} นาที {elapsed_secs} วินาที"
            else:
                elapsed_str = f"{elapsed_secs} วินาที"

            st.session_state.video_path = result['path']

            # บันทึกข้อมูลวิดีโอลง list
            video_data = {
                'path': result['path'],
                'method': 'Veo3',
                'task_id': result.get('task_id', ''),
                'prompt': video_prompt,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'filename': Path(result['path']).name,
                'num_images': len(final_image_urls),
                'elapsed_time': elapsed_str
            }
            st.session_state.generated_videos.append(video_data)

            st.success(f"✅ สร้างวิดีโอด้วย Veo3 สำเร็จ! (ใช้เวลา {elapsed_str})")
            st.info(f"📝 Task ID: {result['task_id']}")
            st.info(f"🖼️ เจนจากภาพเดียว (image-to-video)")

            # Refresh credits after video creation
            st.session_state.kie_credits = None
            st.rerun()

        except Exception as e:
            # Clear progress placeholders
            progress_placeholder.empty()
            status_placeholder.empty()

            # Calculate elapsed time even on error
            end_time = time.time()
            elapsed_seconds = int(end_time - start_time)
            elapsed_minutes = elapsed_seconds // 60
            elapsed_secs = elapsed_seconds % 60

            if elapsed_minutes > 0:
                elapsed_str = f"{elapsed_minutes} นาที {elapsed_secs} วินาที"
            else:
                elapsed_str = f"{elapsed_secs} วินาที"

            import traceback
            error_details = traceback.format_exc()

            st.error(f"❌ Veo3 Error: {str(e)}")
            st.warning(f"⏱️ ใช้เวลาไปก่อน error: {elapsed_str}")

            # Show detailed error in expander
            with st.expander("🔍 ดูรายละเอียด Error (สำหรับ debug)"):
                st.code(error_details)

            # Provide helpful suggestions
            error_msg = str(e).lower()
            if "timeout" in error_msg:
                st.warning("⏱️ **Timeout** - Veo3 ใช้เวลานานกว่า 15 นาที")
                st.info("💡 **แนะนำ:**\n- ลองใหม่อีกครั้ง (บางครั้งอาจสำเร็จ)\n- หรือใช้ Sora 2 แทน (เร็วกว่า ~3-5 นาที)")
            elif "webhook" in error_msg or "callback" in error_msg:
                st.warning("📞 **Webhook Error** - ไม่สามารถรับผลลัพธ์จาก API")
                st.info("💡 ตรวจสอบว่าเครือข่ายเชื่อมต่อได้ปกติ")
            elif "api key" in error_msg or "authorization" in error_msg:
                st.warning("🔑 **API Key Error** - ตรวจสอบ Kie.ai API Key")
                st.info("💡 กรอก API Key ในแถบด้านข้าง")
            elif "image" in error_msg and "url" in error_msg:
                st.warning("🖼️ **Image URL Error** - ไม่สามารถเข้าถึงภาพได้")
                st.info("💡 ตรวจสอบว่าภาพอัปโหลดสำเร็จและ URL ถูกต้อง")
            else:
                st.info("💡 ลองตรวจสอบ:\n- API Key ถูกต้อง\n- มีเครดิตเพียงพอ\n- ภาพอัปโหลดสำเร็จ")

    # Display latest video only
    if st.session_state.generated_videos:
        st.divider()
        total_videos = len(st.session_state.generated_videos)
        st.subheader("✅ วิดีโอล่าสุด")
        st.caption(f"วิดีโอทั้งหมด {total_videos} คลิปดูได้ในแท็บ 🎬 Video Gallery")

        # Show latest video
        latest_video = st.session_state.generated_videos[-1]

        # จำกัดขนาดวิดีโอให้เล็กลงและจัดกึ่งกลาง
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            st.video(str(latest_video['path']))
            st.caption(f"📁 {latest_video['filename']}")
            st.caption(f"⚙️ {latest_video['method']} | 🕐 {latest_video['timestamp']}")
            if 'elapsed_time' in latest_video:
                st.caption(f"⏱️ ใช้เวลา: {latest_video['elapsed_time']}")

        # Download button
        with open(latest_video['path'], 'rb') as video_file:
            video_bytes = video_file.read()
            st.download_button(
                label="📥 ดาวน์โหลดวิดีโอนี้",
                data=video_bytes,
                file_name=latest_video['filename'],
                mime="video/mp4",
                use_container_width=True
            )

        st.info(f"📂 วิดีโอทั้งหมดบันทึกที่: `results/videos/`")



def gallery_tab():
    """Display all generated images (recent + archived)"""

    st.header("🖼️ แกลเลอรี่ภาพทั้งหมด")

    # Combine all images (recent + archived)
    all_images = st.session_state.generated_images + st.session_state.gallery_images

    if not all_images:
        st.info("ยังไม่มีภาพในแกลเลอรี่")
        return

    # Display counts
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("ภาพพรีวิว", len(st.session_state.generated_images))
    with col2:
        st.metric("ภาพที่เก็บแล้ว", len(st.session_state.gallery_images))
    with col3:
        st.metric("รวมทั้งหมด", len(all_images))

    # Add tabs for filtering
    tab1, tab2, tab3 = st.tabs(["📸 ทั้งหมด", "🆕 ภาพล่าสุด", "🗂️ ภาพที่เก็บแล้ว"])

    with tab1:
        display_image_grid(all_images, "ทั้งหมด")

    with tab2:
        if st.session_state.generated_images:
            display_image_grid(st.session_state.generated_images, "ล่าสุด")
        else:
            st.info("ยังไม่มีภาพในพรีวิว")

    with tab3:
        if st.session_state.gallery_images:
            display_image_grid(st.session_state.gallery_images, "เก็บแล้ว")
        else:
            st.info("ยังไม่มีภาพที่เก็บแล้ว")


def display_image_grid(images, label):
    """Helper function to display images in a grid"""
    if not images:
        return

    st.caption(f"แสดง {len(images)} ภาพ")

    # Display in grid
    cols_per_row = 3

    for i in range(0, len(images), cols_per_row):
        cols = st.columns(cols_per_row)

        for j in range(cols_per_row):
            idx = i + j
            if idx < len(images):
                img_data = images[idx]

                with cols[j]:
                    try:
                        image = Image.open(img_data['path'])
                        # Create thumbnail copy for preview
                        img_preview = image.copy()
                        img_preview.thumbnail((400, 400))
                        st.image(img_preview, width=400, caption=f"สินค้า: {Path(img_data['path']).name}")
                        st.caption(f"{img_data['product_category']}")
                        st.caption(f"🕐 {img_data['timestamp']}")
                    except Exception as e:
                        st.error(f"Error: {e}")


def video_gallery_tab():
    """Display all generated videos"""

    st.header("🎬 แกลเลอรี่วิดีโอทั้งหมด")

    if not st.session_state.generated_videos:
        st.info("ยังไม่มีวิดีโอในแกลเลอรี่")
        return

    # Display count
    total_videos = len(st.session_state.generated_videos)
    st.metric("จำนวนวิดีโอทั้งหมด", total_videos)

    # Info about folder
    st.info(f"📂 **วิดีโอทั้งหมด {total_videos} คลิปบันทึกที่:** `results/videos/`")

    # Button to open folder
    if st.button("📁 เปิดโฟลเดอร์วิดีโอทั้งหมด"):
        import subprocess
        import os
        folder_path = os.path.abspath("results/videos")
        try:
            subprocess.Popen(f'explorer "{folder_path}"')
            st.success("เปิดโฟลเดอร์แล้ว!")
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()

    # Display videos in grid (2 columns)
    cols_per_row = 2

    # Show in reverse order (newest first)
    for i in range(0, total_videos, cols_per_row):
        cols = st.columns(cols_per_row)

        for j in range(cols_per_row):
            idx = total_videos - 1 - (i + j)  # Reverse index
            if idx >= 0:
                video_data = st.session_state.generated_videos[idx]

                with cols[j]:
                    try:
                        # Video preview
                        st.video(str(video_data['path']))

                        # Info
                        st.caption(f"📁 **{video_data['filename']}**")
                        st.caption(f"⚙️ {video_data['method']}")
                        st.caption(f"🕐 {video_data['timestamp']}")
                        if 'elapsed_time' in video_data:
                            st.caption(f"⏱️ ใช้เวลา: {video_data['elapsed_time']}")

                        # Download button
                        with open(video_data['path'], 'rb') as video_file:
                            video_bytes = video_file.read()
                            st.download_button(
                                label="📥 ดาวน์โหลด",
                                data=video_bytes,
                                file_name=video_data['filename'],
                                mime="video/mp4",
                                key=f"download_video_{idx}",
                                use_container_width=True
                            )

                        st.divider()

                    except Exception as e:
                        st.error(f"Error: {e}")


def export_logs_to_csv():
    """Export all prompts and data to CSV"""

    if not st.session_state.prompts_data:
        st.warning("ไม่มีข้อมูลสำหรับ export")
        return

    # Prepare data for CSV
    csv_data = []
    for img_data in st.session_state.prompts_data:
        csv_data.append({
            'filename': Path(img_data['path']).name,
            'product_category': img_data['product_category'],
            'gender': img_data['gender'],
            'age_range': img_data['age_range'],
            'prompt': img_data['prompt'],
            'timestamp': img_data['timestamp'],
            'video_created': 'Yes' if st.session_state.video_path else 'No'
        })

    # Create DataFrame
    df = pd.DataFrame(csv_data)

    # Save to CSV
    csv_path = config.PROMPTS_CSV
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    st.success(f"✅ Export สำเร็จ! บันทึกที่: {csv_path}")

    # Download button
    csv_string = df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 Download CSV",
        data=csv_string,
        file_name=f"prompts_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )


def batch_load_products_from_folder():
    """Load all product images from upload_images folder"""
    try:
        upload_dir = config.UPLOAD_IMAGES_DIR

        # Get all image files from upload_images folder
        image_files = []
        for ext in config.ALLOWED_EXTENSIONS:
            image_files.extend(list(upload_dir.glob(f"*{ext}")))

        if not image_files:
            st.warning("⚠️ ไม่พบรูปภาพในโฟลเดอร์ upload_images กรุณาเพิ่มรูปสินค้า")
            return

        # Store in session state
        st.session_state.batch_products = [str(img) for img in image_files]
        st.success(f"✅ โหลดสินค้าสำเร็จ {len(image_files)} รายการ!")
        st.rerun()

    except Exception as e:
        st.error(f"❌ Error loading products: {str(e)}")


def batch_generate_all_products(
    product_category,
    gender,
    age_range,
    photo_style,
    location,
    camera_angle,
    custom_details,
    num_images_per_product,
    ai_engine
):
    """Generate images for all products in batch"""

    if 'batch_products' not in st.session_state or not st.session_state.batch_products:
        st.error("❌ ไม่มีสินค้าที่โหลด กรุณากดปุ่ม 'โหลดสินค้าจากโฟลเดอร์' ก่อน")
        return

    # Validate API keys
    if ai_engine == "Kie.ai Nano Banana (แนะนำสุด! ไม่มี Content Filter)":
        if not config.KIE_API_KEY:
            st.error("❌ กรุณากรอก Kie.ai API Key")
            return
        if not config.IMGBB_API_KEY:
            st.error("❌ กรุณากรอก imgbb API Key")
            return
        if not config.GEMINI_API_KEY:
            st.error("❌ กรุณากรอก Gemini API Key")
            return

    total_products = len(st.session_state.batch_products)
    total_images = total_products * num_images_per_product

    st.info(f"🚀 กำลังสร้างภาพสำหรับ {total_products} สินค้า (รวม {total_images} ภาพ)")

    # Progress tracking
    overall_progress = st.progress(0)
    status_container = st.empty()

    # Initialize prompt generator
    prompt_gen = PromptGenerator()

    # Loop through each product
    for product_idx, product_path in enumerate(st.session_state.batch_products):
        try:
            product_name = Path(product_path).name
            status_container.text(f"📦 กำลังสร้างสินค้า {product_idx + 1}/{total_products}: {product_name}")

            # Set as current reference image
            st.session_state.uploaded_reference_images = [product_path]

            # Generate prompt for this product
            generated_prompt = prompt_gen.generate_image_prompt_v2(
                product_category=product_category,
                gender=gender,
                age_range=age_range,
                photo_style=photo_style,
                location=location,
                camera_angle=camera_angle,
                custom_details=custom_details
            )

            # Generate images for this product
            generate_images_from_prompt(
                prompt=generated_prompt,
                product_category=product_category,
                gender=gender,
                age_range=age_range,
                num_images=num_images_per_product,
                ai_engine=ai_engine,
                advanced_params=None,
                photo_style=photo_style,
                location=location,
                camera_angle=camera_angle
            )

            # Update overall progress
            progress = (product_idx + 1) / total_products
            overall_progress.progress(progress)

        except Exception as e:
            st.error(f"❌ Error generating images for {product_name}: {str(e)}")
            continue

    status_container.empty()
    overall_progress.empty()

    st.success(f"✅ สร้างภาพเสร็จสิ้น! สร้างไปทั้งหมด {len(st.session_state.generated_images)} ภาพ")
    st.balloons()

    # Show gallery
    show_latest_images_gallery(n=12)


if __name__ == "__main__":
    main()
