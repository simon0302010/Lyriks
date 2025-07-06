import os
import subprocess

import click
import pysubs2

from . import ffmpeg


class VideoGenerator:
    def __init__(
        self,
        fontname="Comic Sans MS",
        fontsize=28,
        text_color=(255, 255, 255, 0),
        highlightcolor=(0, 255, 0, 0),
        outlinecolor=(0, 0, 0, 0),
        outline=2,
        shadow=0,
        alignment=pysubs2.Alignment.MIDDLE_CENTER,
    ):
        self.subs = pysubs2.SSAFile()
        self.text_color = text_color
        self.highlightcolor = highlightcolor
        self.subs.styles["Default"] = pysubs2.SSAStyle(
            fontname=fontname,
            fontsize=fontsize,
            primarycolor=pysubs2.Color(*self.highlightcolor),
            secondarycolor=pysubs2.Color(*self.text_color),
            outlinecolor=pysubs2.Color(*outlinecolor),
            outline=outline,
            shadow=shadow,
            alignment=alignment,
        )
        self.filename = None

    def add_words(self, segment, style="Default"):
        words = segment["words"]
        if not words:
            return

        if isinstance(words[0], tuple):
            words = [{"start": w[0], "end": w[1], "word": w[2]} for w in words]
        elif isinstance(words[0], list):
            words = [{"start": w[0], "end": w[1], "word": w[2]} for w in words]

        # full_text = " ".join([w["word"] for w in words])

        # karaoke highlighting
        ass_text = ""
        for i, w in enumerate(words):
            duration_cs = int((w["end"] - w["start"]) * 100)
            ass_text += f"{{\K{duration_cs}}}" + w["word"]
            if i < len(words) - 1:
                ass_text += " "

        fade_ms = 100
        ass_text = r"{\fad(" + str(fade_ms) + "," + str(fade_ms) + ")}" + ass_text

        self.subs.append(
            pysubs2.SSAEvent(
                start=int(segment["start"] * 1000),
                end=int(segment["end"] * 1000),
                text=ass_text,
                style=style,
            )
        )

    def save(self, folder):
        self.filename = str(folder / "lyrics.ass")
        self.subs.save(self.filename)
        return self.filename

    def render_video(
        self,
        output_file_name,
        audio_file=None,
        size="1920x1080",
        fps=60,
        duration=60,
        background_path=None,
    ):
        if not self.filename:
            click.secho("Please save subtitles first.", fg="red")
            return False

        temp_video = output_file_name + "_temp.mp4"

        try:
            if audio_file:
                cmd = [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    str(audio_file),
                ]
                try:
                    result = subprocess.run(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=True,
                    )
                    duration = round(float(result.stdout.strip()), 1)
                except subprocess.CalledProcessError as e:
                    click.secho(
                        f"Error getting audio duration with ffprobe:\n{e.stderr}",
                        fg="red",
                    )
                    return False
                except (ValueError, IndexError) as e:
                    click.secho(f"Error parsing audio duration: {e}", fg="red")
                    return False

            fade_filter = f"fade=t=in:st=0:d=1,fade=t=out:st={duration-1}:d=1"

            if background_path:
                bg_cmd = [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    str(background_path),
                ]
                try:
                    bg_result = subprocess.run(
                        bg_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=True,
                    )
                    bg_duration = float(bg_result.stdout.strip())
                except subprocess.CalledProcessError as e:
                    click.secho(
                        f"Error getting background video duration:\n{e.stderr}",
                        fg="red",
                    )
                    return False
                except (ValueError, IndexError) as e:
                    click.secho(
                        f"Error parsing background video duration: {e}", fg="red"
                    )
                    return False

                if bg_duration < duration:
                    click.secho(
                        "Error: Background video must be at least as long as the audio.",
                        fg="red",
                    )
                    return False

                ffmpeg_cmd = [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(background_path),
                    "-t",
                    str(duration),  # cut background to audio length
                    "-vf",
                    f"{fade_filter},ass={self.filename}",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-r",
                    str(fps),
                    temp_video,
                ]
            else:
                ffmpeg_cmd = [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    f"color=c=black:s={size}:d={duration}:r={fps}",
                    "-vf",
                    f"{fade_filter},ass={self.filename}",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    temp_video,
                ]

            click.secho("Rendering video...", fg="blue")
            ffmpeg.ffmpeg_progress(ffmpeg_cmd, duration)

            # mix audio and video
            if audio_file:
                final_output = output_file_name + ".mp4"
                ffmpeg_mux_cmd = [
                    "ffmpeg",
                    "-y",
                    "-i",
                    temp_video,
                    "-i",
                    str(audio_file),
                    "-c:v",
                    "copy",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "192k",
                    "-shortest",
                    final_output,
                ]
                click.secho("Adding audio to video...", fg="blue")
                ffmpeg.ffmpeg_progress(ffmpeg_mux_cmd, duration)
            else:
                os.rename(temp_video, output_file_name + ".mp4")

            return True

        except subprocess.CalledProcessError as e:
            click.secho(
                f"ffmpeg command failed with exit code {e.returncode}", fg="red"
            )
            click.secho(f"Stderr:\n{e.stderr}", fg="yellow")
            return False
        except Exception as e:
            click.secho(
                f"An unexpected error occurred during video rendering: {e}", fg="red"
            )
            return False
        finally:
            if os.path.exists(temp_video):
                os.remove(temp_video)
