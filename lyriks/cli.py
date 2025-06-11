import click

from .core import audio_processor
from .core import video_generator
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
def generate(audio_file, lyrics_file, output):
    AudioProcessor = audio_processor.AudioProcessor(audio_file)
    transcript = AudioProcessor.transcribe()
    click.echo(audio_file)
    click.echo(lyrics_file)
    click.echo(output)

if __name__ == "__main__":
    main()