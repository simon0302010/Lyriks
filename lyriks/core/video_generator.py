import click
import numpy as np
from moviepy import *
from pathlib import Path
from matplotlib import font_manager

class VideoGenerator:
    def __init__(self, audio_path, clip_path=None):
        self.audio = AudioFileClip(str(audio_path))
        self.audio_duration = self.audio.duration
        self.audio = self.audio.subclipped(0, 20)
        if clip_path is None:
            clip_path = Path(__file__).parent.parent / "templates" / "video.mp4"
            clip_path = clip_path.resolve()
        self.clip = (VideoFileClip(str(clip_path)).subclipped(0, 20))
        self.video_width = self.clip.w
        self.video_height = self.clip.h
        self.font_path = font_manager.findfont("DejaVu Sans")
        self.text_clips = []
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
        self.text_clips.append(txt_clip)
        
    def render_video(self, output):
        self.video = CompositeVideoClip([self.clip] + self.text_clips)
        self.video = self.video.with_audio(self.audio)
        self.video.write_videofile(
            output,
            temp_audiofile="temp-audio.mp3",
            remove_temp=True,
            codec="libx264",
            audio_codec="libmp3lame"
        )