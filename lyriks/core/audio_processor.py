import click
import whisper_timestamped as whisper
from pathlib import Path
from typing import List, Dict, Any
from langdetect import detect

class AudioProcessor:
    def __init__(self, audio_file: Path, lyrics_file: Path, model_size="small", device="cpu"):
        self.audio_file = audio_file
        with open(lyrics_file, "r") as f: self.lyrics = f.read()
        self.language = detect(self.lyrics)
        click.secho(f"Detected language: {self.language}", fg="blue")
        self.audio = whisper.load_audio(audio_file)
        self.model = whisper.load_model(model_size, device=device)

    def transcribe(self):
        result = whisper.transcribe(self.model, self.audio, self.language)
        return result