# -*- coding: utf-8 -*-
"""
Automation Loop Module
สร้างภาพและวิดีโอแบบวนลูปอัตโนมัติ: รูป 1 → คลิป 1 → รูป 2 → คลิป 2...
"""

import streamlit as st
import time
from datetime import datetime
from pathlib import Path
import config
import sys
import io
import random

# Fix encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, OSError, ValueError):
        # Python < 3.7 or Streamlit environment where reconfigure is not allowed
        # ValueError: closed file, OSError: invalid argument, AttributeError: no reconfigure
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        except (AttributeError, OSError, ValueError):
            # Streamlit environment - stdout/stderr are already handled, skip
            pass


# Helper function to suppress output (fixes Windows encoding errors)
import os
import contextlib

@contextlib.contextmanager
def suppress_stdout_stderr():
    """Temporarily suppress stdout/stderr to avoid encoding errors during imports"""
    with open(os.devnull, 'w', encoding='utf-8') as devnull:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
            sys.stdout = devnull
            sys.stderr = devnull
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr


class AutomationLoop:
    """จัดการ loop สร้างภาพและวิดีโออัตโนมัติ"""

    def __init__(self):
        self.is_running = False
        self.total_products_processed = 0
        self.total_products_skipped = 0

    def generate_simple_prompt(self, product_category: str, gender: str) -> str:
        """
        สร้าง prompt แบบง่ายๆ พร้อมสุ่มชุดและสถานที่เพื่อความหลากหลาย
        จับคู่ชุดให้เข้ากับประเภทสินค้า

        Args:
            product_category: ประเภทสินค้า
            gender: เพศของโมเดล

        Returns:
            prompt สั้นและกระชับ พร้อมสุ่มรายละเอียด
        """
        product_en = self._extract_english(product_category)
        gender_en = self._extract_english(gender)

        # Model type
        if gender_en.lower() == "male":
            model = "man"
        elif gender_en.lower() == "female":
            model = "woman"
        else:
            model = "person"

        # จับคู่ชุดตามประเภทสินค้า (outfit matching by product type)
        product_lower = product_en.lower()

        # ชุดสำหรับผู้หญิง - เน้นกางเกงยีน กระโปรงยีน กระโปรงลูกไม้ เสื้อรัดรูป
        if gender_en.lower() == "female":
            # Casual Trendy style - กางเกงยีน + เสื้อรัดรูป
            casual_outfits = [
                "a fitted crop top with high-waisted skinny jeans",
                "a tight-fitting tank top with slim-fit blue jeans",
                "a body-hugging tee with high-waisted mom jeans",
                "a fitted white t-shirt with black skinny jeans",
                "a snug crop tank with distressed denim jeans",
                "a form-fitting ribbed top with light-wash skinny jeans"
            ]

            # Skirt styles - กระโปรงยีน + กระโปรงลูกไม้
            elegant_outfits = [
                "a fitted crop top with a short denim skirt",
                "a tight-fitting tank top with a cute denim mini skirt",
                "a body-hugging tee with a short lace skirt",
                "a fitted blouse with a romantic mid-calf lace skirt",
                "a snug ribbed top with a pretty short lace skirt",
                "a form-fitting camisole with an elegant midi lace skirt"
            ]

            # จับคู่ชุดตามสินค้า
            if "shoe" in product_lower or "sneaker" in product_lower:
                # รองเท้าผ้าใบ → ชุดแคชชวล
                outfits = casual_outfits
            elif "bag" in product_lower or "watch" in product_lower or "sunglasses" in product_lower:
                # กระเป๋า, นาฬิกา, แว่นตา → ใช้ได้ทั้งหมด
                outfits = casual_outfits + elegant_outfits
            else:
                # สินค้าอื่นๆ → ใช้ทั้งหมด
                outfits = casual_outfits + elegant_outfits

        else:  # male or unisex
            # ผู้ชาย - เน้นกางเกงยีน + เสื้อรัดรูปพอดีตัว
            casual_outfits = [
                "a fitted t-shirt with slim-fit black jeans",
                "a tight-fitting polo with dark blue skinny jeans",
                "a body-hugging henley shirt with slim-fit denim jeans",
                "a snug graphic tee with distressed skinny jeans",
                "a fitted button-up shirt with tight black jeans",
                "a form-fitting turtleneck with slim-fit blue jeans",
                "a fitted crew neck tee with high-waisted slim jeans",
                "a tight-fitting long sleeve with dark skinny jeans"
            ]

            outfits = casual_outfits

        outfit = random.choice(outfits)

        # สุ่มสถานที่ในไทย - เน้นสวนสาธารณะและหน้าคาเฟ่ (ไม่มีคนอื่น)
        locations = [
            "in front of a quiet modern Bangkok cafe, empty background",
            "at a peaceful garden area in Lumpini Park, no other people",
            "outside a cozy Thonglor cafe, clean empty surroundings",
            "in a serene public park with green trees, isolated setting",
            "at a tranquil Thai cafe terrace, no crowds",
            "beside a calm park pathway, peaceful atmosphere",
            "in front of a minimalist Bangkok cafe, clean background",
            "at a quiet corner of Benjakitti Park, empty space",
            "outside a stylish Ari cafe, deserted area",
            "in a peaceful garden setting, solitary environment",
            "at a serene cafe courtyard, no other people visible",
            "beside park greenery, empty peaceful surroundings",
            "in front of a modern cafe entrance, isolated shot",
            "at a calm public park area, clean empty background",
            "outside a chic Bangkok cafe, peaceful solitary setting"
        ]

        location = random.choice(locations)

        # Template ที่เน้นให้ AI สร้างชุดใหม่ ไม่ก็อปปี้จากภาพตัวอย่าง
        # สำหรับรองเท้า: ใช้มุมเอวลงมาเท่านั้น เพื่อให้ Sora 2 ไม่ reject
        # สำหรับสินค้าอื่น: ใช้มุมไหล่ลงมา แต่เน้นว่าเป็น illustration style

        product_lower = product_en.lower()

        if "shoe" in product_lower or "sneaker" in product_lower:
            # รองเท้า - ใช้มุมเอวลงมาเท่านั้น (waist down - legs and feet only) + iPhone camera style
            prompt = f"iPhone candid photo: single {model} in {outfit} wearing {product_en}, waist down view only, show legs and feet, no upper body, no torso, crop from waist, {location}, natural daylight, iPhone camera aesthetic, authentic candid shot, shallow depth of field, focus on {product_en}, 9:16 vertical portrait, natural color grading, unposed lifestyle photography, solo person only no other people in background, keep product design exact"
        else:
            # สินค้าอื่นๆ - iPhone camera style + illustration เพื่อหลีกเลี่ยงการตรวจจับ photorealistic people
            prompt = f"iPhone candid photo illustration: single {model} in {outfit} wearing {product_en}, shoulder down view, no face visible, crop from shoulders, {location}, natural daylight, iPhone portrait mode aesthetic, soft background blur, focus on {product_en}, artistic semi-realistic style, 9:16 vertical portrait, natural color tone, casual lifestyle shot, faceless mannequin aesthetic, solo person only no other people in scene, keep product design exact"

        return prompt

    def generate_simple_video_prompt(self, product_category: str) -> str:
        """
        สร้าง video prompt แบบง่ายๆ พร้อมการเคลื่อนไหวที่ชัดเจน

        Args:
            product_category: ประเภทสินค้า

        Returns:
            video prompt ที่มีการเคลื่อนไหวชัดเจน
        """
        product_en = self._extract_english(product_category)

        # Video prompts - เน้นการเคลื่อนไหวของคน ไม่ใช่กล้อง (Sora 2 ทำ camera zoom ได้แต่ไม่ค่อยทำ motion ดี)
        if "shoe" in product_en.lower():
            motion_styles = [
                f"Person wearing {product_en} walks slowly forward taking natural steps, full body in frame from waist down, person moves toward camera, steady walking motion, legs and feet movement clearly visible, natural walking pace, person gets closer with each step",
                f"Model in {product_en} takes relaxed casual steps, walking motion from waist-down view, person strolls naturally, feet stepping forward repeatedly, continuous walking movement, person advances steadily",
                f"Person walks in {product_en} with natural stride, lower body shot showing legs moving, each foot stepping forward alternately, smooth walking rhythm, person progresses forward continuously, waist-down framing throughout",
                f"Casual walking in {product_en}, person takes calm steps moving toward viewer, waist-down perspective captures leg movement, natural foot placement with each step, person walks closer progressively, steady forward motion"
            ]
        else:
            # สำหรับสินค้าอื่นๆ - เน้นการเคลื่อนไหวของคน
            motion_styles = [
                f"Person wearing {product_en} turns body slowly from side to front, natural rotation movement, person twists torso smoothly, shoulder-down view, body rotates to show different angles, continuous turning motion, person completes quarter turn",
                f"Model showcasing {product_en} shifts weight from one side to other, person sways gently side to side, natural body movement, weight transfer visible, person rocks slowly back and forth, subtle continuous motion",
                f"Person with {product_en} moves arm to touch or adjust product, hand reaches toward product naturally, person interacts with item, arm movement clearly visible, person gestures toward product area, natural interaction motion",
                f"Model in {product_en} takes small step forward, person advances one step, body moves toward camera, stepping motion visible, person shifts position forward, natural forward movement, single deliberate step"
            ]

        # สุ่มเลือก 1 motion style
        import random
        prompt = random.choice(motion_styles)

        return prompt

    def _extract_english(self, text: str) -> str:
        """แยกข้อความภาษาอังกฤษจากข้อความแบบ Thai-English"""
        if "(" in text and ")" in text:
            return text.split("(")[1].split(")")[0].strip()
        return text.strip()

    def run_automation_loop(
        self,
        reference_images: list,
        product_category: str,
        gender: str,
        age_range: str,
        ai_engine: str,
        video_method: str = "Sora 2",
        stop_callback=None
    ):
        """
        วนลูปสร้างภาพและวิดีโอทีละชิ้น (รูป → คลิป → รูป → คลิป...)

        Args:
            reference_images: รายการรูปสินค้าอ้างอิง
            product_category: ประเภทสินค้า
            gender: เพศ
            age_range: ช่วงอายุ
            ai_engine: AI engine ที่ใช้สร้างภาพ
            video_method: วิธีสร้างวิดีโอ
            stop_callback: ฟังก์ชันเช็คว่าควรหยุดหรือไม่
        """
        # Import sys to avoid UnboundLocalError (since we assign to sys.stdout later)
        import sys as _sys

        # Import generators
        try:
            from kie_generator import KieGenerator
            from prompt_generator import PromptGenerator
        except Exception as e:
            st.error(f"Failed to import generators: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
            return

        self.is_running = True
        self.total_products_processed = 0
        self.total_products_skipped = 0
        self.consecutive_failures = 0  # Track consecutive failures

        # Initialize generators
        try:
            # Suppress stdout/stderr during initialization to prevent I/O errors
            old_stdout = _sys.stdout
            old_stderr = _sys.stderr

            try:
                # Redirect to devnull to prevent I/O errors from print statements
                devnull = open(os.devnull, 'w')
                _sys.stdout = devnull
                _sys.stderr = devnull

                # Always initialize kie_gen (needed for imgbb upload in video generation)
                kie_gen = KieGenerator()
                prompt_gen = PromptGenerator()
            finally:
                # Always restore stdout/stderr
                _sys.stdout = old_stdout
                _sys.stderr = old_stderr
                try:
                    devnull.close()
                except:
                    pass

        except Exception as e:
            st.error(f"Error initializing generators: {str(e)}")
            st.error("Failed to initialize generator. Please check your API key.")
            import traceback
            st.error(traceback.format_exc())
            return

        # สร้าง UI containers
        status_header = st.empty()
        progress_container = st.container()
        current_item_status = st.empty()

        total_items = len(reference_images)

        # Check Kie.ai credits if using Kie.ai engine (optional - silent fail if not available)
        if kie_gen and "Kie.ai" in ai_engine:
            credit_col1, credit_col2 = st.columns([3, 1])

            with credit_col1:
                try:
                    credit_info = kie_gen.get_credits()
                    if credit_info.get('success'):
                        credits = credit_info.get('credits', 0)
                        st.info(f"💳 **Kie.ai Credits**: {credits:,} {credit_info.get('currency', 'credits')}")

                        # Warning if credits < 200
                        if credits < 200:
                            st.warning(f"⚠️ **Low Credits Warning**: You only have {credits} credits remaining!")
                            st.warning(f"💡 Each image generation uses approximately 10-20 credits. You may need to top up soon.")
                        elif credits < 500:
                            st.info(f"ℹ️ You have {credits} credits. Consider topping up if you plan to generate many images.")
                    # Silent fail if credit check endpoint is not available
                except Exception:
                    pass  # Credit check not available - continue without warning

            with credit_col2:
                # Top-up button - opens in new tab
                st.markdown("&nbsp;")  # Spacing
                st.link_button(
                    "💰 เติมเครดิต",
                    "https://kie.ai/billing",
                    help="เปิดหน้าเติมเครดิต Kie.ai (New Tab)",
                    use_container_width=True
                )

        # ใช้ st.write แทน print เพื่อหลีกเลี่ยง encoding error
        status_header.info(f"🔄 **Automation Loop started** - Processing {total_items} products (infinite loop)")

        # วนลูปไปเรื่อยๆ จนกว่าจะกด STOP
        round_number = 1
        while self.is_running:
            status_header.info(f"🔄 **Round {round_number}** - Processing {total_items} products")

            # เช็คเครดิตก่อนเริ่ม round ใหม่ (สำหรับ Kie.ai)
            if "Kie.ai" in ai_engine:
                try:
                    credit_info = kie_gen.get_credits()
                    if credit_info.get('success'):
                        credits = credit_info.get('credits', 0)
                        st.info(f"💳 Credits remaining: {credits:,}")

                        # หยุด loop ถ้าเครดิตน้อยกว่า 50
                        if credits < 50:
                            st.error(f"🚫 **LOOP STOPPED: Insufficient credits ({credits} remaining)**")
                            st.error("Please top up your Kie.ai credits to continue")
                            st.link_button("💰 Top up credits", "https://kie.ai/billing")
                            self.is_running = False
                            break
                        elif credits < 200:
                            st.warning(f"⚠️ Low credits warning: {credits} remaining")
                except Exception:
                    pass  # Continue if credit check fails

            # วนลูปแต่ละสินค้า
            for idx, ref_image_path in enumerate(reference_images):

                # เช็คว่าควรหยุดหรือไม่
                if stop_callback and stop_callback():
                    status_header.warning("⏸️ **Loop หยุดโดยผู้ใช้**")
                    self.is_running = False
                    break

                if not self.is_running:
                    break

                product_num = idx + 1

                with progress_container:
                    st.divider()
                    st.subheader(f"📦 สินค้าที่ {product_num}/{total_items}")

                    # ============ STEP 1: Generate Image ============
                    current_item_status.info(f"🎨 **[{product_num}/{total_items}] Generating image...**")

                    try:
                        # สร้าง prompt แบบง่าย
                        simple_prompt = self.generate_simple_prompt(product_category, gender)

                        st.info(f"📝 Prompt: {simple_prompt[:100]}...")

                        # เรียกฟังก์ชันสร้างภาพจาก __main__ module
                        import sys
                        if '__main__' in sys.modules:
                            generate_images_from_prompt = sys.modules['__main__'].generate_images_from_prompt
                        else:
                            st.error("❌ ไม่พบ __main__ module - กรุณารีสตาร์ทแอป")
                            continue

                        # Set uploaded_reference_images ชั่วคราว
                        temp_uploaded = [ref_image_path]
                        original_uploaded = st.session_state.uploaded_reference_images.copy() if st.session_state.uploaded_reference_images else []
                        st.session_state.uploaded_reference_images = temp_uploaded

                        # สร้างรูป 1 รูป
                        start_time = time.time()
                        generate_images_from_prompt(
                            prompt=simple_prompt,
                            product_category=product_category,
                            gender=gender,
                            age_range=age_range,
                            num_images=1,
                            ai_engine=ai_engine,
                            photo_style="iPhone Candid",
                            location="Minimal Background",
                            camera_angle="Waist Down",
                            skip_display=True
                        )

                        # Restore
                        st.session_state.uploaded_reference_images = original_uploaded

                        elapsed_img = int(time.time() - start_time)
                        current_item_status.success(f"✅ **[{product_num}/{total_items}] Image created!** ({elapsed_img} sec)")

                        # Get latest image
                        if st.session_state.generated_images:
                            latest_image = st.session_state.generated_images[-1]
                            st.image(latest_image['path'], caption=f"Product {product_num} image", width=300)
                            # Reset consecutive failures on success
                            self.consecutive_failures = 0

                    except Exception as e:
                        current_item_status.error(f"❌ **Image generation failed**: {str(e)[:150]}")
                        st.session_state.uploaded_reference_images = original_uploaded

                        # Track consecutive failures
                        self.consecutive_failures += 1

                        # Stop loop if too many consecutive failures
                        if self.consecutive_failures >= 5:
                            st.error(f"🚫 **LOOP STOPPED: {self.consecutive_failures} consecutive image generation failures**")
                            st.error("Possible causes:")
                            st.error("- Insufficient API credits")
                            st.error("- API key expired or invalid")
                            st.error("- Network connection issues")
                            st.error("- API service temporarily unavailable")
                            self.is_running = False
                            break

                        continue

                    # Check if should stop
                    if stop_callback and stop_callback():
                        status_header.warning("⏸️ **Loop stopped by user**")
                        self.is_running = False
                        break

                    # ============ STEP 2: Generate Video ============
                    current_item_status.info(f"🎬 **[{product_num}/{total_items}] Generating video...**")

                    # Create placeholder for real-time progress updates
                    video_progress_placeholder = st.empty()

                    try:
                        if not st.session_state.generated_images:
                            st.warning("⚠️ No image to create video - skip")
                            continue

                        # Get latest image
                        latest_image = st.session_state.generated_images[-1]

                        # Generate simple video prompt
                        video_prompt = self.generate_simple_video_prompt(product_category)

                        st.info(f"🎬 Video Prompt: {video_prompt[:100]}...")

                        # Check API keys (required for AI video generation)
                        if not config.KIE_API_KEY or not config.IMGBB_API_KEY:
                            st.error("❌ KIE_API_KEY and IMGBB_API_KEY required for AI video generation")
                            continue

                        # Define progress callback for real-time updates
                        def update_video_progress(elapsed_seconds, remaining_str="", status_method=""):
                            """Update video generation progress in real-time"""
                            minutes = int(elapsed_seconds // 60)
                            seconds = int(elapsed_seconds % 60)

                            if minutes > 0:
                                time_display = f"{minutes} นาที {seconds} วินาที"
                            else:
                                time_display = f"{seconds} วินาที"

                            # Update placeholder with current progress
                            video_progress_placeholder.info(
                                f"⏰ **สร้างวิดีโอ...** {time_display} {remaining_str}"
                            )

                        # Initialize video creator - AI only (Veo3 or Sora 2)
                        if "Veo3" in video_method:
                            from veo_video_creator import Veo3VideoCreator
                            video_creator = Veo3VideoCreator()

                            start_time_vid = time.time()

                            # Upload to imgbb
                            image_url = kie_gen.upload_image_to_imgbb(latest_image['path'], config.IMGBB_API_KEY)

                            # Create video with progress callback
                            result = video_creator.create_video_from_images(
                                image_urls=[image_url],
                                prompt=video_prompt,
                                filename=f"auto_r{round_number}_veo_p{product_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                                aspect_ratio="9:16",
                                watermark=None,
                                progress_callback=update_video_progress
                            )

                        else:  # Sora 2
                            from sora2_video_creator import Sora2VideoCreator
                            video_creator = Sora2VideoCreator()

                            start_time_vid = time.time()

                            # Upload to imgbb
                            image_url = kie_gen.upload_image_to_imgbb(latest_image['path'], config.IMGBB_API_KEY)

                            # Create video with progress callback
                            result = video_creator.create_video_from_image(
                                image_url=image_url,
                                prompt=video_prompt,
                                filename=f"auto_r{round_number}_sora_p{product_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                                aspect_ratio="portrait",
                                remove_watermark=True,
                                progress_callback=update_video_progress
                            )

                        elapsed_vid = int(time.time() - start_time_vid)
                        current_item_status.success(f"✅ **[{product_num}/{total_items}] Video created!** ({elapsed_vid} sec)")

                        # Save video data
                        video_data = {
                            'path': result['path'],
                            'method': f'{video_method} (Auto Loop)',
                            'task_id': result.get('task_id', ''),
                            'prompt': video_prompt,
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'filename': Path(result['path']).name,
                            'image_used': latest_image['path']
                        }
                        st.session_state.generated_videos.append(video_data)

                        # Show preview (reduced size - 400px width)
                        if Path(result['path']).exists():
                            preview_col1, preview_col2 = st.columns([1, 2])
                            with preview_col1:
                                st.video(result['path'])
                                st.caption(f"⏱️ Time: {elapsed_vid} sec")

                        self.total_products_processed += 1

                    except TimeoutError as e:
                        error_msg = str(e)
                        current_item_status.warning(f"⏱️ **Video generation timeout**: {error_msg[:150]}")
                        st.warning(f"⏭️ **Skipping Product {product_num}** - Video generation took too long")
                        st.info("💡 Continuing with next product...")
                        self.total_products_skipped += 1
                        continue

                    except Exception as e:
                        error_msg = str(e)
                        # Show full error for debugging
                        st.error(f"❌ **Video generation failed for Product {product_num}**")
                        st.error(f"**Error type**: {type(e).__name__}")
                        st.error(f"**Error message**: {error_msg}")
                        current_item_status.error(f"❌ **Video generation failed**: {error_msg[:150]}")

                        # Auto-fallback to Veo3 if Sora 2 fails due to photorealistic people
                        if 'photorealistic people' in error_msg.lower() and "Sora" in video_method:
                            st.warning("🚫 Image contains real people - Sora 2 not supported")
                            st.info("🔄 **Auto-fallback: Trying Veo3 instead...**")

                            try:
                                from veo_video_creator import Veo3VideoCreator
                                video_creator_veo = Veo3VideoCreator()

                                start_time_veo = time.time()

                                # Create video with Veo3 (already have image_url from Sora attempt)
                                result = video_creator_veo.create_video_from_images(
                                    image_urls=[image_url],
                                    prompt=video_prompt,
                                    filename=f"auto_r{round_number}_veo_p{product_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                                    aspect_ratio="9:16",
                                    watermark=None,
                                    progress_callback=update_video_progress
                                )

                                elapsed_vid = int(time.time() - start_time_veo)
                                current_item_status.success(f"✅ **[{product_num}/{total_items}] Video created with Veo3!** ({elapsed_vid} sec)")

                                # Save video data
                                video_data = {
                                    'path': result['path'],
                                    'method': 'Veo3 (Auto-fallback)',
                                    'task_id': result.get('task_id', ''),
                                    'prompt': video_prompt,
                                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    'filename': Path(result['path']).name,
                                    'image_used': latest_image['path']
                                }
                                st.session_state.generated_videos.append(video_data)

                                # Show preview
                                if Path(result['path']).exists():
                                    preview_col1, preview_col2 = st.columns([1, 2])
                                    with preview_col1:
                                        st.video(result['path'])
                                        st.caption(f"⏱️ Time: {elapsed_vid} sec (Veo3)")

                                self.total_products_processed += 1

                                # Don't skip - continue to next product successfully
                                progress = (product_num / total_items) * 100
                                status_header.success(f"📊 **Round {round_number} - Progress: {product_num}/{total_items} products ({progress:.1f}%)**")
                                continue

                            except Exception as veo_error:
                                st.error(f"❌ **Veo3 fallback also failed**: {str(veo_error)[:150]}")
                                st.warning(f"⏭️ **Skipping Product {product_num}** - Both Sora 2 and Veo3 failed")
                                self.total_products_skipped += 1
                                continue

                        elif 'timeout' in error_msg.lower():
                            st.warning(f"⏱️ Video generation timeout after waiting")

                        st.warning(f"⏭️ **Skipping Product {product_num}** - Will continue with next product")
                        self.total_products_skipped += 1
                        continue

                    # Show progress
                    progress = (product_num / total_items) * 100
                    status_header.success(f"📊 **Round {round_number} - Progress: {product_num}/{total_items} products ({progress:.1f}%)**")

            # เสร็จ 1 รอบแล้ว - เช็คว่าควรหยุดหรือไม่
            if not self.is_running:
                break

            # เพิ่มรอบและเริ่มใหม่
            round_number += 1
            status_header.success(f"✅ **Round {round_number - 1} Complete!** Starting Round {round_number}...")
            time.sleep(1)  # รอ 1 วินาทีก่อนเริ่มรอบใหม่

        # Summary
        self.is_running = False

        if self.total_products_processed > 0:
            st.balloons()
            total_attempted = self.total_products_processed + self.total_products_skipped
            success_rate = (self.total_products_processed / total_attempted * 100) if total_attempted > 0 else 0

            st.success(f"""
            🎉 **Automation Loop Complete!**

            📊 Summary:
            - Products processed: {self.total_products_processed}/{total_items}
            - Products skipped: {self.total_products_skipped}
            - Success rate: {success_rate:.1f}%
            - Method: {video_method}
            """)
        else:
            st.warning("⚠️ No products processed successfully")


# Helper function สำหรับใช้ใน main.py
def create_automation_tab():
    """สร้าง UI tab สำหรับ Automation Loop"""

    st.header("🔄 Automation Loop")
    st.markdown("### วนลูปสร้างรูปและคลิปอัตโนมัติ: รูป → คลิป → รูป → คลิป...")

    # ============ CREDIT DISPLAY (PROMINENT) ============
    # แสดงเครดิต Kie.ai แบบเรียลไทม์ที่หัวโปรแกรม
    try:
        from kie_generator import KieGenerator
        kie_gen = KieGenerator()

        credit_info = kie_gen.get_credits()

        if credit_info.get('success'):
            credits = credit_info.get('credits', 0)
            currency = credit_info.get('currency', 'credits')

            # แสดงเครดิตแบบเด่นชัด พร้อมสี
            credit_col1, credit_col2 = st.columns([3, 1])

            with credit_col1:
                # เลือกสีตามจำนวนเครดิต
                if credits == 0:
                    st.error(f"### 💳 เครดิต: **{credits:,}** {currency}")
                    st.error("⚠️ **เครดิตหมด!** กรุณาเติมเครดิตก่อนใช้งาน")
                elif credits < 50:
                    st.error(f"### 💳 เครดิต: **{credits:,}** {currency}")
                    st.error("🚨 **เครดิตเหลือน้อยมาก!** ระบบจะหยุดอัตโนมัติเมื่อเครดิต < 50")
                elif credits < 200:
                    st.warning(f"### 💳 เครดิต: **{credits:,}** {currency}")
                    st.warning("⚠️ **เครดิตเหลือน้อย** - แนะนำให้เติมเครดิต")
                else:
                    st.success(f"### 💳 เครดิต: **{credits:,}** {currency}")
                    st.info("✅ เครดิตเพียงพอสำหรับการใช้งาน")

            with credit_col2:
                st.markdown("<br>", unsafe_allow_html=True)  # Spacing
                st.link_button(
                    "💰 เติมเครดิต",
                    "https://kie.ai/billing",
                    help="เปิดหน้าเติมเครดิต Kie.ai",
                    use_container_width=True
                )
        else:
            # ไม่สามารถเช็คเครดิตได้
            st.info("💳 **เครดิต**: ไม่สามารถตรวจสอบได้")

    except Exception as e:
        # Silent fail - แสดงข้อความสั้นๆ
        st.warning(f"💳 **เครดิต**: ไม่สามารถตรวจสอบได้ ({str(e)[:50]})")

    st.divider()
    # ============ END CREDIT DISPLAY ============

    # Initialize session state - ใช้ setdefault แทน if check
    st.session_state.setdefault('loop_is_running', False)
    st.session_state.setdefault('loop_should_start', False)

    # Settings
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("⚙️ ตั้งค่า")

        loop_product_category = st.selectbox(
            "ประเภทสินค้า",
            config.PRODUCT_CATEGORIES,
            key="loop_product_category"
        )

        loop_gender = st.selectbox(
            "เพศ",
            config.GENDER_OPTIONS,
            key="loop_gender"
        )

        loop_age_range = st.selectbox(
            "ช่วงอายุ",
            config.AGE_RANGES,
            key="loop_age_range"
        )

    with col2:
        st.subheader("🎨 AI Engine")

        loop_ai_engine = st.selectbox(
            "AI สร้างภาพ",
            config.AI_ENGINES,
            key="loop_ai_engine"
        )

        loop_video_method = st.selectbox(
            "วิธีสร้างวิดีโอ (AI เท่านั้น)",
            ["Veo3 (แนะนำ)", "Sora 2"],
            key="loop_video_method"
        )

    st.divider()

    # โหลดสินค้า
    st.subheader("📦 โหลดสินค้า")

    # ปุ่มโหลดสินค้าจากโฟลเดอร์
    if st.button("📂 โหลดสินค้าจากโฟลเดอร์", key="loop_load_batch"):
        # ใช้ sys.modules เพื่อหลีกเลี่ยง circular import
        import sys
        if '__main__' in sys.modules:
            batch_load_products_from_folder = sys.modules['__main__'].batch_load_products_from_folder
            batch_load_products_from_folder()
        else:
            st.error("❌ ไม่พบ __main__ module - กรุณารีสตาร์ทแอป")

    # แสดงจำนวนสินค้า
    uploaded_images = st.session_state.get('uploaded_reference_images', [])
    batch_images = st.session_state.get('batch_products', [])

    # Priority: batch_images > uploaded_images (เพราะมักมีสินค้าเยอะกว่า)
    reference_images = batch_images if batch_images else uploaded_images

    # Debug: แสดงข้อมูล
    st.write(f"Debug: uploaded_images = {len(uploaded_images)}, batch_images = {len(batch_images)}")

    if reference_images:
        source = "batch_products" if batch_images else "uploaded_reference_images"
        st.success(f"✅ มีสินค้า {len(reference_images)} ชิ้นพร้อมประมวลผล (จาก {source})")
    else:
        st.warning("⚠️ ยังไม่มีสินค้า - กรุณาโหลดสินค้าก่อน")

    st.divider()

    # Start/Stop Buttons
    st.subheader("🎮 ควบคุม")

    col_btn1, col_btn2, col_btn3 = st.columns(3)

    with col_btn1:
        start_disabled = st.session_state.loop_is_running or len(reference_images) == 0
        st.write(f"Debug START: disabled={start_disabled}, running={st.session_state.loop_is_running}, imgs={len(reference_images)}")

        if st.button("▶️ START LOOP", type="primary", disabled=start_disabled, key="start_loop_btn"):
            st.write("🔴 START button clicked!")
            st.session_state.loop_should_start = True
            st.session_state.loop_is_running = True
            st.write(f"🔴 Set loop_should_start = {st.session_state.loop_should_start}")
            st.write(f"🔴 Set loop_is_running = {st.session_state.loop_is_running}")

    with col_btn2:
        if st.button("⏸️ STOP LOOP", type="secondary", disabled=not st.session_state.loop_is_running, key="stop_loop_btn"):
            st.session_state.loop_is_running = False
            st.warning("🛑 Loop จะหยุดหลังจากสินค้าปัจจุบันเสร็จ...")

    with col_btn3:
        if st.button("🔄 RESET", key="reset_loop_btn"):
            st.session_state.loop_is_running = False
            st.success("✅ รีเซ็ตสถานะเรียบร้อย")

    # แสดงสถานะ
    if st.session_state.loop_is_running:
        st.info("🔄 **Loop กำลังทำงาน...** กด STOP เพื่อหยุด")
    else:
        st.info("⏸️ **Loop หยุดอยู่** กด START เพื่อเริ่ม")

    st.divider()

    # Debug: แสดงสถานะ
    st.write(f"Debug LOOP EXEC: loop_is_running = {st.session_state.loop_is_running}, loop_should_start = {st.session_state.get('loop_should_start', False)}, reference_images count = {len(reference_images)}")

    # ใช้ loop_should_start แทน loop_is_running เพื่อเริ่ม loop
    condition_met = st.session_state.get('loop_should_start', False) and len(reference_images) > 0
    st.write(f"Debug CONDITION: condition_met = {condition_met}")

    # เริ่มต้น loop ถ้ากด start
    if condition_met:
        # Reset flag
        st.session_state.loop_should_start = False
        st.warning(f"🚀 กำลังเริ่มต้น loop สำหรับ {len(reference_images)} สินค้า...")
        st.write(f"🟢 ENTERING LOOP EXECUTION...")

        def check_should_stop():
            """เช็คว่าควรหยุด loop หรือไม่"""
            return not st.session_state.loop_is_running

        # สร้าง AutomationLoop และเริ่มทำงาน
        automation = AutomationLoop()

        automation.run_automation_loop(
            reference_images=reference_images,
            product_category=loop_product_category,
            gender=loop_gender,
            age_range=loop_age_range,
            ai_engine=loop_ai_engine,
            video_method=loop_video_method,
            stop_callback=check_should_stop
        )

        # Loop เสร็จแล้ว - รีเซ็ตสถานะ
        st.session_state.loop_is_running = False
        st.session_state.loop_should_start = False
        st.success("✅ Loop เสร็จสมบูรณ์แล้ว!")
