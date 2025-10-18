"""
Kie.ai Generator for AI Product Visualizer
Generates images using Kie.ai Nano Banana Edit API
"""

import requests
import time
import json
import base64
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
import config
from PIL import Image
import io


class KieGenerator:
    """Generate images using Kie.ai Nano Banana Edit API"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Kie.ai Generator

        Args:
            api_key: Kie.ai API key (optional, will use config if not provided)
        """
        self.api_key = api_key or config.KIE_API_KEY
        self.base_url = "https://api.kie.ai/api/v1"
        self.model = "google/nano-banana-edit"

        if not self.api_key:
            print("⚠️  Warning: KIE_API_KEY not found")

    def get_credits(self) -> Dict:
        """
        Get remaining credits from Kie.ai account

        Returns:
            Dict with credit information
        """
        url = f"{self.base_url}/user/credits"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            result = response.json()

            if result.get("code") == 200:
                return {
                    'success': True,
                    'credits': result.get("data", {}).get("credits", 0),
                    'currency': result.get("data", {}).get("currency", "credits")
                }
            else:
                return {
                    'success': False,
                    'error': result.get('message', 'Unknown error')
                }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }

    def resize_image_for_upload(self, image_path: str, max_width: int = 1920, max_height: int = 1080) -> bytes:
        """
        Resize image to optimize upload speed and API processing

        Args:
            image_path: Path to image file
            max_width: Maximum width (default 1920)
            max_height: Maximum height (default 1080)

        Returns:
            Resized image as bytes (JPEG format)
        """
        try:
            img = Image.open(image_path)
            original_width, original_height = img.size

            print(f"   Original size: {original_width}x{original_height}")

            # Calculate new size maintaining aspect ratio
            ratio = min(max_width / original_width, max_height / original_height, 1.0)

            if ratio < 1.0:
                new_width = int(original_width * ratio)
                new_height = int(original_height * ratio)

                # Resize with high quality
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                print(f"   Resized to: {new_width}x{new_height} (reduced by {int((1-ratio)*100)}%)")
            else:
                print(f"   No resize needed (already optimal size)")

            # Convert to RGB if needed (for JPEG)
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = rgb_img

            # Save to bytes with optimization
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=90, optimize=True)
            buffer.seek(0)

            resized_bytes = buffer.getvalue()
            original_size_kb = Path(image_path).stat().st_size / 1024
            resized_size_kb = len(resized_bytes) / 1024

            print(f"   File size: {original_size_kb:.1f}KB → {resized_size_kb:.1f}KB (reduced by {int((1-resized_size_kb/original_size_kb)*100)}%)")

            return resized_bytes

        except Exception as e:
            print(f"⚠️  Resize failed, using original: {e}")
            # Fallback: return original image
            with open(image_path, 'rb') as f:
                return f.read()

    def upload_image_to_imgbb(self, image_path: str, imgbb_api_key: str, max_retries: int = 3) -> str:
        """
        Upload image to imgbb.com and get public URL

        Args:
            image_path: Path to local image file
            imgbb_api_key: imgbb API key
            max_retries: Maximum number of retry attempts

        Returns:
            Public URL of uploaded image
        """
        print(f"📤 Uploading image to imgbb: {image_path}")

        # Resize image for faster upload and processing
        resized_image_bytes = self.resize_image_for_upload(image_path)

        # Encode resized image
        image_data = base64.b64encode(resized_image_bytes).decode('utf-8')

        # Upload to imgbb with retry
        url = "https://api.imgbb.com/1/upload"
        payload = {
            'key': imgbb_api_key,
            'image': image_data
        }

        last_error = None
        for attempt in range(max_retries):
            try:
                print(f"   Attempt {attempt + 1}/{max_retries}...")
                response = requests.post(url, data=payload, timeout=60)  # Increased timeout to 60s
                response.raise_for_status()

                result = response.json()

                if result.get('success'):
                    image_url = result['data']['url']
                    print(f"✅ Image uploaded: {image_url}")
                    return image_url
                else:
                    raise Exception(f"imgbb upload failed: {result.get('error', {}).get('message', 'Unknown error')}")

            except requests.exceptions.SSLError as e:
                last_error = e
                print(f"⚠️  SSL Error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    print(f"   Retrying in 2 seconds...")
                    time.sleep(2)
                continue

            except requests.exceptions.RequestException as e:
                last_error = e
                print(f"❌ Upload failed on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    print(f"   Retrying in 2 seconds...")
                    time.sleep(2)
                continue

        # All retries failed
        print(f"❌ Upload failed after {max_retries} attempts")
        raise last_error if last_error else Exception("Upload failed")

    def create_webhook(self) -> Dict[str, str]:
        """
        Create a temporary webhook using webhook.site

        Returns:
            Dict with 'webhook_url' and 'webhook_id'
        """
        try:
            # Create webhook via webhook.site API
            response = requests.post("https://webhook.site/token", timeout=30)
            response.raise_for_status()

            data = response.json()
            webhook_id = data.get('uuid')
            webhook_url = f"https://webhook.site/{webhook_id}"

            print(f"✅ Created temporary webhook: {webhook_url}")
            return {
                'webhook_url': webhook_url,
                'webhook_id': webhook_id
            }
        except Exception as e:
            print(f"❌ Failed to create webhook: {e}")
            # Return None to proceed without callback
            return None

    def get_webhook_requests(self, webhook_id: str) -> list:
        """
        Get all requests received by the webhook

        Args:
            webhook_id: Webhook UUID

        Returns:
            List of requests
        """
        try:
            url = f"https://webhook.site/token/{webhook_id}/requests"
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()
            return data.get('data', [])
        except Exception as e:
            print(f"❌ Failed to get webhook requests: {e}")
            return []

    def create_task(
        self,
        prompt: str,
        reference_image_urls: List[str],
        image_size: str = "9:16",
        output_format: str = "png",
        callback_url: Optional[str] = None
    ) -> tuple:
        """
        Create image generation task

        Args:
            prompt: The prompt for image editing
            reference_image_urls: List of reference image URLs (max 10)
            image_size: Output image size (1:1, 9:16, 16:9, etc.)
            output_format: Output format (png or jpeg)
            callback_url: Optional callback URL (webhook)

        Returns:
            Tuple of (task_id, webhook_id) or (task_id, None)
        """
        url = f"{self.base_url}/jobs/createTask"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # Create webhook if callback_url not provided
        webhook_id = None
        if not callback_url:
            webhook_data = self.create_webhook()
            if webhook_data:
                callback_url = webhook_data['webhook_url']
                webhook_id = webhook_data['webhook_id']
                print(f"📞 Using temporary webhook for callback")

        payload = {
            "model": self.model,
            "input": {
                "prompt": prompt,
                "image_urls": reference_image_urls,
                "output_format": output_format,
                "image_size": image_size
            }
        }

        # Add callback URL if available
        if callback_url:
            payload["callBackUrl"] = callback_url
            print(f"📞 Callback URL: {callback_url}")

        print(f"🚀 Creating Kie.ai task...")
        print(f"   Model: {self.model}")
        print(f"   Image size: {image_size}")
        print(f"   Reference images: {len(reference_image_urls)}")

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()

            if result.get("code") == 200:
                task_id = result["data"]["taskId"]
                print(f"✅ Task created: {task_id}")
                print(f"📋 Full response: {json.dumps(result, indent=2)}")
                return task_id, webhook_id
            else:
                raise Exception(f"API Error: {result.get('message', 'Unknown error')}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            raise

    def query_task(self, task_id: str) -> Dict:
        """
        Query task status using the correct recordInfo endpoint

        Args:
            task_id: Task ID from create_task

        Returns:
            Task status and results
        """
        # Correct endpoint for Nano Banana API
        url = f"{self.base_url}/playground/recordInfo?taskId={task_id}"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            print(f"🔍 Querying task status: {url}")
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            result = response.json()

            # Log the full response for debugging
            if result.get("code") != 200:
                print(f"⚠️  API returned non-200 code: {json.dumps(result, indent=2)}")

            return result

        except requests.exceptions.RequestException as e:
            print(f"❌ Query failed: {e}")
            print(f"💡 Tip: If polling doesn't work, Kie.ai might require using callback URL")
            print(f"   The webhook callback should deliver results automatically")
            raise

    def wait_for_task(
        self,
        task_id: str,
        webhook_id: Optional[str] = None,
        max_wait_time: int = 600,
        poll_interval: int = 10
    ) -> Dict:
        """
        Wait for task to complete using webhook callback

        Args:
            task_id: Task ID
            webhook_id: Webhook UUID (if using webhook.site)
            max_wait_time: Maximum time to wait (seconds)
            poll_interval: Time between status checks (seconds)

        Returns:
            Final task result
        """
        start_time = time.time()

        print(f"⏳ Waiting for task to complete...")

        if webhook_id:
            print(f"📞 Polling webhook for callback...")

        poll_attempt = 0

        while True:
            elapsed = time.time() - start_time

            if elapsed > max_wait_time:
                print(f"❌ Task {task_id} timed out after {max_wait_time}s")
                print(f"💡 The task may still be processing. Check your Kie.ai dashboard or try again later.")
                raise TimeoutError(f"Task {task_id} timed out after {max_wait_time}s")

            # Try webhook first if available (check every iteration)
            if webhook_id:
                requests_list = self.get_webhook_requests(webhook_id)

                for req in requests_list:
                    try:
                        # Parse webhook content
                        content = req.get('content', '{}')
                        if isinstance(content, str):
                            callback_data = json.loads(content)
                        else:
                            callback_data = content

                        # Check if this is our task
                        if callback_data.get('data', {}).get('taskId') == task_id:
                            state = callback_data.get('data', {}).get('state')

                            if state == 'success':
                                print(f"✅ Task completed successfully (via webhook)!")
                                return callback_data
                            elif state == 'fail':
                                fail_msg = callback_data.get('data', {}).get('failMsg', 'Unknown error')
                                raise Exception(f"Task failed: {fail_msg}")
                    except json.JSONDecodeError as e:
                        print(f"⚠️  Error parsing webhook JSON: {e}")
                        continue
                    except Exception as e:
                        print(f"⚠️  Error processing webhook: {e}")
                        continue

            # Try direct query every 3rd attempt (to reduce API calls)
            poll_attempt += 1
            if poll_attempt % 3 == 0:
                try:
                    result = self.query_task(task_id)

                    if result.get("code") == 200:
                        data = result.get("data", {})
                        state = data.get("state")

                        if state == "success":
                            print(f"✅ Task completed successfully (via polling)!")
                            return result
                        elif state == "fail":
                            fail_msg = data.get("failMsg", "Unknown error")
                            raise Exception(f"Task failed: {fail_msg}")
                        else:
                            print(f"   Status: {state} ({int(elapsed)}s elapsed)")
                    else:
                        print(f"   Polling unavailable, waiting for webhook... ({int(elapsed)}s elapsed)")
                except Exception as e:
                    # Query failed, continue waiting for webhook
                    print(f"   Waiting for webhook callback... ({int(elapsed)}s elapsed)")
            else:
                print(f"   Waiting... ({int(elapsed)}s elapsed)")

            time.sleep(poll_interval)

    def download_image(self, image_url: str, save_path: Path, max_retries: int = 3) -> Path:
        """
        Download generated image with retry logic

        Args:
            image_url: URL of generated image
            save_path: Path to save image
            max_retries: Maximum number of retry attempts

        Returns:
            Path to saved image
        """
        print(f"📥 Downloading image from {image_url}")

        # Ensure directory exists
        save_path.parent.mkdir(parents=True, exist_ok=True)

        last_error = None
        for attempt in range(max_retries):
            try:
                print(f"   Attempt {attempt + 1}/{max_retries}...")

                # Use streaming download with per-chunk timeout
                # timeout=(connect, read) - read timeout applies to each chunk
                response = requests.get(image_url, timeout=(30, 60), stream=True)
                response.raise_for_status()

                # Get file size if available
                total_size = int(response.headers.get('content-length', 0))

                # Download with progress
                downloaded = 0
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                            if total_size > 0:
                                progress = (downloaded / total_size) * 100
                                print(f"   Progress: {progress:.1f}%", end='\r')

                # Check if download is complete
                if total_size > 0 and downloaded < total_size:
                    missing_pct = ((total_size - downloaded) / total_size) * 100
                    if missing_pct < 5:  # Less than 5% missing
                        print(f"\n   ⚠️ Downloaded {(downloaded/total_size)*100:.1f}% - accepting (missing {missing_pct:.1f}%)")
                    else:
                        raise Exception(f"Incomplete download: {downloaded}/{total_size} bytes ({missing_pct:.1f}% missing)")

                print(f"\n✅ Saved to: {save_path}")
                return save_path

            except requests.exceptions.Timeout as e:
                last_error = e
                print(f"\n⚠️  Download timeout on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5  # Progressive backoff: 5s, 10s, 15s
                    print(f"   Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                continue

            except requests.exceptions.RequestException as e:
                last_error = e
                print(f"\n❌ Download failed on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    print(f"   Retrying in 5 seconds...")
                    time.sleep(5)
                continue

        # All retries failed
        print(f"\n❌ Download failed after {max_retries} attempts")
        raise last_error if last_error else Exception("Download failed")

    def generate_image(
        self,
        prompt: str,
        reference_image_paths: List[str],
        filename_prefix: str = "kie",
        image_size: str = "9:16",
        output_format: str = "png",
        imgbb_api_key: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Complete workflow: Upload images, create task, wait, download image

        Args:
            prompt: Generation prompt
            reference_image_paths: List of local image paths (will be auto-uploaded)
            filename_prefix: Prefix for saved filename
            image_size: Output size
            output_format: Output format
            imgbb_api_key: imgbb API key for auto-upload (optional)

        Returns:
            Dict with 'path', 'url', 'prompt', 'task_id'
        """
        print("="*80)
        print("🎨 Kie.ai Nano Banana Generation")
        print("="*80)
        print(f"Prompt: {prompt[:100]}...")
        print(f"Reference images: {len(reference_image_paths)}")
        print("="*80)

        try:
            # Step 0: Upload images to imgbb if needed
            reference_image_urls = []
            for img_path in reference_image_paths:
                # Check if it's already a URL
                if img_path.startswith('http://') or img_path.startswith('https://'):
                    reference_image_urls.append(img_path)
                else:
                    # Upload to imgbb
                    if not imgbb_api_key:
                        raise ValueError(
                            "imgbb_api_key is required for uploading local images. "
                            "Get your free API key from https://api.imgbb.com/"
                        )
                    uploaded_url = self.upload_image_to_imgbb(img_path, imgbb_api_key)
                    reference_image_urls.append(uploaded_url)

            print(f"✅ All images ready: {len(reference_image_urls)} URLs")
            print("="*80)

            # Step 1: Create task (with webhook)
            task_id, webhook_id = self.create_task(
                prompt=prompt,
                reference_image_urls=reference_image_urls,
                image_size=image_size,
                output_format=output_format
            )

            # Step 2: Wait for completion (using webhook)
            result = self.wait_for_task(task_id, webhook_id=webhook_id)

        except TimeoutError as e:
            print("="*80)
            print("❌ TIMEOUT ERROR")
            print("="*80)
            print(f"Error: {str(e)}")
            print("\n🔧 Troubleshooting steps:")
            print("1. The Kie.ai API may be experiencing high load")
            print("2. Try again in a few minutes")
            print("3. Check your Kie.ai dashboard for task status")
            print("4. Verify your API key has sufficient credits")
            print("="*80)
            raise

        except requests.exceptions.RequestException as e:
            print("="*80)
            print("❌ NETWORK/API ERROR")
            print("="*80)
            print(f"Error: {str(e)}")
            print("\n🔧 Troubleshooting steps:")
            print("1. Check your internet connection")
            print("2. Verify your KIE_API_KEY is correct")
            print("3. Check if api.kie.ai is accessible")
            print("4. Try again in a few moments")
            print("="*80)
            raise

        except Exception as e:
            print("="*80)
            print("❌ UNEXPECTED ERROR")
            print("="*80)
            print(f"Error: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            print("="*80)
            raise

        # Step 3: Parse result
        try:
            # Try to get resultJson from response
            result_json_str = result.get("data", {}).get("resultJson", "{}")

            if isinstance(result_json_str, str):
                result_json = json.loads(result_json_str)
            else:
                result_json = result_json_str

            result_urls = result_json.get("resultUrls", [])

            if not result_urls:
                # Try alternative response structure
                result_urls = result.get("data", {}).get("resultUrls", [])

            if not result_urls:
                raise Exception("No images generated")
        except Exception as e:
            print(f"⚠️  Error parsing result: {e}")
            print(f"Response structure: {json.dumps(result, indent=2)}")
            raise

        # Step 4: Download first image
        image_url = result_urls[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.{output_format}"
        save_path = config.IMAGES_DIR / filename

        downloaded_path = self.download_image(image_url, save_path)

        print("="*80)
        print("✅ Generation Complete!")
        print(f"   Task ID: {task_id}")
        print(f"   Local path: {downloaded_path}")
        print("="*80)

        return {
            'path': str(downloaded_path),
            'url': image_url,
            'prompt': prompt,
            'task_id': task_id,
            'all_urls': result_urls
        }


# Example usage
if __name__ == "__main__":
    generator = KieGenerator()

    # Note: You need to upload your reference image to a public URL first
    reference_urls = [
        "https://example.com/your-product-image.jpg"
    ]

    result = generator.generate_image(
        prompt="A modern lifestyle product photography scene: Thai outdoor cafe, tropical plants, natural sunlight, professional composition, vertical 9:16 format",
        reference_image_urls=reference_urls,
        filename_prefix="test_product",
        image_size="9:16"
    )

    print(f"Image saved to: {result['path']}")
