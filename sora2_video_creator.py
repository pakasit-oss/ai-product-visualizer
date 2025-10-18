"""
Sora 2 Video Creator for AI Product Visualizer
Creates videos using OpenAI Sora 2 via Kie.ai API
"""

import requests
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
import config


class Sora2VideoCreator:
    """Generate videos using Sora 2 (image-to-video) via Kie.ai API"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Sora 2 Video Creator

        Args:
            api_key: Kie.ai API key (optional, will use config if not provided)
        """
        self.api_key = api_key or config.KIE_API_KEY
        self.base_url = "https://api.kie.ai/api/v1"
        self.model = "sora-2-image-to-video"

        if not self.api_key:
            print("⚠️  Warning: KIE_API_KEY not found")

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

    def generate_video(
        self,
        prompt: str,
        image_url: str,
        aspect_ratio: str = "portrait",
        remove_watermark: bool = True,
        callback_url: Optional[str] = None
    ) -> str:
        """
        Generate video with Sora 2

        Args:
            prompt: Video generation prompt describing the motion
            image_url: URL of the image to use as first frame (must be publicly accessible)
            aspect_ratio: Video aspect ratio ("portrait" or "landscape")
            remove_watermark: Whether to remove watermark from generated video
            callback_url: Optional callback URL (webhook)

        Returns:
            Task ID
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
                "image_urls": [image_url],
                "aspect_ratio": aspect_ratio,
                "remove_watermark": remove_watermark
            }
        }

        # Add callback URL if available
        if callback_url:
            payload["callBackUrl"] = callback_url
            print(f"📞 Callback URL: {callback_url}")

        print(f"🎬 Creating Sora 2 video task...")
        print(f"   Model: {self.model}")
        print(f"   Aspect ratio: {aspect_ratio}")
        print(f"   Image URL: {image_url}")

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()

            if result.get("code") == 200:
                task_id = result["data"]["taskId"]
                print(f"✅ Sora 2 task created: {task_id}")
                return task_id, webhook_id
            else:
                raise Exception(f"API Error: {result.get('message', 'Unknown error')}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            raise

    def query_task(self, task_id: str) -> Dict:
        """
        Query video generation task status

        Args:
            task_id: Task ID from generate_video

        Returns:
            Task status and results
        """
        # Try multiple possible endpoints
        possible_endpoints = [
            f"{self.base_url}/jobs/query?taskId={task_id}",
            f"{self.base_url}/playground/query?taskId={task_id}",
        ]

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        last_error = None

        # Try GET requests
        for url in possible_endpoints:
            try:
                print(f"🔍 Trying GET: {url}")
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()

                result = response.json()
                print(f"✅ Success with endpoint: {url}")
                return result

            except requests.exceptions.RequestException as e:
                last_error = e
                print(f"❌ Failed: {e}")
                continue

        # Try POST requests with taskId in body
        post_endpoints = [
            f"{self.base_url}/jobs/query",
            f"{self.base_url}/playground/query",
        ]

        for url in post_endpoints:
            try:
                print(f"🔍 Trying POST: {url}")
                payload = {"taskId": task_id}
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                response.raise_for_status()

                result = response.json()
                print(f"✅ Success with endpoint: {url}")
                return result

            except requests.exceptions.RequestException as e:
                last_error = e
                print(f"❌ Failed: {e}")
                continue

        # If all endpoints failed
        print(f"❌ All query endpoints failed")
        print(f"💡 Tip: Kie.ai might require using callback URL instead of polling")
        raise last_error if last_error else Exception("Query failed with all endpoints")

    def wait_for_video(
        self,
        task_id: str,
        webhook_id: Optional[str] = None,
        max_wait_time: int = 300,  # 5 minutes timeout - skip if too slow
        poll_interval: int = 10,
        progress_callback = None
    ) -> Dict:
        """
        Wait for video generation to complete using webhook callback

        Args:
            task_id: Task ID
            webhook_id: Webhook UUID (if using webhook.site)
            max_wait_time: Maximum time to wait (seconds, default 10 min)
            poll_interval: Time between status checks (seconds)

        Returns:
            Final task result with video URL
        """
        start_time = time.time()

        print(f"⏳ Waiting for Sora 2 video generation (this may take several minutes)...")

        if webhook_id:
            print(f"📞 Polling webhook for callback...")

        while True:
            elapsed = time.time() - start_time

            if elapsed > max_wait_time:
                raise TimeoutError(f"Task {task_id} timed out after {max_wait_time}s")

            # Try webhook first if available
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
                                print(f"✅ Video generation completed successfully (via webhook)!")
                                return callback_data
                            elif state == 'fail':
                                fail_msg = callback_data.get('data', {}).get('failMsg', 'Unknown error')

                                # Check for specific error about photorealistic people
                                if 'photorealistic people' in fail_msg.lower():
                                    print(f"❌ Sora 2 Error: Image contains photorealistic people")
                                    print(f"💡 Sora 2 does not support images with realistic-looking people")
                                    print(f"💡 Solutions:")
                                    print(f"   1. Use Veo3 instead (supports images with people)")
                                    print(f"   2. Use product-only images (no people)")
                                    print(f"   3. Use MoviePy for quick slideshow")
                                    raise Exception(
                                        f"Sora 2 Error: Image contains photorealistic people. "
                                        f"Try using Veo3 instead, or use images without people."
                                    )
                                else:
                                    print(f"❌ Task failed: {fail_msg}")
                                    raise Exception(f"Task failed: {fail_msg}")
                    except json.JSONDecodeError as e:
                        # JSON parsing error - skip this webhook
                        print(f"⚠️  Error parsing webhook JSON: {e}")
                        continue
                    except Exception as e:
                        # If it's our custom exception about photorealistic people, re-raise it
                        if 'photorealistic people' in str(e).lower():
                            raise
                        # Otherwise just print and continue
                        print(f"⚠️  Error processing webhook: {e}")
                        continue

            # Fallback: Try direct query
            try:
                result = self.query_task(task_id)

                if result.get("code") == 200:
                    state = result["data"].get("state")

                    if state == "success":
                        print(f"✅ Video generation completed!")
                        return result
                    elif state == "fail":
                        fail_msg = result["data"].get("failMsg", "Unknown error")
                        raise Exception(f"Task failed: {fail_msg}")
            except Exception as e:
                # Query failed, continue waiting for webhook
                pass

            # Format time nicely
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            if minutes > 0:
                time_str = f"{minutes} นาที {seconds} วินาที"
            else:
                time_str = f"{seconds} วินาที"

            # Estimate time remaining (Sora 2 usually takes 2-3 minutes)
            estimated_total = 180  # 3 minutes
            remaining = max(0, estimated_total - elapsed)
            remaining_min = int(remaining // 60)
            remaining_sec = int(remaining % 60)

            if remaining > 0:
                if remaining_min > 0:
                    remaining_str = f"(เหลืออีกประมาณ {remaining_min} นาที {remaining_sec} วินาที)"
                else:
                    remaining_str = f"(เหลืออีกประมาณ {remaining_sec} วินาที)"
            else:
                remaining_str = "(กำลังจะเสร็จแล้ว...)"

            # Call progress callback if provided
            if progress_callback:
                progress_callback(elapsed, remaining_str, "webhook")

            print(f"   ⏰ รอวิดีโอ... {time_str} {remaining_str}")
            time.sleep(poll_interval)

    def download_video(self, video_url: str, save_path: Path, max_retries: int = 3) -> Path:
        """
        Download generated video with retry logic

        Args:
            video_url: URL of generated video
            save_path: Path to save video
            max_retries: Maximum number of retry attempts

        Returns:
            Path to saved video
        """
        print(f"📥 Downloading video from {video_url}")

        # Ensure directory exists
        save_path.parent.mkdir(parents=True, exist_ok=True)

        last_error = None
        for attempt in range(max_retries):
            try:
                print(f"   Attempt {attempt + 1}/{max_retries}...")

                response = requests.get(video_url, timeout=300, stream=True)
                response.raise_for_status()

                # Save video with progress
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0

                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                progress = (downloaded / total_size) * 100
                                print(f"   Download progress: {progress:.1f}%", end='\r')

                # Verify file was actually saved
                if save_path.exists() and save_path.stat().st_size > 0:
                    print(f"\n✅ Video saved to: {save_path} ({save_path.stat().st_size / (1024*1024):.2f} MB)")
                    return save_path
                else:
                    raise Exception(f"File was not saved properly: {save_path}")

            except requests.exceptions.Timeout as e:
                last_error = e
                print(f"\n⚠️  Download timeout on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 10  # Progressive backoff: 10s, 20s, 30s
                    print(f"   Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                continue

            except requests.exceptions.RequestException as e:
                last_error = e
                print(f"\n❌ Download failed on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    print(f"   Retrying in 10 seconds...")
                    time.sleep(10)
                continue

        # All retries failed
        print(f"\n❌ Download failed after {max_retries} attempts")
        raise last_error if last_error else Exception("Download failed")

    def create_video_from_image(
        self,
        image_url: str,
        prompt: str,
        filename: str = None,
        aspect_ratio: str = "portrait",
        remove_watermark: bool = True,
        progress_callback = None
    ) -> Dict[str, str]:
        """
        Complete workflow: Generate video from image using Sora 2

        Args:
            image_url: URL of image to animate (must be publicly accessible)
            prompt: Video generation prompt describing motion
            filename: Output filename (optional)
            aspect_ratio: Video aspect ratio ("portrait" or "landscape")
            remove_watermark: Whether to remove watermark
            progress_callback: Optional callback for progress updates

        Returns:
            Dict with 'path', 'url', 'task_id'
        """
        print("="*80)
        print("🎬 Sora 2 Video Generation")
        print("="*80)
        print(f"Prompt: {prompt[:100]}...")
        print(f"Image URL: {image_url}")
        print(f"Aspect ratio: {aspect_ratio}")
        print("="*80)

        # Step 1: Create video generation task
        task_id, webhook_id = self.generate_video(
            prompt=prompt,
            image_url=image_url,
            aspect_ratio=aspect_ratio,
            remove_watermark=remove_watermark
        )

        # Step 2: Wait for completion with progress callback
        result = self.wait_for_video(task_id, webhook_id=webhook_id, progress_callback=progress_callback)

        # Step 3: Get video URL from result
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
                raise Exception("No video URL in response")

            video_url = result_urls[0]
        except Exception as e:
            print(f"⚠️  Error parsing result: {e}")
            print(f"Response structure: {json.dumps(result, indent=2)}")
            raise

        # Step 4: Download video
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sora2_{timestamp}.mp4"

        save_path = config.VIDEOS_DIR / filename

        # Debug: Print actual save path
        print(f"📂 VIDEOS_DIR: {config.VIDEOS_DIR}")
        print(f"📂 Absolute save path: {save_path.absolute()}")
        print(f"📂 Directory exists: {save_path.parent.exists()}")

        downloaded_path = self.download_video(video_url, save_path)

        # Verify file exists after download
        if not downloaded_path.exists():
            raise Exception(f"❌ CRITICAL: File not found after download! Path: {downloaded_path.absolute()}")

        file_size_mb = downloaded_path.stat().st_size / (1024 * 1024)
        print(f"✅ VERIFIED: File exists at {downloaded_path.absolute()} ({file_size_mb:.2f} MB)")

        print("="*80)
        print("✅ Sora 2 Video Generation Complete!")
        print(f"   Task ID: {task_id}")
        print(f"   Local path: {downloaded_path}")
        print("="*80)

        return {
            'path': str(downloaded_path),
            'url': video_url,
            'task_id': task_id,
            'prompt': prompt
        }


# Example usage
if __name__ == "__main__":
    creator = Sora2VideoCreator()

    # Example: Video from image
    image_url = "https://example.com/product-image.jpg"

    result = creator.create_video_from_image(
        image_url=image_url,
        prompt="A woman is standing in a natural pose, wearing stylish shoes. She gently lifts one foot with toes touching the ground, pointing slightly down to highlight the footwear. After a brief pause, she slowly starts walking forward in a relaxed, smooth motion. The camera stays low and focused only on her legs and shoes — no face shown.",
        aspect_ratio="portrait",
        remove_watermark=True,
        filename="sora2_product_showcase.mp4"
    )

    print(f"Video saved to: {result['path']}")
