"""
Video Creator for AI Product Visualizer
Creates advertisement videos from product images
"""

from pathlib import Path
from datetime import datetime
from typing import List, Optional
from PIL import Image
import config

# Import moviepy lazily to avoid import errors if not installed
try:
    from moviepy.editor import ImageClip, concatenate_videoclips, VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    ImageClip = None
    concatenate_videoclips = None
    VideoFileClip = None


class VideoCreator:
    """Create videos from product images"""

    def __init__(
        self,
        fps: int = config.VIDEO_FPS,
        duration_per_image: int = config.VIDEO_DURATION_PER_IMAGE,
        video_size: tuple = config.VIDEO_SIZE
    ):
        """
        Initialize Video Creator

        Args:
            fps: Frames per second for the video
            duration_per_image: Duration to show each image (in seconds)
            video_size: Output video size (width, height) for 9:16 ratio
        """
        self.fps = fps
        self.duration_per_image = duration_per_image
        self.video_size = video_size  # (1080, 1920) for 9:16

    def create_video(
        self,
        image_paths: List[str],
        output_path: Optional[Path] = None,
        filename: str = None
    ) -> Path:
        """
        Create a video from a list of images

        Args:
            image_paths: List of paths to images
            output_path: Directory to save the video (default: config.VIDEOS_DIR)
            filename: Custom filename for the video (optional)

        Returns:
            Path to the created video file
        """
        if not MOVIEPY_AVAILABLE:
            raise ImportError("MoviePy is not available. Please install it with: pip install moviepy")

        if not image_paths:
            raise ValueError("No images provided for video creation")

        if output_path is None:
            output_path = config.VIDEOS_DIR

        # Create filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"product_ad_{timestamp}.mp4"

        # Ensure .mp4 extension
        if not filename.endswith('.mp4'):
            filename += '.mp4'

        video_path = output_path / filename

        # Process images and create clips
        clips = []
        for img_path in image_paths:
            # Resize image to fit video dimensions
            processed_img = self._process_image(img_path)

            # Create clip from image
            clip = ImageClip(processed_img).set_duration(self.duration_per_image)
            clips.append(clip)

        if not clips:
            raise ValueError("No valid clips created from images")

        # Concatenate all clips
        final_video = concatenate_videoclips(clips, method="compose")

        # Write video file
        print(f"📹 Creating video: {video_path.name}")
        final_video.write_videofile(
            str(video_path),
            fps=self.fps,
            codec='libx264',
            audio=False,
            preset='medium',
            verbose=False,
            logger=None
        )
        print(f"✅ Video created successfully!")

        # Close clips to free memory
        for clip in clips:
            clip.close()
        final_video.close()

        return video_path

    def _process_image(self, img_path: str) -> str:
        """
        Process image to fit video dimensions (9:16 aspect ratio)

        Args:
            img_path: Path to the image

        Returns:
            Path to the processed image (same path, modified in place for MoviePy)
        """
        # Open image
        img = Image.open(img_path)

        # Get target dimensions
        target_width, target_height = self.video_size

        # Calculate aspect ratios
        img_aspect = img.width / img.height
        target_aspect = target_width / target_height

        # Resize and crop to fit 9:16 aspect ratio
        if img_aspect > target_aspect:
            # Image is wider, crop width
            new_width = int(img.height * target_aspect)
            left = (img.width - new_width) // 2
            img = img.crop((left, 0, left + new_width, img.height))
        else:
            # Image is taller, crop height
            new_height = int(img.width / target_aspect)
            top = (img.height - new_height) // 2
            img = img.crop((0, top, img.width, top + new_height))

        # Resize to target dimensions
        img = img.resize(self.video_size, Image.Resampling.LANCZOS)

        # Save processed image (temp)
        temp_path = Path(img_path).parent / f"temp_{Path(img_path).name}"
        img.save(temp_path, quality=95)

        return str(temp_path)

    def add_transition_effect(self, clips: List, transition_type: str = "fade") -> List:
        """
        Add transitions between clips (optional enhancement)

        Args:
            clips: List of video clips
            transition_type: Type of transition ('fade', 'crossfade')

        Returns:
            List of clips with transitions
        """
        # This is a placeholder for future enhancement
        # Can add crossfade or other transition effects
        return clips

    def get_video_info(self, video_path: Path) -> dict:
        """
        Get information about a created video

        Args:
            video_path: Path to the video file

        Returns:
            Dictionary with video information
        """
        if not MOVIEPY_AVAILABLE:
            raise ImportError("MoviePy is not available. Please install it with: pip install moviepy")

        clip = VideoFileClip(str(video_path))
        info = {
            'duration': clip.duration,
            'fps': clip.fps,
            'size': clip.size,
            'filename': video_path.name,
            'path': str(video_path)
        }
        clip.close()

        return info


# Example usage
if __name__ == "__main__":
    # Example: Create a video from images in the images directory
    creator = VideoCreator()

    # Get all images from the images directory
    images_dir = config.IMAGES_DIR
    image_files = list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpg"))

    if not image_files:
        print("No images found in the images directory")
        print(f"Please add some images to: {images_dir}")
    else:
        print(f"Found {len(image_files)} images")
        print("Creating video...")

        try:
            # Convert Path objects to strings
            image_paths = [str(img) for img in image_files[:5]]  # Use first 5 images

            video_path = creator.create_video(
                image_paths=image_paths,
                filename="test_video.mp4"
            )

            print(f"Video created successfully: {video_path}")

            # Get video info
            info = creator.get_video_info(video_path)
            print(f"Video duration: {info['duration']} seconds")
            print(f"Video size: {info['size']}")

        except Exception as e:
            print(f"Error creating video: {e}")
