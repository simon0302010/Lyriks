import os
import click
import torch
import tempfile
import numpy as np
import soundfile as sf
import whisper_timestamped as whisper
from pathlib import Path
from langdetect import detect
from typing import List, Dict, Any
from demucs.audio import AudioFile
from demucs.apply import apply_model
from demucs.pretrained import get_model

class AudioProcessor:
    def __init__(self, audio_file: Path, lyrics_file: Path, model_size="small", device="cpu"):
        if isinstance(audio_file, bytes): audio_file = audio_file.decode()
        self.audio_file = str(audio_file)
        with open(lyrics_file, "r") as f: self.lyrics = f.read()
        self.language = detect(self.lyrics)
        click.secho(f"Detected language: {self.language}", fg="blue")
        self.device = device
        self.model_size = model_size
        self.vocals_file = None
        self.temp_dir = Path(tempfile.mkdtemp())

    def transcribe(self):
        model = whisper.load_model(self.model_size, device=self.device)
        
        # check which audios exist and choose one
        if hasattr(self, 'no_silence_file') and self.no_silence_file:
            audio = whisper.load_audio(self.no_silence_file)
            self.used_silence_removed = True
        elif self.vocals_file:
            audio = whisper.load_audio(self.vocals_file)
            self.used_silence_removed = False
        else:
            audio = whisper.load_audio(self.audio_file)
            self.used_silence_removed = False
        
        self.transcript = whisper.transcribe(model, audio, self.language)
        
        self.words = []
        for segment in self.transcript["segments"]:
            for word in segment['words']:
                self.words.append((float(word['start']), float(word['end']), word['text']))
        
        return self.transcript
    
    def isolate_vocals(self):
        model = get_model("htdemucs").to(self.device)
        model.eval()
        
        wav = AudioFile(Path(self.audio_file)).read(streams=0, samplerate=model.samplerate, channels=model.audio_channels)
        wav = wav.float().unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            sources = apply_model(model, wav, device=self.device)[0]
            
        vocals_idx = model.sources.index("vocals")
        vocals = sources[vocals_idx].detach().cpu().numpy().T
        
        self.vocals_file = str(self.temp_dir / 'vocals.wav')
        sf.write(self.vocals_file, vocals, model.samplerate)

        return self.vocals_file
    
    def remove_silence(self, frame_length=2048, hop_length=512, silence_thresh=0.02, min_non_silence_sec=0.2):
        if hasattr(self, 'vocals_file') and self.vocals_file:
            audio_file = self.vocals_file
        else:
            audio_file = self.audio_file

        audio_data, sr = sf.read(audio_file)
        if len(audio_data.shape) > 1:
            audio_data = audio_data.mean(axis=1)
        self.total_duration = len(audio_data) / sr

        energies = []
        for i in range(0, len(audio_data) - frame_length, hop_length):
            frame = audio_data[i:i+frame_length]
            energy = np.sqrt(np.mean(frame**2))
            energies.append(energy)
        energies = np.array(energies)

        non_silent = energies > silence_thresh
        non_silent_indices = np.where(non_silent)[0]

        self.non_silent_parts = []
        if len(non_silent_indices) > 0:
            start = non_silent_indices[0]
            for i in range(1, len(non_silent_indices)):
                if non_silent_indices[i] != non_silent_indices[i-1] + 1:
                    end = non_silent_indices[i-1]
                    start_time = start * hop_length / sr
                    end_time = (end * hop_length + frame_length) / sr
                    if end_time - start_time >= min_non_silence_sec:
                        self.non_silent_parts.append((start_time, end_time))
                    start = non_silent_indices[i]
            end = non_silent_indices[-1]
            start_time = start * hop_length / sr
            end_time = (end * hop_length + frame_length) / sr
            if end_time - start_time >= min_non_silence_sec:
                self.non_silent_parts.append((start_time, end_time))

        self.silent_parts = []
        prev_end = 0.0
        for start_time, end_time in self.non_silent_parts:
            if start_time > prev_end:
                self.silent_parts.append((float(round(prev_end, 2)), float(round(start_time, 2))))
            prev_end = end_time
        if prev_end < self.total_duration:
            self.silent_parts.append((float(round(prev_end, 2)), float(round(self.total_duration, 2))))

        # save audio without silence
        extracted = []
        for start_time, end_time in self.non_silent_parts:
            start_sample = int(start_time * sr)
            end_sample = int(end_time * sr)
            extracted.append(audio_data[start_sample:end_sample])
        if extracted:
            result = np.concatenate(extracted)
            self.no_silence_file = str(self.temp_dir / 'no_silence.wav')
            sf.write(self.no_silence_file, result, sr)

        return self.silent_parts, self.no_silence_file
    
    def map_words_to_original(self):
        # only run function if silence has been removed
        if not hasattr(self, 'used_silence_removed') or not self.used_silence_removed:
            return self.words
        
        mapping = []
        new_time = 0.0
        for orig_start, orig_end in self.non_silent_parts:
            duration = orig_end - orig_start
            mapping.append((orig_start, orig_end, new_time, new_time + duration))
            new_time += duration

        mapped_words = []
        for word_start, word_end, word in self.words:
            for orig_start, orig_end, new_start, new_end in mapping:
                if new_start <= word_start < new_end:
                    offset = word_start - new_start
                    orig_word_start = orig_start + offset
                    offset_end = word_end - new_start
                    orig_word_end = orig_start + offset_end
                    mapped_words.append((round(float(orig_word_start), 2), round(float(orig_word_end), 2), word))
                    break
        return mapped_words