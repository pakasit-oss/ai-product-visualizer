"""
Veo3 Video Creator for AI Product Visualizer
Creates videos using Google Veo3 via Kie.ai API
"""

import requests
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
import config


class Veo3VideoCreator:
    """Generate videos using Veo3 via Kie.ai API"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Veo3 Video Creator

        Args:
            api_key: Kie.ai API key (optional, will use config if not provided)
        """
        self.api_key = api_key or config.KIE_API_KEY
        self.base_url = "https://api.kie.ai/api/v1"
        self.model = "veo3"

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

    def get_webhook_requests(self, webhook_id: str, retry_count: int = 3) -> list:
        """
        Get all requests received by the webhook with retry logic

        Args:
            webhook_id: Webhook UUID
            retry_count: Number of retries on failure

        Returns:
            List of requests
        """
        url = f"https://webhook.site/token/{webhook_id}/requests"

        for attempt in range(retry_count):
            try:
                # Use shorter timeout to fail fast and retry
                response = requests.get(url, timeout=10)
                response.raise_for_status()

                data = response.json()
                return data.get('data', [])
            except Exception as e:
                if attempt < retry_count - 1:
                    print(f"⚠️  Webhook request failed (attempt {attempt + 1}/{retry_count}), retrying...")
                    time.sleep(1)  # Short delay before retry
                else:
                    print(f"❌ Failed to get webhook requests after {retry_count} attempts: {e}")
                    return []

        return []

    def generate_video(
        self,
        prompt: str,
        image_urls: Optional[List[str]] = None,
        aspect_ratio: str = "9:16",
        watermark: Optional[str] = None,
        seeds: Optional[int] = None,
        enable_fallback: bool = False,
        enable_translation: bool = False,
        callback_url: Optional[str] = None
    ) -> tuple:
        """
        Generate video with Veo3

        Args:
            prompt: Video generation prompt
            image_urls: List of reference image URLs (optional)
            aspect_ratio: Video aspect ratio (9:16, 16:9, 1:1)
            watermark: Optional watermark text
            seeds: Random seed for reproducibility
            enable_fallback: Enable fallback to alternative models
            enable_translation: Auto-translate non-English prompts (default: False for faster processing)
            callback_url: Optional callback URL (webhook)

        Returns:
            Tuple of (task_id, webhook_id)
        """
        url = f"{self.base_url}/veo/generate"

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
            "prompt": prompt,
            "aspectRatio": aspect_ratio,
            "enableFallback": enable_fallback,
            "enableTranslation": enable_translation
        }

        # Add optional parameters
        if image_urls:
            payload["imageUrls"] = image_urls

        if watermark:
            payload["watermark"] = watermark

        if seeds is not None:
            payload["seeds"] = seeds

        # Add callback URL if available
        if callback_url:
            payload["callBackUrl"] = callback_url
            print(f"📞 Callback URL: {callback_url}")

        print(f"🎬 Creating Veo3 video task...")
        print(f"   Model: {self.model}")
        print(f"   Aspect ratio: {aspect_ratio}")
        if image_urls:
            print(f"   Reference images: {len(image_urls)}")

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()

            if result.get("code") == 200:
                task_id = result["data"]["taskId"]
                print(f"✅ Veo3 task created: {task_id}")
                return task_id, webhook_id
            else:
                raise Exception(f"API Error: {result.get('msg', 'Unknown error')}")

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
            f"{self.base_url}/veo/query?taskId={task_id}",
        ]

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        last_error = None

        # Try GET requests (with longer timeout but silently)
        for url in possible_endpoints:
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()

                result = response.json()
                print(f"✅ Query success with: {url}")
                return result

            except requests.exceptions.RequestException:
                # Silently continue to next endpoint
                continue

        # Try POST requests with taskId in body
        post_endpoints = [
            f"{self.base_url}/jobs/query",
            f"{self.base_url}/playground/query",
        ]

        for url in post_endpoints:
            try:
                payload = {"taskId": task_id}
                response = requests.post(url, headers=headers, json=payload, timeout=10)
                response.raise_for_status()

                result = response.json()
                print(f"✅ Query success with: {url}")
                return result

            except requests.exceptions.RequestException:
                # Silently continue
                continue

        # If all endpoints failed - return None (webhook will handle it)
        return None

    def wait_for_video(
        self,
        task_id: str,
        webhook_id: Optional[str] = None,
        max_wait_time: int = 1800,  # 30 minutes timeout - Veo3 can be very slow
        poll_interval: int = 10,
        progress_callback = None
    ) -> Dict:
        """
        Wait for video generation to complete using webhook callback

        Args:
            task_id: Task ID
            webhook_id: Webhook UUID (if using webhook.site)
            max_wait_time: Maximum time to wait (seconds, default 30 min)
            poll_interval: Time between status checks (seconds)

        Returns:
            Final task result with video URL
        """
        start_time = time.time()
        consecutive_webhook_failures = 0
        max_consecutive_failures = 2  # Switch to query after 2 failures (faster)
        last_direct_query_time = 0

        print(f"⏳ Waiting for Veo3 video generation (this may take several minutes)...")

        if webhook_id:
            print(f"📞 Polling webhook for callback...")

        while True:
            elapsed = time.time() - start_time

            if elapsed > max_wait_time:
                minutes_elapsed = int(elapsed // 60)
                error_msg = (
                    f"⏰ Veo3 timeout after {minutes_elapsed} minutes.\n"
                    f"💡 Veo3 via Kie.ai can be slow and unreliable.\n"
                    f"💡 Recommendations:\n"
                    f"   1. Try using Sora 2 instead (faster and more reliable)\n"
                    f"   2. Sora 2 doesn't support images with photorealistic people\n"
                    f"   3. For product-only images, Sora 2 is recommended\n"
                    f"Task ID: {task_id}"
                )
                raise TimeoutError(error_msg)

            # Try webhook first if available
            webhook_success = False
            if webhook_id and consecutive_webhook_failures < max_consecutive_failures:
                requests_list = self.get_webhook_requests(webhook_id)

                if requests_list is not None and len(requests_list) >= 0:
                    webhook_success = True
                    consecutive_webhook_failures = 0  # Reset counter on success

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
                                    print(f"❌ Task failed: {fail_msg}")
                                    raise Exception(f"Video generation failed: {fail_msg}")
                        except json.JSONDecodeError as e:
                            # JSON parsing error - skip this webhook
                            print(f"⚠️  Error parsing webhook JSON: {e}")
                            continue
                        except Exception as e:
                            print(f"⚠️  Error processing webhook: {e}")
                            continue
                else:
                    # Webhook request failed
                    consecutive_webhook_failures += 1
                    print(f"⚠️  Webhook check failed ({consecutive_webhook_failures}/{max_consecutive_failures})")

            # Only try direct query if webhook completely fails
            # Don't query if webhook is working (to avoid spam and delays)
            should_query_direct = (
                consecutive_webhook_failures >= max_consecutive_failures and
                (elapsed - last_direct_query_time) >= 120  # Only every 2 minutes if webhook fails
            )

            if should_query_direct:
                print(f"🔄 Webhook failed, trying direct query...")
                last_direct_query_time = elapsed

                result = self.query_task(task_id)
                if result and result.get('code') == 200:
                    data = result.get('data', {})
                    state = data.get('state')

                    if state == 'success':
                        print(f"✅ Video generation completed successfully (via direct query)!")
                        return result
                    elif state == 'fail':
                        fail_msg = data.get('failMsg', 'Unknown error')
                        print(f"❌ Task failed: {fail_msg}")
                        raise Exception(f"Video generation failed: {fail_msg}")

            if not webhook_id:
                # If no webhook, we can't get status - this is a problem
                print(f"⚠️  No webhook available and query endpoints don't work")
                print(f"   Consider using Sora 2 instead for better support")

            # Format time nicely
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            if minutes > 0:
                time_str = f"{minutes} นาที {seconds} วินาที"
            else:
                time_str = f"{seconds} วินาที"

            # Estimate time remaining (Veo3 usually takes 3-5 minutes with optimized images)
            estimated_total = 300  # 5 minutes average
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

            status_method = "webhook" if consecutive_webhook_failures < max_consecutive_failures else "direct query"

            # Call progress callback if provided
            if progress_callback:
                progress_callback(elapsed, remaining_str, status_method)

            print(f"   ⏰ รอผลลัพธ์ (via {status_method})... {time_str} {remaining_str}")
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

    def create_video_from_images(
        self,
        image_urls: List[str],
        prompt: str,
        filename: str = None,
        aspect_ratio: str = "9:16",
        watermark: Optional[str] = None,
        progress_callback = None
    ) -> Dict[str, str]:
        """
        Complete workflow: Generate video from images

        Args:
            image_urls: List of image URLs to animate
            prompt: Video generation prompt
            filename: Output filename (optional)
            aspect_ratio: Video aspect ratio
            watermark: Optional watermark

        Returns:
            Dict with 'path', 'url', 'task_id'
        """
        print("="*80)
        print("🎬 Veo3 Video Generation")
        print("="*80)
        print(f"Prompt: {prompt[:100]}...")
        if image_urls:
            print(f"Input images: {len(image_urls)}")
        print(f"Aspect ratio: {aspect_ratio}")
        print("="*80)

        # Step 1: Create video generation task
        task_id, webhook_id = self.generate_video(
            prompt=prompt,
            image_urls=image_urls,
            aspect_ratio=aspect_ratio,
            watermark=watermark
        )

        # Step 2: Wait for completion
        result = self.wait_for_video(task_id, webhook_id=webhook_id, progress_callback=progress_callback)

        # Step 3: Get video URL
        video_url = result["data"].get("videoUrl")
        if not video_url:
            # Try alternative response structure
            result_json = result["data"].get("resultJson")
            if result_json:
                if isinstance(result_json, str):
                    result_json = json.loads(result_json)
                video_url = result_json.get("videoUrl")

        if not video_url:
            raise Exception("No video URL in response")

        # Step 4: Download video
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"veo3_{timestamp}.mp4"

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
        print("✅ Video Generation Complete!")
        print(f"   Task ID: {task_id}")
        print(f"   Local path: {downloaded_path}")
        print("="*80)

        return {
            'path': str(downloaded_path),
            'url': video_url,
            'task_id': task_id,
            'prompt': prompt
        }

    def create_video_from_text(
        self,
        prompt: str,
        filename: str = None,
        aspect_ratio: str = "9:16",
        watermark: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate video from text prompt only (no reference images)

        Args:
            prompt: Video generation prompt
            filename: Output filename (optional)
            aspect_ratio: Video aspect ratio
            watermark: Optional watermark

        Returns:
            Dict with 'path', 'url', 'task_id'
        """
        return self.create_video_from_images(
            image_urls=None,
            prompt=prompt,
            filename=filename,
            aspect_ratio=aspect_ratio,
            watermark=watermark
        )


# Example usage
if __name__ == "__main__":
    creator = Veo3VideoCreator()

    # Example 1: Video from images
    image_urls = [
        "https://example.com/product1.jpg",
        "https://example.com/product2.jpg"
    ]

    result = creator.create_video_from_images(
        image_urls=image_urls,
        prompt="Smooth transitions between product showcase images in a modern Thai cafe setting, professional commercial style",
        aspect_ratio="9:16",
        filename="product_showcase.mp4"
    )

    print(f"Video saved to: {result['path']}")

    # Example 2: Video from text only
    result2 = creator.create_video_from_text(
        prompt="A stylish product showcase in a modern Thai cafe, natural lighting, professional photography style",
        aspect_ratio="9:16",
        filename="generated_scene.mp4"
    )

    print(f"Video saved to: {result2['path']}")
