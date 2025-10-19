"""
Image Generator for AI Product Visualizer
Handles image generation using:
- Google Gemini + Imagen (Primary)
- OpenAI's DALL-E API (Fallback)
- Replicate SDXL (For reference-based generation)
"""

import os
import requests
import base64
import io
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict
from openai import OpenAI
from PIL import Image
import google.generativeai as genai
import config


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to remove invalid characters for Windows/Linux filesystems

    Args:
        filename: Original filename

    Returns:
        Safe filename without invalid characters
    """
    # Remove invalid characters: < > : " / \ | ? *
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)

    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(' .')

    # Limit length to 200 characters (leave room for timestamp and extension)
    if len(sanitized) > 200:
        sanitized = sanitized[:200]

    # Replace multiple underscores with single one
    sanitized = re.sub(r'_+', '_', sanitized)

    return sanitized


class DALLEGenerator:
    """Generate images using Gemini/Imagen (primary) or DALL-E (fallback)"""

    def __init__(self, api_key: Optional[str] = None, use_gemini: bool = True):
        """
        Initialize Image Generator

        Args:
            api_key: OpenAI API key (for DALL-E fallback)
            use_gemini: Whether to use Gemini/Imagen as primary (default: True)
        """
        # Gemini configuration
        self.use_gemini = use_gemini and bool(config.GEMINI_API_KEY)

        if self.use_gemini:
            try:
                genai.configure(api_key=config.GEMINI_API_KEY)
                self.gemini_model = genai.GenerativeModel(config.GEMINI_PRO_MODEL)
                print("✅ Gemini initialized successfully")
            except Exception as e:
                print(f"⚠️  Gemini initialization failed: {e}, falling back to DALL-E")
                self.use_gemini = False

        # DALL-E configuration (fallback or alternative)
        self.api_key = api_key or config.OPENAI_API_KEY
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            self.model = config.DALLE_MODEL
            self.size = config.DALLE_SIZE
            self.quality = config.DALLE_QUALITY
            self.style = config.DALLE_STYLE
        else:
            if not self.use_gemini:
                print("⚠️  Warning: No API keys found. Please set GEMINI_API_KEY or OPENAI_API_KEY")

    def generate_image(
        self,
        prompt: str,
        save_path: Optional[Path] = None,
        filename_prefix: str = "generated"
    ) -> Dict[str, str]:
        """
        Generate an image using Gemini/Imagen (primary) or DALL-E (fallback)

        Args:
            prompt: The prompt for image generation
            save_path: Directory to save the image (default: config.IMAGES_DIR)
            filename_prefix: Prefix for the saved filename

        Returns:
            Dictionary containing:
                - 'url': URL of the generated image (if available)
                - 'path': Local path where image was saved
                - 'revised_prompt': Revised prompt used
        """
        if self.use_gemini:
            try:
                return self._generate_with_imagen(prompt, save_path, filename_prefix)
            except Exception as e:
                print(f"⚠️  Imagen generation failed: {e}")
                if self.api_key:
                    print("Falling back to DALL-E...")
                    return self._generate_with_dalle(prompt, save_path, filename_prefix)
                else:
                    raise Exception(f"Image generation failed and no fallback available: {str(e)}")
        else:
            return self._generate_with_dalle(prompt, save_path, filename_prefix)

    def _generate_with_imagen(
        self,
        prompt: str,
        save_path: Optional[Path] = None,
        filename_prefix: str = "imagen"
    ) -> Dict[str, str]:
        """
        Generate image using Google's Imagen API via Vertex AI

        Note: Requires google-cloud-aiplatform package
        """
        try:
            from vertexai.preview.vision_models import ImageGenerationModel

            if save_path is None:
                save_path = config.IMAGES_DIR

            print(f"🎨 Generating image with Imagen...")
            print(f"Prompt: {prompt[:100]}...")

            # Initialize Imagen model
            model = ImageGenerationModel.from_pretrained(config.IMAGEN_MODEL)

            # Generate image
            images = model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="9:16",  # Vertical format for social media
                safety_filter_level="block_some",
                person_generation="allow_adult",
            )

            # Save the generated image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.png"
            file_path = save_path / filename

            # Save image bytes to file
            images[0].save(location=str(file_path))

            print(f"✅ Image saved: {file_path}")

            return {
                'url': '',  # Imagen doesn't provide URL
                'path': str(file_path),
                'revised_prompt': prompt
            }

        except ImportError:
            raise Exception(
                "Vertex AI package not installed. Install with: "
                "pip install google-cloud-aiplatform"
            )
        except Exception as e:
            raise Exception(f"Imagen generation failed: {str(e)}")

    def _generate_with_dalle(
        self,
        prompt: str,
        save_path: Optional[Path] = None,
        filename_prefix: str = "dalle"
    ) -> Dict[str, str]:
        """Generate image using DALL-E"""
        try:
            if not self.api_key:
                raise ValueError("OpenAI API key is required for DALL-E")

            if save_path is None:
                save_path = config.IMAGES_DIR

            print(f"🎨 Generating image with DALL-E...")

            # Generate image
            response = self.client.images.generate(
                model=self.model,
                prompt=prompt,
                size=self.size,
                quality=self.quality,
                style=self.style,
                n=1,
            )

            # Get the generated image URL and revised prompt
            image_url = response.data[0].url
            revised_prompt = response.data[0].revised_prompt

            # Download and save the image
            image_path = self._download_image(
                image_url,
                save_path,
                filename_prefix
            )

            print(f"✅ Image saved: {image_path}")

            return {
                'url': image_url,
                'path': str(image_path),
                'revised_prompt': revised_prompt or prompt
            }

        except Exception as e:
            raise Exception(f"DALL-E generation failed: {str(e)}")

    def _download_image(
        self,
        url: str,
        save_path: Path,
        filename_prefix: str
    ) -> Path:
        """
        Download image from URL and save locally

        Args:
            url: URL of the image to download
            save_path: Directory to save the image
            filename_prefix: Prefix for the filename

        Returns:
            Path to the saved image
        """
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.png"
        file_path = save_path / filename

        # Download the image
        response = requests.get(url)
        response.raise_for_status()

        # Save to file
        with open(file_path, 'wb') as f:
            f.write(response.content)

        return file_path

    def regenerate_image(
        self,
        prompt: str,
        save_path: Optional[Path] = None,
        filename_prefix: str = "regenerated"
    ) -> Dict[str, str]:
        """
        Regenerate an image with the same prompt (convenience method)

        Args:
            prompt: The prompt for image generation
            save_path: Directory to save the image
            filename_prefix: Prefix for the saved filename

        Returns:
            Dictionary with image information
        """
        return self.generate_image(prompt, save_path, filename_prefix)

    def _generate_product_clean(
        self,
        reference_image_path: str,
        save_path: Path,
        replicate
    ) -> str:
        """
        Stage 1: Generate clean product image using Image-to-Image

        Args:
            reference_image_path: Path to reference product image
            save_path: Directory to save temporary product
            replicate: Replicate module

        Returns:
            Path to cleaned product image
        """
        print("[Stage 2] Generating clean product (Img2Img)...")

        model = "stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc"

        with open(reference_image_path, "rb") as image_file:
            output = replicate.run(
                model,
                input={
                    "image": image_file,
                    "prompt": "high quality studio product photography, clean background, professional lighting, sharp focus, exact same design",
                    "prompt_strength": 0.30,  # Lower = preserve original design better
                    "guidance_scale": 7.0,
                    "num_inference_steps": 44,
                    "refine": "expert_ensemble_refiner",
                    "scheduler": "K_EULER_ANCESTRAL",  # Euler a
                    "negative_prompt": "different product, changed design, modified colors, low quality, blurry, artifacts, extra laces, deformation, duplicate shoes, wrong brand"
                }
            )

        # Get URL and download
        product_url = output[0] if isinstance(output, list) else output
        product_path = save_path / "temp_product_clean.png"

        response = requests.get(product_url)
        response.raise_for_status()
        with open(product_path, 'wb') as f:
            f.write(response.content)

        print(f"Clean product saved: {product_path}")
        return str(product_path)

    def _generate_scene_background(
        self,
        prompt: str,
        save_path: Path,
        replicate
    ) -> str:
        """
        Stage 2: Generate scene with person using Text-to-Image

        Args:
            prompt: Scene description prompt
            save_path: Directory to save scene
            replicate: Replicate module

        Returns:
            Path to scene background image
        """
        print("[Stage 1] Generating scene background (Txt2Img FIRST)...")

        # Build clean, bright scene prompt (NO SHOES - will be added in Stage 3)
        scene_prompt = (
            f"{prompt}. "
            "Full body photograph of a young Thai woman (20-30 years old) standing barefoot in a modern outdoor Thai cafe garden. "
            "Clean bright setting, lush green plants, wooden furniture, natural sunlight, cafe atmosphere. "
            "The woman is visible from head to toe wearing casual clothing, legs and feet clearly visible. "
            "Natural daylight, realistic photography, professional composition, vertical 9:16 format, clean edges."
        )

        model = "stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc"

        output = replicate.run(
            model,
            input={
                "prompt": scene_prompt,
                "guidance_scale": 7.0,
                "num_inference_steps": 44,
                "refine": "expert_ensemble_refiner",
                "scheduler": "K_EULER_ANCESTRAL",  # Euler a
                "width": 768,
                "height": 1344,  # 9:16 ratio
                "negative_prompt": (
                    "deformed face, ugly face, bad anatomy, mutated hands, extra limbs, disfigured, "
                    "3d render, cartoon, painting, blurry, low quality, artifacts, jpeg artifacts, lowres, "
                    "shoes, footwear"  # Don't generate shoes in scene
                )
            }
        )

        # Get URL and download
        scene_url = output[0] if isinstance(output, list) else output
        scene_path = save_path / "temp_scene_bg.png"

        response = requests.get(scene_url)
        response.raise_for_status()
        with open(scene_path, 'wb') as f:
            f.write(response.content)

        print(f"Scene background saved: {scene_path}")
        return str(scene_path)

    def _cleanup_temp_files(self, save_path: Path):
        """Clean up all temporary files"""
        print("Cleaning up temporary files...")

        temp_patterns = ["temp_*.png", "temp_*.jpg"]
        cleaned = 0

        for pattern in temp_patterns:
            for temp_file in save_path.glob(pattern):
                try:
                    temp_file.unlink()
                    cleaned += 1
                except Exception as e:
                    print(f"Warning: Could not delete {temp_file}: {e}")

        if cleaned > 0:
            print(f"Cleaned up {cleaned} temporary file(s)")

    def _analyze_product_with_vision(self, product_path: str) -> str:
        """
        Use GPT-4 Vision to analyze product image and generate detailed description

        Args:
            product_path: Path to product image

        Returns:
            Detailed product description
        """
        print("Analyzing product with GPT-4 Vision...")

        try:
            # Read image and encode to base64
            with open(product_path, "rb") as image_file:
                import base64
                image_data = base64.b64encode(image_file.read()).decode('utf-8')

            # Call GPT-4 Vision
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Analyze this product image in detail. "
                                    "Describe: 1) Product type, 2) Main colors, 3) Design patterns, "
                                    "4) Brand/logo if visible, 5) Material texture, 6) Unique features. "
                                    "Keep description concise (max 3 sentences) but highly specific."
                                )
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=150
            )

            description = response.choices[0].message.content.strip()
            print(f"Product description: {description[:100]}...")
            return description

        except Exception as e:
            print(f"Warning: Vision analysis failed: {e}")
            return "stylish athletic shoes with modern design"

    def _create_foot_mask(self, scene_path: str, save_path: Path) -> str:
        """
        Create mask for foot area (bottom 25% of image)

        Args:
            scene_path: Path to scene image
            save_path: Directory to save mask

        Returns:
            Path to mask image
        """
        print("Creating foot area mask...")

        scene = Image.open(scene_path).convert("RGB")
        width, height = scene.size

        # Create black image (mask)
        mask = Image.new("RGB", (width, height), (0, 0, 0))

        # Draw white rectangle at bottom 25% (where feet typically are)
        from PIL import ImageDraw
        draw = ImageDraw.Draw(mask)

        # Foot area: bottom 25% of image, centered
        foot_height = int(height * 0.25)
        foot_width = int(width * 0.6)  # 60% width centered
        x1 = (width - foot_width) // 2
        y1 = height - foot_height
        x2 = x1 + foot_width
        y2 = height

        # Draw white rectangle (inpaint area)
        draw.rectangle([x1, y1, x2, y2], fill=(255, 255, 255))

        # Save mask
        mask_path = save_path / "temp_foot_mask.png"
        mask.save(mask_path)

        print(f"Mask created: {mask_path}")
        return str(mask_path)

    def _inpaint_product_onto_scene(
        self,
        scene_path: str,
        product_path: str,
        prompt: str,
        save_path: Path,
        filename_prefix: str,
        replicate
    ) -> str:
        """
        Stage 3: Inpaint product onto scene using advanced methods

        Args:
            scene_path: Path to scene background
            product_path: Path to clean product
            prompt: Original prompt
            save_path: Final output directory
            filename_prefix: Prefix for final filename
            replicate: Replicate module

        Returns:
            Path to final inpainted image
        """
        print("[Stage 3] Using Smart Composite (Direct Overlay)...")

        # Skip inpainting entirely - it creates duplicate shoes without product reference
        # Use direct composite instead
        return self._composite_images(
            scene_path,
            product_path,
            save_path,
            filename_prefix,
            replicate
        )

        # OLD CODE BELOW - Commented out because inpainting creates duplicate shoes
        # without product reference
        """
        # Create foot mask
        mask_path = self._create_foot_mask(scene_path, save_path)

        # Get product description from Vision
        product_description = self._analyze_product_with_vision(product_path)

        # Enhanced inpaint prompt
        inpaint_prompt = (
            f"{prompt}. "
            f"The woman is wearing {product_description} on her feet. "
            "The shoes fit naturally on her feet, realistic perspective, proper lighting and shadows, "
            "photorealistic blending, natural pose."
        )

        print(f"Inpaint prompt: {inpaint_prompt[:120]}...")

        try:
            # Try Method 1: SDXL Inpainting (stable and reliable)
            print("Trying SDXL Inpainting...")

            with open(scene_path, "rb") as scene_file, \
                 open(mask_path, "rb") as mask_file:

                output = replicate.run(
                    "stability-ai/stable-diffusion-inpainting:95b7223104132402a9ae91cc677285bc5eb997834bd2349fa486f53910fd68b3",
                    input={
                        "image": scene_file,
                        "mask": mask_file,
                        "prompt": inpaint_prompt,
                        "negative_prompt": (
                            "floating shoes, wrong shoes, different color, deformed feet, "
                            "distorted perspective, blurry, low quality, duplicate shoes"
                        ),
                        "num_inference_steps": 50,
                        "guidance_scale": 12.0,  # Higher = follow prompt more
                    }
                )

            print("SDXL Inpainting succeeded")

            # Download result
            inpaint_url = output[0] if isinstance(output, list) else output
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_filename = f"{filename_prefix}_inpaint_{timestamp}.png"
            final_path = save_path / final_filename

            response = requests.get(inpaint_url)
            response.raise_for_status()
            with open(final_path, 'wb') as f:
                f.write(response.content)

            # Cleanup
            self._cleanup_temp_files(save_path)

            print(f"Inpainted image saved: {final_path}")
            return str(final_path)

        except Exception as e:
            print(f"Warning: SDXL Inpainting failed: {str(e)}")

            # Try Method 2: IP-Adapter (uses product image as reference)
            try:
                print("Trying IP-Adapter with product reference...")

                with open(scene_path, "rb") as scene_file, \
                     open(product_path, "rb") as product_file:

                    output = replicate.run(
                        "tencentarc/photomaker:ddfc2b08d209f9fa8c1eca692712918bd449f695dabb4a958da31802a9570fe4",
                        input={
                            "image": scene_file,
                            "style_image": product_file,  # Product as reference
                            "prompt": inpaint_prompt,
                            "negative_prompt": "floating, wrong color, deformed, blurry",
                            "num_inference_steps": 50,
                            "guidance_scale": 10.0,
                            "style_strength": 0.8,  # Strong product reference
                        }
                    )

                print("IP-Adapter succeeded")

                # Download result
                output_url = output[0] if isinstance(output, list) else output
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                final_filename = f"{filename_prefix}_ipadapter_{timestamp}.png"
                final_path = save_path / final_filename

                response = requests.get(output_url)
                response.raise_for_status()
                with open(final_path, 'wb') as f:
                    f.write(response.content)

                # Cleanup
                self._cleanup_temp_files(save_path)

                print(f"IP-Adapter image saved: {final_path}")
                return str(final_path)

            except Exception as e2:
                print(f"Warning: IP-Adapter failed: {str(e2)}")
                print("Final fallback: Using smart composite...")

                # Fallback: Use smart composite
                return self._composite_images(
                    scene_path,
                    product_path,
                    save_path,
                    filename_prefix,
                    replicate
                )
        """

    def _composite_images(
        self,
        scene_path: str,
        product_path: str,
        save_path: Path,
        filename_prefix: str,
        replicate
    ) -> str:
        """
        Stage 3: Advanced composite using OpenCV Seamless Cloning

        Args:
            scene_path: Path to scene background
            product_path: Path to clean product
            save_path: Final output directory
            filename_prefix: Prefix for final filename
            replicate: Replicate module

        Returns:
            Path to final composited image
        """
        print("[Stage 3] Advanced seamless compositing...")

        try:
            import cv2
            import numpy as np
            from rembg import remove

            # 1. Remove background from product
            print("Removing product background...")
            product_img = Image.open(product_path)
            product_no_bg = remove(product_img)

            # Convert to OpenCV format
            product_cv = cv2.cvtColor(np.array(product_no_bg), cv2.COLOR_RGBA2BGRA)
            scene_cv = cv2.imread(str(scene_path))

            # 2. Resize product to fit scene (bottom 35% of image for better visibility)
            scene_h, scene_w = scene_cv.shape[:2]
            target_h = int(scene_h * 0.35)  # 35% of scene height
            product_h, product_w = product_cv.shape[:2]
            scale = target_h / product_h
            new_w = int(product_w * scale)

            product_resized = cv2.resize(product_cv, (new_w, target_h), interpolation=cv2.INTER_LANCZOS4)

            # 3. Extract product without background
            b, g, r, a = cv2.split(product_resized)
            product_rgb = cv2.merge([b, g, r])
            mask = a

            # 4. Position at bottom center
            x = (scene_w - new_w) // 2
            y = scene_h - target_h - int(scene_h * 0.05)  # 5% from bottom

            # 5. Create white background for product (required for seamlessClone)
            product_white_bg = np.ones_like(product_rgb) * 255
            product_white_bg[mask > 0] = product_rgb[mask > 0]

            # 6. Apply seamless cloning (Poisson blending)
            print("Applying Poisson seamless blending...")

            # Center point for cloning
            center = (x + new_w // 2, y + target_h // 2)

            # Resize mask to match product
            mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

            # Use cv2.NORMAL_CLONE for realistic blending
            try:
                blended = cv2.seamlessClone(
                    product_white_bg,
                    scene_cv,
                    mask_3ch,
                    center,
                    cv2.NORMAL_CLONE
                )
            except:
                # Fallback: Mixed clone
                blended = cv2.seamlessClone(
                    product_white_bg,
                    scene_cv,
                    mask_3ch,
                    center,
                    cv2.MIXED_CLONE
                )

            # 7. Save result
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_filename = f"{filename_prefix}_seamless_{timestamp}.png"
            final_path = save_path / final_filename

            cv2.imwrite(str(final_path), blended)

            # Cleanup (commented out temporarily to inspect intermediate files)
            # self._cleanup_temp_files(save_path)

            print(f"Seamless composite saved: {final_path}")
            print(f"Temp files kept for inspection: temp_scene_text2img.png, product_*.png")
            return str(final_path)

        except Exception as e:
            print(f"Warning: Seamless composite failed: {str(e)}")
            print("Using simple overlay...")

            # Ultimate fallback: Simple overlay
            try:
                from rembg import remove

                scene = Image.open(scene_path).convert("RGB")
                product_img = Image.open(product_path)
                product_no_bg = remove(product_img).convert("RGBA")

                scene_w, scene_h = scene.size
                product_w, product_h = product_no_bg.size

                # Resize to 25% of scene width
                target_width = int(scene_w * 0.25)
                scale_ratio = target_width / product_w
                new_product_h = int(product_h * scale_ratio)

                product_resized = product_no_bg.resize(
                    (target_width, new_product_h),
                    Image.Resampling.LANCZOS
                )

                # Position
                x = (scene_w - target_width) // 2
                y = scene_h - new_product_h - int(scene_h * 0.03)

                # Paste with alpha
                scene_rgba = scene.convert("RGBA")
                scene_rgba.paste(product_resized, (x, y), product_resized)

                # Save
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                final_filename = f"{filename_prefix}_overlay_{timestamp}.png"
                final_path = save_path / final_filename
                scene_rgba.convert("RGB").save(final_path, "PNG")

                # Cleanup
                self._cleanup_temp_files(save_path)

                print(f"Simple overlay saved: {final_path}")
                return str(final_path)

            except Exception as e2:
                print(f"Error: All composite methods failed: {str(e2)}")
                print("Final fallback: Simple paste without background removal")

                try:
                    # Last resort: Paste product as-is (with background) onto scene
                    scene = Image.open(scene_path).convert("RGB")
                    product = Image.open(product_path).convert("RGB")

                    scene_w, scene_h = scene.size
                    product_w, product_h = product.size

                    # Resize product to 30% of scene width
                    target_width = int(scene_w * 0.3)
                    scale_ratio = target_width / product_w
                    new_product_h = int(product_h * scale_ratio)

                    product_resized = product.resize(
                        (target_width, new_product_h),
                        Image.Resampling.LANCZOS
                    )

                    # Position at bottom center
                    x = (scene_w - target_width) // 2
                    y = scene_h - new_product_h - int(scene_h * 0.05)

                    # Paste product onto scene
                    scene.paste(product_resized, (x, y))

                    # Save
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    final_filename = f"{filename_prefix}_simple_{timestamp}.png"
                    final_path = save_path / final_filename
                    scene.save(final_path, "PNG")

                    # Cleanup
                    self._cleanup_temp_files(save_path)

                    print(f"Simple paste saved: {final_path}")
                    print("Note: Product pasted without background removal")
                    return str(final_path)

                except Exception as e3:
                    print(f"Error: Final fallback failed: {str(e3)}")
                    # Return scene only as absolute last resort
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    final_filename = f"{filename_prefix}_scene_only_{timestamp}.png"
                    final_path = save_path / final_filename
                    scene = Image.open(scene_path)
                    scene.save(final_path, "PNG")
                    self._cleanup_temp_files(save_path)
                    return str(final_path)

    def generate_with_sdxl(
        self,
        prompt: str,
        reference_image_path: str,
        save_path: Optional[Path] = None,
        filename_prefix: str = "sdxl"
    ) -> Dict[str, str]:
        """
        Generate product image using SIMPLE SDXL img2img
        - Send reference image + prompt directly
        - Let SDXL do all the work (scene + product together)

        Args:
            prompt: The prompt for image generation
            reference_image_path: Path to reference product image
            save_path: Directory to save the image (default: config.IMAGES_DIR)
            filename_prefix: Prefix for the saved filename

        Returns:
            Dictionary containing:
                - 'url': URL of the generated image
                - 'path': Local path where image was saved
                - 'prompt': Original prompt used
        """
        try:
            # Import replicate
            try:
                import replicate
            except ImportError:
                raise ImportError(
                    "Replicate package is required for SDXL mode. "
                    "Install it with: pip install replicate"
                )

            # Check API token
            replicate_token = config.REPLICATE_API_TOKEN
            if not replicate_token:
                raise ValueError(
                    "Replicate API token is required. Set REPLICATE_API_TOKEN environment variable."
                )

            print("Running SIMPLE SDXL img2img (reference + prompt)")
            print(f"Reference image: {reference_image_path}")

            if save_path is None:
                save_path = config.IMAGES_DIR

            # Build comprehensive prompt
            full_prompt = (
                f"{prompt}. "
                "Full body photograph of a young Thai woman (20-30 years old) wearing the SAME shoes from the reference image, "
                "standing in a modern outdoor Thai cafe garden with lush green plants and natural sunlight. "
                "The woman is clearly visible from head to toe in casual clothing. "
                "The shoes MUST match the reference image EXACTLY - same color, same design, same style, same brand. "
                "Do not alter the logo, sole shape, texture, stitching, or pattern. The product should remain identical to the uploaded reference image. "
                "Natural daylight, realistic photography, professional composition, vertical 9:16 format."
            )

            print(f"Full prompt: {full_prompt[:150]}...")

            # Simple img2img - one shot
            model = "stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc"

            with open(reference_image_path, "rb") as image_file:
                output = replicate.run(
                    model,
                    input={
                        "image": image_file,
                        "prompt": full_prompt,
                        "prompt_strength": 0.55,  # เพิ่มให้ prompt มีอิทธิพลขึ้น
                        "strength": 0.4,          # ให้ AI เริ่มปรับฉากใหม่ได้มากขึ้น
                        "guidance_scale": 12.0,   # ลดนิดเพื่อไม่ให้ AI ละเลย reference
                        "num_inference_steps": 50,
                        "refine": "no_refiner",   # ให้ SDXL ตีความ prompt เต็มที่
                        "scheduler": "K_EULER_ANCESTRAL",
                        "width": 768,
                        "height": 1344,  # 9:16
                        "negative_prompt": (
                            "blurry, wrong shoes, different shoes, floating feet, distorted perspective, "
                            "cartoon, painting, fake reflection, cropped feet, "
                            "deformed face, ugly face, bad anatomy, mutated hands, extra limbs"
                        )
                    }
                )

            # Get output URL
            output_url = output[0] if isinstance(output, list) else output
            print(f"SDXL generation complete")

            # Download and save
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_filename = f"{filename_prefix}_simple_{timestamp}.png"
            final_path = save_path / final_filename

            response = requests.get(output_url)
            response.raise_for_status()
            with open(final_path, 'wb') as f:
                f.write(response.content)

            print(f"Image saved: {final_path}")

            return {
                'url': output_url,
                'path': str(final_path),
                'prompt': prompt
            }

        except Exception as e:
            raise Exception(f"Failed to generate image with SDXL: {str(e)}")

    def generate_with_sdxl_refined(
        self,
        prompt: str,
        reference_image_path: str,
        save_path: Optional[Path] = None,
        filename_prefix: str = "sdxl_refined"
    ) -> Dict[str, str]:
        """
        Generate refined product image with SDXL Refiner.
        Keeps the product design identical, changes only the background.

        Args:
            prompt: The prompt for image generation
            reference_image_path: Path to reference product image
            save_path: Directory to save the image (default: config.IMAGES_DIR)
            filename_prefix: Prefix for the saved filename

        Returns:
            Dictionary containing:
                - 'url': URL of the generated image
                - 'path': Local path where image was saved
                - 'prompt': Original prompt used
        """
        try:
            import replicate

            replicate_token = config.REPLICATE_API_TOKEN
            if not replicate_token:
                raise ValueError(
                    "Replicate API token is required. Set REPLICATE_API_TOKEN environment variable."
                )

            print("Running 2-Stage Pipeline (Text2Img -> Inpaint)")
            print(f"Reference image: {reference_image_path}")

            if save_path is None:
                save_path = config.IMAGES_DIR

            # Build full prompt
            full_prompt = (
                f"{prompt}. "
                "OUTDOOR garden setting. A young Thai female standing in an OPEN-AIR garden cafe terrace with NO ROOF, "
                "wearing a short skirt, full body photograph from head to toe. "
                "She is standing BAREFOOT on a stone path showing her legs and feet clearly. "
                "Background: lush green tropical plants, wooden outdoor furniture, natural sunlight, blue sky visible above. "
                "Professional photography, bright natural daylight, realistic skin tone, vertical 9:16 format, sharp focus."
            )

            print("--- PROMPT DEBUG ---")
            print(f"Full prompt: {full_prompt}")
            print("-------------------------")

            # Stage 1: Generate scene from prompt ONLY (no image reference)
            print("[Stage 1] Generating scene from prompt (Text2Img)...")

            model = "stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc"

            scene_output = replicate.run(
                model,
                input={
                    "prompt": full_prompt,
                    "width": 768,
                    "height": 1344,
                    "num_inference_steps": 50,
                    "guidance_scale": 9.0,
                    "scheduler": "K_EULER_ANCESTRAL",
                    "refine": "expert_ensemble_refiner",
                    "negative_prompt": (
                        "shoes, footwear, sneakers, boots, sandals, slippers, any type of footwear, "
                        "shoes shoes shoes, footwear footwear footwear, "
                        "indoor, interior, enclosed space, roof, ceiling, walls, "
                        "tables blocking view, furniture in front, sitting, blurry, distorted perspective, "
                        "cartoon, painting, deformed face, ugly face, bad anatomy, mutated hands, extra limbs"
                    )
                }
            )

            # Download scene
            scene_url = scene_output[0] if isinstance(scene_output, list) else scene_output
            scene_path = save_path / "temp_scene_text2img.png"

            response = requests.get(scene_url)
            response.raise_for_status()
            with open(scene_path, 'wb') as f:
                f.write(response.content)

            print(f"Scene generated: {scene_path}")

            # Stage 2: Clean product
            print("[Stage 2] Cleaning product image...")
            product_path = self._generate_product_clean(
                reference_image_path,
                save_path,
                replicate
            )

            # Stage 3: Inpaint product onto scene
            print("[Stage 3] Inpainting product onto scene...")
            final_path = self._inpaint_product_onto_scene(
                str(scene_path),
                product_path,
                prompt,
                save_path,
                filename_prefix,
                replicate
            )

            print(f"2-Stage pipeline complete: {final_path}")

            # Get URL (return empty since final is composite)
            output_url = ""
            image_path = final_path

            return {
                'url': output_url,
                'path': str(image_path),
                'prompt': prompt
            }

        except Exception as e:
            raise Exception(f"Failed to generate refined SDXL image: {str(e)}")

    def generate_with_sdxl_controlnet_reference(
        self,
        reference_image_path: str,
        background_prompt: str = "modern Thai outdoor cafe, tropical plants, natural sunlight",
        save_path: Optional[Path] = None,
        filename_prefix: str = "sdxl_controlnet",
        seed: Optional[int] = None
    ) -> Dict[str, str]:
        """
        ULTIMATE METHOD: SDXL + ControlNet Reference-Only
        ยึดรูปสินค้าต้นฉบับ 100% + สร้างฉากรอบๆ

        Args:
            reference_image_path: Path to product image
            background_prompt: Light prompt for background/scene only
            save_path: Directory to save image
            filename_prefix: Filename prefix
            seed: Random seed for reproducibility

        Returns:
            Dictionary with image info
        """
        try:
            import replicate
            import requests
            from pathlib import Path
            from datetime import datetime

            replicate_token = config.REPLICATE_API_TOKEN
            if not replicate_token:
                raise ValueError("Replicate API token required")

            if save_path is None:
                save_path = config.IMAGES_DIR

            print("=== 🎯 ULTIMATE: SDXL + ControlNet Reference-Only ===")
            print(f"Reference: {reference_image_path}")
            print(f"Background: {background_prompt}")

            # Use SDXL with ControlNet IP-Adapter (reference-only)
            model = "batouresearch/sdxl-controlnet-lora:4f2d6cffaaa9f0bb6c8a53c409177df7c4e2e1ff02b1f6c28fc48b21c4ce87d4"

            # Minimal prompt - focus on scene, not product
            minimal_prompt = f"A lifestyle product photography scene: {background_prompt}, professional composition, natural lighting, vertical 9:16 format"

            with open(reference_image_path, "rb") as image_file:
                input_params = {
                    "image": image_file,
                    "prompt": minimal_prompt,
                    "structure": "canny",  # Use canny edge for product structure preservation
                    "guidance_scale": 3.5,  # VERY LOW - let reference dominate
                    "prompt_strength": 0.05,  # EXTREMELY LOW - almost ignore prompt
                    "controlnet_conditioning_scale": 1.5,  # HIGH - strong reference influence
                    "num_inference_steps": 50,
                    "width": 768,
                    "height": 1344,
                    "negative_prompt": "different product, modified product, changed colors, altered design, cartoon, 3d render, low quality"
                }

                if seed is not None:
                    input_params["seed"] = seed

                print("🔄 Generating with ControlNet reference-only mode...")
                output = replicate.run(model, input=input_params)

            # Get output
            image_url = output[0] if isinstance(output, list) else output

            # Download and save
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_filename = f"{filename_prefix}_{timestamp}.png"
            final_path = save_path / final_filename

            response = requests.get(image_url)
            response.raise_for_status()
            with open(final_path, 'wb') as f:
                f.write(response.content)

            print(f"✅ [SUCCESS] {final_path}")

            return {
                'url': image_url,
                'path': str(final_path),
                'prompt': minimal_prompt
            }

        except Exception as e:
            print(f"⚠️  ControlNet method failed: {e}")
            print("Falling back to standard SDXL img2img...")
            # Fallback to standard method
            return self.generate_with_sdxl_simple(
                prompt=background_prompt,
                reference_image_path=reference_image_path,
                save_path=save_path,
                filename_prefix=filename_prefix,
                seed=seed,
                prompt_strength=0.15
            )

    def generate_with_sdxl_simple(
        self,
        prompt: str,
        reference_image_path: str,
        save_path: Optional[Path] = None,
        filename_prefix: str = "sdxl_simple",
        seed: Optional[int] = None,
        prompt_strength: float = 0.35
    ) -> Dict[str, str]:
        """
        ULTRA SIMPLE img2img - ไม่ซับซ้อน ไม่ขัดแย้ง
        ส่ง reference image + prompt สั้น ๆ เข้า SDXL แค่นั้น

        Args:
            prompt: Short, clear prompt (no conflicts)
            reference_image_path: Path to reference product image
            save_path: Directory to save the image
            filename_prefix: Prefix for filename

        Returns:
            Dictionary with image URL, path, and prompt
        """
        try:
            import replicate
            import requests
            from pathlib import Path
            from datetime import datetime

            replicate_token = config.REPLICATE_API_TOKEN
            if not replicate_token:
                raise ValueError("Replicate API token is required")

            if save_path is None:
                save_path = config.IMAGES_DIR

            print("=== ULTRA SIMPLE img2img Pipeline ===")
            print(f"Reference: {reference_image_path}")
            print(f"Prompt: {prompt[:150]}...")

            model = "stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc"

            # SIMPLE STRATEGY: img2img with high reference strength
            with open(reference_image_path, "rb") as image_file:
                input_params = {
                    "image": image_file,
                    "prompt": prompt,
                    "prompt_strength": min(prompt_strength, 0.25),  # FORCE lower values for stronger reference adherence
                    "strength": 0.6,  # Higher strength = preserve more of original image
                    "num_inference_steps": 60,  # More steps for better quality
                    "guidance_scale": 8.0,  # LOWERED: Less prompt influence, more reference influence
                    "scheduler": "K_EULER_ANCESTRAL",
                    "refine": "expert_ensemble_refiner",
                    "width": 768,
                    "height": 1344,  # 9:16
                    "negative_prompt": (
                        "different product, modified product, changed product, altered product, wrong product, "
                        "different color, wrong color, different design, wrong design, different style, "
                        "different brand, wrong brand, changed logo, modified logo, altered logo, "
                        "face visible, portrait, face in frame, upper body visible, head visible, "
                        "person dominant, model focused, human centered, people prominent, "
                        "standing straight, stiff pose, formal pose, passport photo, "
                        "artificial background, fake garden, computer generated, cgi, "
                        "blurry, low quality, distorted, deformed, cartoon, 3d render, "
                        "bad anatomy, deformed feet, extra limbs, mutated, ugly, artifacts"
                    )
                }

                # Add seed if provided (for reproducibility)
                if seed is not None:
                    input_params["seed"] = seed
                    print(f"Using seed: {seed}")

                output = replicate.run(model, input=input_params)

            # Get output
            image_url = output[0] if isinstance(output, list) else output

            # Download and save
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_filename = f"{filename_prefix}_{timestamp}.png"
            final_path = save_path / final_filename

            response = requests.get(image_url)
            response.raise_for_status()
            with open(final_path, 'wb') as f:
                f.write(response.content)

            print(f"[SUCCESS] {final_path}")

            return {
                'url': image_url,
                'path': str(final_path),
                'prompt': prompt
            }

        except Exception as e:
            raise Exception(f"Failed to generate SDXL image: {str(e)}")

    def generate_with_gemini_vision(
        self,
        prompt: str,
        reference_image_path: str,
        save_path: Optional[Path] = None,
        filename_prefix: str = "gemini_vision"
    ) -> Dict[str, str]:
        """
        Generate product analysis using Gemini Vision API directly (no backend needed)

        Args:
            prompt: The prompt for image generation
            reference_image_path: Path to reference product image
            save_path: Directory to save the image (default: config.IMAGES_DIR)
            filename_prefix: Prefix for the saved filename

        Returns:
            Dictionary containing:
                - 'url': URL of the generated image (if available)
                - 'path': Local path where image was saved
                - 'prompt': Original prompt used
                - 'analysis': Gemini analysis text
        """
        try:
            print("=== GEMINI VISION Analysis (Direct API) ===")
            print(f"Reference: {reference_image_path}")
            print(f"Prompt: {prompt[:150]}...")

            if save_path is None:
                save_path = config.IMAGES_DIR

            # Use Gemini Vision directly
            if not hasattr(self, 'gemini_model') or not self.use_gemini:
                raise Exception("Gemini is not initialized. Please set GEMINI_API_KEY")

            # Load image
            from PIL import Image as PILImage
            img = PILImage.open(reference_image_path)

            # Create vision prompt
            vision_prompt = f"""
Analyze this product image in detail for affiliate marketing purposes.

User's request: {prompt}

Please provide:
1. Product type and category
2. Key visual features (colors, design, materials)
3. Brand or logo identification (if visible)
4. Unique selling points visible in the image
5. Recommended photography angle and lighting for marketing
6. Target audience based on product style

Keep the analysis concise but detailed (max 300 words).
"""

            # Use Gemini 1.5 Flash for vision analysis (multimodal)
            vision_model = genai.GenerativeModel('gemini-1.5-flash')
            response = vision_model.generate_content([vision_prompt, img])
            analysis_text = response.text.strip()

            print(f"Gemini Analysis: {analysis_text[:200]}...")

            # Save the analysis to a text file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            analysis_filename = f"{filename_prefix}_analysis_{timestamp}.txt"
            analysis_path = save_path / analysis_filename

            with open(analysis_path, 'w', encoding='utf-8') as f:
                f.write("=== GEMINI VISION ANALYSIS (Direct API) ===\n")
                f.write(f"Original Prompt: {prompt}\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"Model: gemini-pro-vision\n\n")
                f.write("=== PRODUCT ANALYSIS ===\n")
                f.write(analysis_text)
                f.write("\n\n=== RECOMMENDATIONS ===\n")
                f.write("Use this analysis to create a better prompt for DALL-E or SDXL image generation.\n")
                f.write("The analysis provides detailed product description for maximum fidelity.\n")

            print(f"[SUCCESS] Gemini Vision analysis saved: {analysis_path}")

            # Create a visual summary image
            from PIL import ImageDraw, ImageFont

            img_summary = PILImage.new('RGB', (768, 1344), color='white')
            draw = ImageDraw.Draw(img_summary)

            try:
                font = ImageFont.load_default()
            except:
                font = None

            # Add content to image
            text_lines = [
                "🔮 GEMINI VISION ANALYSIS",
                "   (Direct API - No Backend Needed)",
                "",
                "📊 Product Analysis Complete",
                "",
                "✅ Gemini Pro Vision",
                "✅ Analysis: Detailed product insights",
                "",
                "📁 Full analysis saved to:",
                f"   {analysis_filename}",
                "",
                "💡 Next Steps:",
                "1. Review the analysis",
                "2. Use insights for DALL-E/SDXL",
                "3. Generate with better prompts",
                "",
                "🎯 Goal: 100% Product Fidelity"
            ]

            y_offset = 50
            for line in text_lines:
                draw.text((50, y_offset), line, fill='black', font=font)
                y_offset += 35

            # Save the summary image
            summary_filename = f"{filename_prefix}_summary_{timestamp}.png"
            summary_path = save_path / summary_filename
            img_summary.save(summary_path)

            # Return result
            return {
                'url': '',  # No URL for generated content
                'path': str(summary_path),
                'prompt': prompt,
                'analysis': analysis_text,
                'analysis_file': str(analysis_path)
            }

        except Exception as e:
            raise Exception(f"Failed to analyze with Gemini Vision: {str(e)}")

    def generate_with_gemini_analysis_then_sdxl(
        self,
        prompt: str,
        reference_image_path: str,
        save_path: Optional[Path] = None,
        filename_prefix: str = "gemini_sdxl_hybrid"
    ) -> Dict[str, str]:
        """
        DIRECT METHOD: Gemini 1.5 Flash analyzes image → Creates detailed prompt → SDXL generates

        This is the "ตรงๆ" approach using Gemini API directly

        Args:
            prompt: The prompt for image generation
            reference_image_path: Path to reference product image
            save_path: Directory to save the image (default: config.IMAGES_DIR)
            filename_prefix: Prefix for the saved filename

        Returns:
            Dictionary containing:
                - 'url': URL of the generated image
                - 'path': Local path where image was saved
                - 'prompt': Enhanced prompt used
                - 'analysis': Gemini analysis text
        """
        try:
            import replicate
            from PIL import Image as PILImage

            print("=== 🚀 DIRECT METHOD: Gemini 1.5 Flash → SDXL ===")

            if save_path is None:
                save_path = config.IMAGES_DIR

            # Check Gemini availability
            if not hasattr(self, 'gemini_model') or not self.use_gemini:
                raise Exception("Gemini is not initialized. Please set GEMINI_API_KEY")

            # Check Replicate token
            if not config.REPLICATE_API_TOKEN:
                raise ValueError("Replicate API token required for SDXL generation")

            # Step 1: Load product image
            print("[Step 1/3] 📸 Loading product image...")
            product_img = PILImage.open(reference_image_path)

            # Step 2: Analyze with Gemini 1.5 Flash (multimodal)
            print("[Step 2/3] 🔮 Analyzing with Gemini 1.5 Flash...")

            vision_model = genai.GenerativeModel('gemini-1.5-flash')

            analysis_prompt = f"""
You are a professional product photographer. Analyze this product image and create a COMPLETE, DETAILED prompt for an AI image generator.

Original request: {prompt}

Based on the product in the image, create ONE detailed paragraph describing the EXACT scene to generate:

1. Describe the product SPECIFICALLY (colors, style, brand if visible, design details)
2. Create a complete scene with a Thai model using/wearing this product
3. Specify the environment (Thai cafe, outdoor, indoor, lighting)
4. Camera angle and composition for best product visibility
5. Style and mood (Instagram, professional, lifestyle, etc.)

Write as ONE flowing paragraph, ready to send directly to Stable Diffusion XL.
Be VERY specific about the product details you see.

Example format: "A Thai young woman in her twenties wearing [specific product details from image: exact colors, design, style], sitting at a modern outdoor Bangkok cafe with natural afternoon sunlight streaming through tropical plants, shot from a low angle to showcase the product clearly, bright and airy Instagram aesthetic, vertical 9:16 format, professional product photography"

Write ONLY the complete prompt, nothing else.
"""

            response = vision_model.generate_content([analysis_prompt, product_img])
            enhanced_prompt = response.text.strip()

            print(f"✅ Gemini generated prompt ({len(enhanced_prompt)} chars)")
            print(f"📝 Prompt preview: {enhanced_prompt[:200]}...")

            # Step 3: Generate with SDXL using Gemini's prompt
            print("[Step 3/3] 🎨 Generating image with SDXL...")

            sdxl_result = self.generate_with_sdxl_simple(
                prompt=enhanced_prompt,
                reference_image_path=reference_image_path,
                save_path=save_path,
                filename_prefix=f"{filename_prefix}_final",
                prompt_strength=0.20  # Balance between prompt and reference
            )

            # Save analysis for reference
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            analysis_path = save_path / f"{filename_prefix}_prompt_{timestamp}.txt"
            with open(analysis_path, 'w', encoding='utf-8') as f:
                f.write("=== GEMINI 1.5 FLASH GENERATED PROMPT ===\n\n")
                f.write(f"Original request: {prompt}\n\n")
                f.write("=== ENHANCED PROMPT ===\n\n")
                f.write(enhanced_prompt)

            # Combine results
            final_result = {
                'url': sdxl_result['url'],
                'path': sdxl_result['path'],
                'prompt': enhanced_prompt,
                'original_prompt': prompt,
                'analysis': enhanced_prompt,
                'analysis_file': str(analysis_path)
            }

            print(f"✅ [SUCCESS] Image generated: {final_result['path']}")
            print(f"📄 Prompt saved: {analysis_path}")
            return final_result

        except Exception as e:
            raise Exception(f"Failed Gemini→SDXL generation: {str(e)}")

    def _create_enhanced_prompt_via_backend(
        self,
        original_prompt: str,
        gemini_analysis: str
    ) -> str:
        """
        Create enhanced prompt using Express.js backend
        """
        try:
            import requests
            
            backend_url = "http://localhost:5000"
            
            payload = {
                "analysis": gemini_analysis,
                "originalPrompt": original_prompt,
                "productType": "shoes"
            }
            
            response = requests.post(
                f"{backend_url}/api/create-enhanced-prompt",
                json=payload,
                timeout=30
            )
            
            if response.ok:
                result = response.json()
                if result.get('success'):
                    return result.get('enhancedPrompt', original_prompt)
            
            print("Warning: Backend enhanced prompt failed, using local method")
            
        except Exception as e:
            print(f"Warning: Could not use backend for enhanced prompt: {e}")
        
        # Fallback to local method
        return self._create_enhanced_prompt_from_analysis(original_prompt, gemini_analysis)

    def _create_enhanced_prompt_from_analysis(
        self,
        original_prompt: str,
        gemini_analysis: str
    ) -> str:
        """
        Create enhanced prompt by combining original prompt with Gemini analysis insights
        """
        
        # Extract key product details from analysis
        key_details = []
        
        # Look for color mentions
        if "color" in gemini_analysis.lower():
            color_match = self._extract_color_details(gemini_analysis)
            if color_match:
                key_details.append(f"Color: {color_match}")
        
        # Look for design details
        if "design" in gemini_analysis.lower():
            design_match = self._extract_design_details(gemini_analysis)
            if design_match:
                key_details.append(f"Design: {design_match}")
        
        # Look for brand details
        if any(word in gemini_analysis.lower() for word in ["brand", "logo", "label"]):
            brand_match = self._extract_brand_details(gemini_analysis)
            if brand_match:
                key_details.append(f"Brand: {brand_match}")
        
        # Create enhanced prompt
        enhanced_parts = [
            original_prompt,
            "CRITICAL PRODUCT FIDELITY: Based on AI analysis, ensure these exact details:",
            " | ".join(key_details) if key_details else "Match reference image exactly",
            "The product must appear IDENTICAL to the reference - same color, design, brand, texture.",
            "Focus on product accuracy over artistic interpretation.",
            "Professional product photography, natural lighting, 9:16 vertical format."
        ]
        
        return " ".join(enhanced_parts)

    def _extract_color_details(self, text: str) -> str:
        """Extract color information from analysis text"""
        colors = ["black", "white", "red", "blue", "green", "yellow", "pink", "brown", "gray", "grey"]
        found_colors = [color for color in colors if color in text.lower()]
        return ", ".join(found_colors) if found_colors else ""

    def _extract_design_details(self, text: str) -> str:
        """Extract design information from analysis text"""
        design_keywords = ["sneaker", "boot", "sandal", "heel", "flat", "lace", "strap"]
        found_designs = [design for design in design_keywords if design in text.lower()]
        return ", ".join(found_designs) if found_designs else ""

    def _extract_brand_details(self, text: str) -> str:
        """Extract brand information from analysis text"""
        brands = ["nike", "adidas", "puma", "converse", "vans", "new balance", "reebok"]
        found_brands = [brand for brand in brands if brand in text.lower()]
        return ", ".join(found_brands) if found_brands else ""


# Example usage
if __name__ == "__main__":
    # Check if API key is set
    if not config.OPENAI_API_KEY:
        print("Please set OPENAI_API_KEY environment variable")
        exit(1)

    # Initialize generator
    generator = DALLEGenerator()

    # Example prompt
    test_prompt = (
        "Realistic iPhone photo, natural lighting, high quality, "
        "young Asian male model in their early twenties, "
        "wearing stylish modern shoes, full body shot, standing pose, "
        "professional photography, advertisement style, clean background, "
        "sharp focus, 9:16 aspect ratio, instagram-worthy"
    )

    print("Generating test image...")
    print(f"Prompt: {test_prompt}\n")

    try:
        result = generator.generate_image(
            prompt=test_prompt,
            filename_prefix="test"
        )

        print("Image generated successfully!")
        print(f"Saved to: {result['path']}")
        print(f"Revised prompt: {result['revised_prompt']}")

    except Exception as e:
        print(f"Error: {e}")
