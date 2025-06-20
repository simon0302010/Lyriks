import click
import numpy as np
from moviepy import *
from pathlib import Path
from matplotlib import font_manager

class VideoGenerator:
    def __init__(self, clip_path=None):
        if clip_path is None:
            clip_path = Path(__file__).parent.parent / "templates" / "video.mp4"
            clip_path = clip_path.resolve()
        self.video = (VideoFileClip(str(clip_path)).subclipped(0, 20))
        self.video_height, self.video_width = self.video.h, self.video.w
        self.font_path = font_manager.findfont("DejaVu Sans")
        click.secho("Video Generator initialized", fg="green")
        
    def add_text(self, text, start: int, end: int):
        txt_clip = TextClip(
            font=self.font_path,
            text=text,
            font_size=80, 
            color="white",
            method="caption",
            size=(self.video_width, self.video_height)
        )
        txt_clip = txt_clip.with_position("center").with_start(start).with_end(end)
        self.video = CompositeVideoClip([self.video, txt_clip])
        
    def render_video(self, output):
        self.video.write_videofile(output)