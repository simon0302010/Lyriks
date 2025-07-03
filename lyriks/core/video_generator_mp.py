from pathlib import Path

import click
from matplotlib import font_manager
from moviepy import AudioFileClip, CompositeVideoClip, TextClip, VideoFileClip
from PIL import ImageFont


class VideoGenerator:
    def __init__(self, audio_path, clip_path=None, duration=None):
        self.audio = AudioFileClip(str(audio_path))
        self.audio_duration = round(self.audio.duration, 2)
        click.secho(f"Audio Duration: {self.audio_duration} seconds", fg="green")
        if clip_path is None:
            clip_path = Path(__file__).parent.parent / "templates" / "video.mp4"
            clip_path = clip_path.resolve()
        if duration is not None:
            self.clip = VideoFileClip(str(clip_path)).subclipped(0, int(duration))
            self.audio = self.audio.subclipped(0, int(duration))
        else:
            self.clip = VideoFileClip(str(clip_path)).subclipped(0, self.audio_duration)
            self.audio = self.audio.subclipped(0, self.audio_duration)
        self.video_width = self.clip.w
        self.video_height = self.clip.h
        self.font_path = font_manager.findfont("DejaVu Sans")
        self.text_clips = []
        click.secho("Video Generator initialized", fg="green")

    def add_text(self, text, start: int, end: int, font_size: int = 80):
        txt_clip = TextClip(
            font=self.font_path,
            text=text,
            font_size=font_size,
            color="white",
            method="caption",
            size=(self.video_width, self.video_height),
        )
        txt_clip = txt_clip.with_position("center").with_start(start).with_end(end)
        self.text_clips.append(txt_clip)

        font = ImageFont.truetype(self.font_path, font_size)
        words = text.split(" ")
        x = 0
        coords = []
        for word in words:
            word_width = font.getlength(word)
            coords.append({"word": word, "start_x": x, "end_x": x + word_width})
            x += word_width + font.getlength(" ")
        return coords

    def place_markers(self, coords, start, end, font_size: int = 80):
        total_text_width = coords[-1]["end_x"] if coords else 0

        x_offset = (self.video_width - total_text_width) // 2
        y_position = self.video_height // 2
        for c in coords:
            marker_clip = TextClip(
                text="|", font=self.font_path, font_size=font_size, color="red"
            )
            marker_clip = marker_clip.with_position(
                (x_offset + c["start_x"] - 10, (y_position - marker_clip.h // 2 + 5))
            )
            click.secho(
                f"Placed marker at {x_offset + c['start_x'] - 10},{y_position - marker_clip.h // 2 + 5}"
            )
            marker_clip = marker_clip.with_start(start).with_end(end)
            self.text_clips.append(marker_clip)

    def render_video(self, output_file_name):
        self.video = CompositeVideoClip([self.clip] + self.text_clips)
        self.video = self.video.with_audio(self.audio)
        output = output_file_name + ".mp4"
        self.video.write_videofile(
            output,
            temp_audiofile="temp-audio.mp3",
            remove_temp=True,
            codec="libx264",
            audio_codec="libmp3lame",
        )
