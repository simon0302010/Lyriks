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
            
    def save(self, folder):
        self.filename = str(folder / "lyrics.ass")
        self.subs.save(self.filename)
        return self.filename