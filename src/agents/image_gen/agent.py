import os
import requests
from typing import List, Dict
from src.models.models import Scene
from src.core.config import settings

class ImageGenAgent:
    def __init__(self):
        # Use centralized config
        self.mock_mode = not settings.USE_REAL_IMAGE
        self.output_dir = os.path.join(settings.GENERATED_ASSETS_DIR, "images")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # API configuration from settings
        self.api_key = settings.NANO_BANANA_API_KEY
        self.api_url = settings.NANO_BANANA_API_URL

    async def generate_images(self, scenes: List[Scene]) -> Dict[int, str]:
        """
        Generates images for a list of scenes.
        Returns a dictionary mapping scene_number to local_file_path.
        """
        image_paths = {}
        print(f"Generating images for {len(scenes)} scenes...")

        for scene in scenes:
            filename = f"scene_{scene.scene_number}.png"
            filepath = os.path.join(self.output_dir, filename)

            if self.mock_mode:
                # Mock image using placeholder service
                prompt_slug = (
                    scene.image_create_prompt[:20].replace(" ", "+")
                    if scene.image_create_prompt
                    else "scene"
                )
                image_url = (
                    f"https://placehold.co/1280x720/2563eb/ffffff/png?text=Scene+{scene.scene_number}:{prompt_slug}"
                )
                print(f"  [Mock] Downloading image for Scene {scene.scene_number}...")
                response = requests.get(image_url)
                if response.status_code == 200:
                    with open(filepath, "wb") as f:
                        f.write(response.content)
                    image_paths[scene.scene_number] = filepath
                else:
                    print(f"Failed to download mock image for scene {scene.scene_number}")
            else:
                # Real image generation via NanoBanana
                if not self.api_key:
                    raise RuntimeError("NANO_BANANA_API_KEY not set for real image generation")
                payload = {
                    "prompt": scene.image_create_prompt or "",
                    "width": 1280,
                    "height": 720,
                    "format": "png",
                }
                headers = {"Authorization": f"Bearer {self.api_key}"}
                try:
                    resp = requests.post(self.api_url, json=payload, headers=headers, timeout=30)
                    resp.raise_for_status()
                    data = resp.json()
                    # Expecting a field `image_base64` or `image_url`
                    if "image_base64" in data:
                        import base64
                        img_bytes = base64.b64decode(data["image_base64"])
                        with open(filepath, "wb") as f:
                            f.write(img_bytes)
                        image_paths[scene.scene_number] = filepath
                    elif "image_url" in data:
                        img_resp = requests.get(data["image_url"], timeout=30)
                        img_resp.raise_for_status()
                        with open(filepath, "wb") as f:
                            f.write(img_resp.content)
                        image_paths[scene.scene_number] = filepath
                    else:
                        raise RuntimeError("Unexpected NanoBanana response format")
                except Exception as e:
                    print(f"[Error] NanoBanana generation failed for scene {scene.scene_number}: {e}")
                    # Fallback to mock image so pipeline continues
                    prompt_slug = (
                        scene.image_create_prompt[:20].replace(" ", "+")
                        if scene.image_create_prompt
                        else "scene"
                    )
                    fallback_url = (
                        f"https://placehold.co/1280x720/ff4444/ffffff/png?text=FAIL+Scene+{scene.scene_number}"
                    )
                    resp = requests.get(fallback_url)
                    if resp.status_code == 200:
                        with open(filepath, "wb") as f:
                            f.write(resp.content)
                        image_paths[scene.scene_number] = filepath
        return image_paths
