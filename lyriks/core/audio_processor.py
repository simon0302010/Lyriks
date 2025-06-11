import click
import whisper_timestamped as whisper
from pathlib import Path
from typing import List, Dict, Any

class AudioProcessor:
    def __init__(self, audio_file: Path, model_size="small", device="cpu"):
        self.audio_file = audio_file
        self.audio = whisper.load_audio(audio_file)
        self.model = whisper.load_model(model_size, device=device)

    def transcribe(self):
        result = whisper.transcribe(self.model, self.audio)
        return result