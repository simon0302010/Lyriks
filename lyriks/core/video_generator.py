import click
import numpy as np
from moviepy import *
from pathlib import Path

class VideoGenerator:
    def __init__(self, clip_path=None):
        if clip_path is None:
            clip_path = Path(__file__).parent.parent / "templates" / "video.mp4"
            clip_path = clip_path.resolve()
        self.video = (VideoFileClip(str(clip_path)).subclipped(0, 20))
        click.secho("Video Generator initialized", fg="green")
        
    def add_text(self, text):
        txt_clip = TextClip(text=text, font_size=70, color="white")
        txt_clip = txt_clip.with_position("center").with_duration(10)
        self.video = CompositeVideoClip([self.video, txt_clip])
        
    def render_video(self, output):
        self.video.write_videofile(output)