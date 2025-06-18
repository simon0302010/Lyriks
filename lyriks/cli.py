import os
import json
import click
from pathlib import Path

@click.group()
@click.version_option()

def main():
    pass

@main.command()
@click.option("--text", "-t", default="Hello World!", help="Creates a lyrics video clip with the specified text.")
def test(text):
    from .core import video_generator
    VideoGenerator = video_generator.VideoGenerator()
    
@main.command()
@click.argument("audio_file", type=click.Path(exists=True, path_type=Path))
@click.argument("lyrics_file", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", help="Output video file")
@click.option("--model_size", "-m", help="Sets the whisper model size")
@click.option("--device", "-d", help="Which device to use for whisper model inference")
def generate(audio_file, lyrics_file, output, model_size, device):
    from .core import audio_processor
    from .core import video_generator    
    import io
    import sys
    from contextlib import redirect_stdout, redirect_stderr
    
    try:
        AudioProcessor = audio_processor.AudioProcessor(audio_file, lyrics_file, model_size, device)
        
        for i in range(3):
            stdout_buffer = io.StringIO()
            stderr_buffer = io.StringIO()
            
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                vocals_path = AudioProcessor.isolate_vocals()
                silent_parts, no_silence_file = AudioProcessor.remove_silence()
                transcript, words = AudioProcessor.transcribe()
            
            stdout_output = stdout_buffer.getvalue()
            stderr_output = stderr_buffer.getvalue()
            
            if "Got start time outside of audio boundary" in stdout_output or "Got start time outside of audio boundary" in stderr_output:
                click.secho("Warning: Running process again", fg="yellow")
            else:
                break
        
        click.secho(f"Vocals Path: {str(vocals_path)}", fg="green")
        click.secho(f"No silence audio: {str(no_silence_file)}", fg="green")
        
        words = AudioProcessor.map_words_to_original()
        
        if output:
            with open(output, "w") as f:
                json.dump(words, f, indent=2)
        if os.path.exists(vocals_path):
            os.remove(vocals_path)
            
        click.secho("Processing completed successfully!", fg="green")
        
    except Exception as e:
        click.secho(f"Error: {str(e)}", fg="red")

if __name__ == "__main__":
    main()