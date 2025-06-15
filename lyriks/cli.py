import os
import json
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
    
    try:
        AudioProcessor = audio_processor.AudioProcessor(audio_file, lyrics_file, model_size, device)
        
        vocals_path = AudioProcessor.isolate_vocals()
        click.secho(f"Vocals Path: {str(vocals_path)}", fg="green")
        
        silent_parts, no_silence_file = AudioProcessor.remove_silence()
        click.secho(f"No silence audio: {str(no_silence_file)}", fg="green")
        
        transcript, words = AudioProcessor.transcribe()
        words = AudioProcessor.map_words_to_original()
        
        if output:
            with open(output, "w") as f:
                json.dump(words, f, indent=2)
        if os.path.exists(vocals_path):
            os.remove(vocals_path)
    except Exception as e:
        click.secho(f"Error: {str(e)}", fg="red")

if __name__ == "__main__":
    main()