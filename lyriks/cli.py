import json
import os
import sys
from pathlib import Path

import click
import questionary
from questionary import Style

questionary_style = Style([("pointer", "fg:cyan bold")])


@click.group()
@click.version_option()
def main():
    pass


@main.command()
@click.argument("audio_file", type=click.Path(exists=True, path_type=Path))
@click.argument("lyrics_file", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", help="Output video file name", default=None)
@click.option("--model_size", "-m", help="Sets the whisper model size", default=None)
@click.option(
    "--device",
    "-d",
    help="Which device to use for whisper model inference",
    default=None,
)
def generate(audio_file, lyrics_file, output, model_size, device):
    import io
    from contextlib import redirect_stderr, redirect_stdout

    from .core import audio_processor, video_generator

    try:
        if not model_size:
            model_choices = [
                {"name": "tiny   (fastest, lowest accuracy)", "value": "tiny"},
                {"name": "small  (fast, good accuracy)", "value": "small"},
                {"name": "medium (balanced)", "value": "medium"},
                {"name": "large  (slowest, highest accuracy)", "value": "large"},
                {"name": "turbo  (experimental, very fast)", "value": "turbo"},
            ]
            model_size = questionary.select(
                "Which Whisper model size do you want to use?",
                choices=model_choices,
                style=questionary_style,
            ).ask()
            if not model_size:
                sys.exit(0)
        if not device:
            device_choices = [
                {"name": "NVIDIA GPU (CUDA)", "value": "cuda"},
                {"name": "CPU", "value": "cpu"},
            ]
            device = questionary.select(
                "Which device do you want to use for computation?",
                choices=device_choices,
                style=questionary_style,
            ).ask()
            if not device:
                sys.exit(0)
        if not output:
            output = questionary.text(
                "What should be the name of the output file?"
            ).ask()
            if not output:
                sys.exit(0)

        AudioProcessor = audio_processor.AudioProcessor(
            audio_file, lyrics_file, model_size, device
        )

        for i in range(3):
            stdout_buffer = io.StringIO()
            stderr_buffer = io.StringIO()

            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                vocals_path = AudioProcessor.isolate_vocals()
                silent_parts, no_silence_file = AudioProcessor.remove_silence()
                transcript, words = AudioProcessor.transcribe()

            stdout_output = stdout_buffer.getvalue()
            stderr_output = stderr_buffer.getvalue()

            if (
                "Got start time outside of audio boundary" in stdout_output
                or "Got start time outside of audio boundary" in stderr_output
            ):
                click.secho(
                    f"Warning: Running process again ({str(i + 1)}/3)", fg="yellow"
                )
            else:
                break

        click.secho(f"Vocals Path: {str(vocals_path)}", fg="green")
        click.secho(f"No silence audio: {str(no_silence_file)}", fg="green")

        words = AudioProcessor.map_words_to_original()

        if os.path.exists(vocals_path):
            os.remove(vocals_path)

        VideoGenerator = video_generator.VideoGenerator(audio_file)
        for segment in json.loads(json.dumps(words)):
            VideoGenerator.add_text(segment["text"], segment["start"], segment["end"])
        VideoGenerator.render_video(output_file_name=output)

        click.secho("Processing completed successfully!", fg="green")

    except Exception as e:
        click.secho(f"Error: {str(e)}", fg="red")


if __name__ == "__main__":
    main()
