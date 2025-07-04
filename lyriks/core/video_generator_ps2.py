import pysubs2
import subprocess
import json

class VideoGenerator:
    def __init__(
        self,
        fontname="Comic Sans",
        fontsize=28,
        primarycolor=(255, 255, 255, 0),
        highlightcolor=(0, 255, 0, 0),
        outlinecolor=(0, 0, 0, 0),
        outline=2,
        shadow=0,
        alignment=pysubs2.Alignment.MIDDLE_CENTER,
    ):
        self.subs = pysubs2.SSAFile()
        self.primarycolor = primarycolor
        self.highlightcolor = highlightcolor
        self.subs.styles["Default"] = pysubs2.SSAStyle(
            fontname=fontname,
            fontsize=fontsize,
            primarycolor=pysubs2.Color(*primarycolor),
            outlinecolor=pysubs2.Color(*outlinecolor),
            outline=outline,
            shadow=shadow,
            alignment=alignment,
        )
        self.filename = None
        
    def add_words(self, segment, style="Default"):
        words = segment["words"]
        if words and isinstance(words[0], list):
            words = [{"start": w[0], "end": w[1], "word": w[2]} for w in words]
        full_text = " ".join([w["word"] for w in words])

        # add white text
        def add_white(start, end):
            self.subs.append(
                pysubs2.SSAEvent(
                    start=int(start * 1000),
                    end=int(end * 1000),
                    text=r"{\c&HFFFFFF&}" + full_text,
                    style=style
                )
            )

        # add white before first word
        segment_start = words[0]["start"]
        segment_end = words[-1]["end"]
        if segment_start > segment["start"]:
            add_white(segment["start"], segment_start)

        # add white after last word
        for i, w in enumerate(words):
            text = ""
            for j, w2 in enumerate(words):
                if i == j:
                    text += r"{\c&H00FF00&}" + w2["word"]
                else:
                    text += r"{\c&HFFFFFF&}" + w2["word"]
                if j != len(words) - 1:
                    text += " "
            self.subs.append(
                pysubs2.SSAEvent(
                    start=int(w["start"] * 1000),
                    end=int(w["end"] * 1000),
                    text=text,
                    style=style
                )
            )
            if i < len(words) - 1:
                gap_start = w["end"]
                gap_end = words[i + 1]["start"]
                if gap_end > gap_start:
                    add_white(gap_start, gap_end)
        if segment_end < segment["end"]:
            add_white(segment_end, segment["end"])
            
    def save(self, folder):
        self.filename = str(folder / "lyrics.ass")
        self.subs.save(self.filename)
        return self.filename
    
    def render_video(self, output_file_name, audio_file=None, size="1920x1080", fps=30):
        if not hasattr(self, "filename"):
            print("Please save subtitles first.")
            return
        duration = None
        if audio_file:
            # use ffprobe to get audio duration
            cmd = [
                "ffprobe", "-v", "error", "-show_entries",
                "format=duration", "-of",
                "default=noprint_wrappers=1:nokey=1", str(audio_file)
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                duration = float(result.stdout.strip())
            except Exception:
                duration = None

        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-f", "lavfi",
            "-i", f"color=c=black:s={size}:d={duration if duration else 60}:r={fps}",
        ]
        if audio_file:
            ffmpeg_cmd += ["-i", str(audio_file)]
        ffmpeg_cmd += [
            "-vf", f"ass={self.filename}",
            "-shortest" if audio_file else "",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
        ]
        if audio_file:
            ffmpeg_cmd += ["-c:a", "aac", "-b:a", "192k"]
        ffmpeg_cmd.append(output_file_name + ".mp4")
        ffmpeg_cmd = [arg for arg in ffmpeg_cmd if arg]
        subprocess.run(ffmpeg_cmd, check=True)