import os
import sys
import json
from pathlib import Path

import click
import questionary
from questionary import Style

from .core import video_generator_mp

questionary_style = Style([("pointer", "fg:cyan bold")])


@click.group()
@click.version_option()
def main():
    pass


@main.command()
@click.argument("audio_file", type=click.Path(exists=True, path_type=Path))
@click.argument("lyrics_file", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", help="Output video file name", default=None)
@click.option("--model_size", "-m", help="Set the Whisper model size", default=None)
@click.option(
    "--device",
    "-d",
    help="Which device to use for Whisper model inference",
    default=None,
)
@click.option(
    "--generator", "-g", help="Which generator to use to create the video", default=None
)
def generate(audio_file, lyrics_file, output, model_size, device, generator):
    import io
    from contextlib import redirect_stderr, redirect_stdout

    from .core import audio_processor

    try:
        audio_name = Path(audio_file).stem
        
        if not model_size:
            model_choices = [
                {"name": "tiny   (fastest, lowest accuracy)", "value": "tiny"},
                {"name": "base   (fast, slightly better accuracy)", "value": "base"},
                {"name": "small  (fast, good accuracy)", "value": "small"},
                {"name": "medium (balanced)", "value": "medium"},
                {"name": "large  (slowest, highest accuracy)", "value": "large"},
                {"name": "turbo  (experimental, very fast)", "value": "turbo"},
            ]
            model_size = questionary.select(
                "Select the Whisper model size:",
                choices=model_choices,
                style=questionary_style,
            ).ask()
            if not model_size:
                click.secho("You must specify a model size.", fg="red")
                sys.exit(0)

        if not device:
            device_choices = [
                {"name": "NVIDIA GPU (CUDA)", "value": "cuda"},
                {"name": "CPU", "value": "cpu"},
            ]
            device = questionary.select(
                "Select the compute device:",
                choices=device_choices,
                style=questionary_style,
            ).ask()
            if not device:
                click.secho("You must specify a compute device.", fg="red")
                sys.exit(0)

        if not output:
            output = questionary.text(
                "Output video file name (without extension):", default=audio_name
            ).ask()
            if not output:
                click.secho("You must specify an output file name.", fg="red")
                sys.exit(0)

        if not generator:
            generator_choices = [
                {"name": "Moviepy (slow, low quality)", "value": "mp"},
                {
                    "name": "pysubs2 + ffmpeg (fast, good quality, experimental)",
                    "value": "ps2",
                },
                {"name": "Only save transcript (for debugging)", "value": "ts"}
            ]
            generator = questionary.select(
                "Select the video generator backend:",
                choices=generator_choices,
                style=questionary_style,
            ).ask()
            if not generator:
                click.secho("You must specify a video generator backend.", fg="red")
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
                click.secho(f"Warning: Retrying process ({str(i + 1)}/3).", fg="yellow")
            else:
                break

        click.secho(f"Vocals path: {str(vocals_path)}", fg="green")
        click.secho(f"No-silence audio: {str(no_silence_file)}", fg="green")

        words = AudioProcessor.map_words_to_original()

        if os.path.exists(vocals_path):
            os.remove(vocals_path)
        if os.path.exists(no_silence_file):
            os.remove(no_silence_file)

        temp_dir = AudioProcessor.temp_dir
        success = False

        if generator == "mp":
            VideoGenerator = video_generator_mp.VideoGenerator(audio_file)
            for segment in words:
                VideoGenerator.add_text(
                    segment["text"], segment["start"], segment["end"]
                )
            VideoGenerator.render_video(output_file_name=output, temp_dir=temp_dir)
            click.secho("Video created using MoviePy.", fg="green")
            success = True
        elif generator == "ps2":
            click.secho(
                "Video creation with pysubs2 + ffmpeg is selected (feature coming soon).",
                fg="yellow",
            )
            success = False
        elif generator == "ts":
            click.secho("Only saving transcript.", fg="green")
            with open(output + ".json", "w") as file:
                json.dump(words, file, indent=2)
            success = True
        else:
            click.secho("Unknown video generator selected.", fg="red")
            success = False

        if success:
            click.secho("Processing completed successfully!", fg="green")
        else:
            click.secho("One or more errors occurred during processing.", fg="red")

    except Exception as e:
        click.secho(f"Error: {str(e)}", fg="red")


if __name__ == "__main__":
    main()
