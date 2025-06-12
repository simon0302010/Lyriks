import os
import click
import torch
import tempfile
import soundfile as sf
import whisper_timestamped as whisper
from pathlib import Path
from langdetect import detect
from typing import List, Dict, Any
from demucs.apply import apply_model
from demucs.pretrained import get_model
from demucs.audio import AudioFile

class AudioProcessor:
    def __init__(self, audio_file: Path, lyrics_file: Path, model_size="small", device="cpu"):
        if isinstance(audio_file, bytes): audio_file = audio_file.decode()
        self.audio_file = str(audio_file)
        with open(lyrics_file, "r") as f: self.lyrics = f.read()
        self.language = detect(self.lyrics)
        click.secho(f"Detected language: {self.language}", fg="blue")
        self.device = device
        self.model_size = model_size

    def transcribe(self):
        model = whisper.load_model(self.model_size, device=self.device)
        if self.vocals_file: self.audio = whisper.load_audio(self.vocals_file)
        else: self.audio = whisper.load_audio(self.audio_file)
        self.transcript = whisper.transcribe(model, self.audio, self.language)
        return self.transcript
    
    def isolate_vocals(self):
        output_dir = tempfile.mkdtemp()
        model = get_model("htdemucs").to(self.device)
        model.eval()
        
        wav = AudioFile(Path(self.audio_file)).read(streams=0, samplerate=model.samplerate, channels=model.audio_channels)
        wav = wav.float().unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            sources = apply_model(model, wav, device=self.device)[0]
            
        vocals_idx = model.sources.index("vocals")
        vocals = sources[vocals_idx].detach().cpu().numpy().T
        
        vocals_dir = Path(output_dir)
        self.vocals_file = str(vocals_dir / 'vocals.wav')
        sf.write(self.vocals_file, vocals, model.samplerate)

        return self.vocals_file