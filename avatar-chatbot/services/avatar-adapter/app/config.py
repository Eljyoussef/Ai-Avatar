import os
from dataclasses import dataclass

@dataclass
class AvatarConfig:
    duix_api_url: str = os.getenv("DUIX_API_URL", "http://localhost:8080")
    render_mode: str = "realtime"  # realtime or hd
    cache_avatars: bool = True
    max_cache_size: int = 5
    video_fps: int = 30
    video_width: int = 512
    video_height: int = 512
    lip_sync_enabled: bool = True