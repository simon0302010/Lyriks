import click
import numpy as np
from moviepy import *
from pathlib import Path

class VideoGenerator:
    def __init__(self, clip):
        clip_path = Path(__file__).parent.parent / "templates" / "video.mp4"
        clip_path = clip_path.resolve()
        self.clip = VideoFileClip(clip_path).subclipped(10, 20)
        click.secho("Video Generator initialized", fg="green")