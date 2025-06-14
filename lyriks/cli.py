import os
import click
from pathlib import Path

@click.group()
@click.version_option()

def main():
    pass

@main.command()
@click.option("--text", "-t", default="Hello World!", help="Prints anything to the Command Line")
def test(text):
    click.secho(str(text), fg="green", bold=True)
    
@main.command()
@click.argument("audio_file", type=click.Path(exists=True, path_type=Path))
@click.argument("lyrics_file", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", help="Output video file")
@click.option("--model_size", "-m", help="Sets the whisper model size")
@click.option("--device", "-d", help="Which device to use for whisper model inference")
def generate(audio_file, lyrics_file, output, model_size, device):
    from .core import audio_processor
    from .core import video_generator    
    
    AudioProcessor = audio_processor.AudioProcessor(audio_file, lyrics_file, model_size, device)
    vocals_path = AudioProcessor.isolate_vocals()
    click.secho(f"Vocals Path: {vocals_path}", fg="green")
    AudioProcessor.remove_silence()
    transcript = AudioProcessor.transcribe()
    if output:
        with open(output, "w") as f: f.write(str(transcript))
    if os.path.exists(vocals_path):
        os.remove(vocals_path)

if __name__ == "__main__":
    main()