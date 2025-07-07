import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

import click
import questionary
from questionary import Style

from .core import gemini, video_generator_mp, video_generator_ps2

questionary_style = Style([("pointer", "fg:cyan bold")])

system = platform.system()


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
@click.option(
    "--no-gemini",
    help="Use this if you don't want Gemini to improve the output of Whisper",
    is_flag=True,
)
@click.option(
    "--background",
    "-b",
    help="Optional background video file for the video (must be a video the same length or longer than the audio).",
    default=None,
    type=click.Path(exists=True, path_type=Path),
)
@click.option(
    "--karaoke",
    "-k",
    help="Use this if you want the video to not have vocals.",
    is_flag=True,
)
def generate(
    audio_file,
    lyrics_file,
    output,
    model_size,
    device,
    generator,
    no_gemini,
    background,
    karaoke,
):
    if system == "Darwin":
        click.secho(
            "Warning: Lyriks has not been fully tested on macOS. You may encounter bugs or unexpected behavior.",
            fg="yellow",
        )
    elif system == "Windows":
        click.secho(
            "Warning: Lyriks has not been fully tested on Windows. You may encounter bugs or unexpected behavior.",
            fg="yellow",
        )

    import io
    from contextlib import redirect_stderr, redirect_stdout

    from .core import audio_processor

    try:
        audio_name = Path(audio_file).stem
        is_interactive = sys.stdin.isatty()

        if not no_gemini and not os.environ.get("GEMINI_API_KEY"):
            click.secho("GEMINI_API_KEY environment variable not set.", fg="red")
            sys.exit(1)

        if not model_size:
            if is_interactive:
                model_choices = [
                    {"name": "tiny   (fastest, lowest accuracy)", "value": "tiny"},
                    {
                        "name": "base   (fast, slightly better accuracy)",
                        "value": "base",
                    },
                    {"name": "small  (fast, good accuracy)", "value": "small"},
                    {"name": "medium (balanced)", "value": "medium"},
                    {"name": "large  (slowest, highest accuracy)", "value": "large"},
                    {
                        "name": "turbo  (very fast, accurate, experimental)",
                        "value": "turbo",
                    },
                ]
                model_size = questionary.select(
                    "Select the Whisper model size:",
                    choices=model_choices,
                    style=questionary_style,
                ).ask()
            else:
                click.secho("You must specify a model size.", fg="red")
                sys.exit(1)

        if not device:
            if is_interactive:
                device_choices = [
                    {"name": "NVIDIA GPU (CUDA)", "value": "cuda"},
                    {"name": "CPU", "value": "cpu"},
                ]
                device = questionary.select(
                    "Select the compute device:",
                    choices=device_choices,
                    style=questionary_style,
                ).ask()
            else:
                click.secho("You must specify a compute device.", fg="red")
                sys.exit(1)

        if not output:
            if is_interactive:
                output = questionary.text(
                    "Output video file name (without extension):", default=audio_name
                ).ask()
            else:
                output = audio_name

        if not generator:
            if is_interactive:
                generator_choices = [
                    {
                        "name": "pysubs2 + ffmpeg (fast, good quality)",
                        "value": "ps2",
                    },
                    {"name": "Moviepy (slow, low quality, legacy)", "value": "mp"},
                    {"name": "Only save transcript (for debugging)", "value": "ts"},
                ]
                generator = questionary.select(
                    "Select the video generator backend:",
                    choices=generator_choices,
                    style=questionary_style,
                ).ask()
            else:
                click.secho("You must specify a video generator backend.", fg="red")
                sys.exit(1)

        if not background and is_interactive:
            use_background = questionary.confirm(
                "Do you want to use a background video for the lyrics video?",
                default=False,
            ).ask()
            if use_background:
                while True:
                    background_str = questionary.path(
                        "Select a background video file (must match or exceed song length):"
                    ).ask()
                    if not background_str:
                        click.secho(
                            "No background video selected. Skipping.", fg="yellow"
                        )
                        background = None
                        break
                    background_path = Path(background_str)
                    if not background_path.exists():
                        click.secho(
                            "File does not exist. Please select a valid file.", fg="red"
                        )
                        continue
                    if background_path.suffix.lower() not in [
                        ".mp4",
                        ".mov",
                        ".mkv",
                        ".avi",
                        ".webm",
                    ]:
                        click.secho(
                            "Please select a valid video file (mp4, mov, mkv, avi, webm).",
                            fg="red",
                        )
                        continue
                    background = background_path
                    break

        if not no_gemini and is_interactive:
            enable_gemini = questionary.confirm(
                "Enable Gemini improvements for Whisper output?"
            ).ask()
            no_gemini = not enable_gemini

        if not karaoke and is_interactive:
            karaoke = questionary.confirm(
                "Remove vocals for karaoke-style video (music only)?", default=False
            ).ask()

        if any(x is None for x in [model_size, device, output, generator]):
            click.secho("One or more required arguments are missing.", fg="red")
            sys.exit(1)

        AudioProcessor = audio_processor.AudioProcessor(
            audio_file, lyrics_file, model_size, device
        )

        # process audio
        for i in range(3):
            stdout_buffer = io.StringIO()
            stderr_buffer = io.StringIO()

            click.secho("Processing audio...", fg="blue")
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                vocals_path, music_path = AudioProcessor.isolate_vocals()
                silent_parts, no_silence_file = AudioProcessor.remove_silence()
                transcript, words = AudioProcessor.transcribe()

            stdout_output = stdout_buffer.getvalue()
            stderr_output = stderr_buffer.getvalue()

            if stdout_output.strip():
                click.secho(stdout_output.strip(), fg="white")
            if stderr_output.strip():
                click.secho(stderr_output.strip(), fg="white")

            if (
                "Got start time outside of audio boundary" in stdout_output
                or "Got start time outside of audio boundary" in stderr_output
            ):
                click.secho(
                    f"Warning: Retrying transcription process ({str(i + 1)}/3).",
                    fg="yellow",
                )
            else:
                break

        click.secho(f"Vocals path: {str(vocals_path)}", fg="blue")
        click.secho(f"Instrumental path: {str(music_path)}", fg="blue")
        click.secho(f"No-silence audio: {str(no_silence_file)}", fg="blue")

        words = AudioProcessor.map_words_to_original()
        if not no_gemini:
            gemini_output = gemini.generate(words, AudioProcessor.lyrics)
            if gemini_output:
                words = gemini_output
                click.secho("Gemini succeeded.", fg="green")
            else:
                click.secho(
                    "Gemini failed, using original lyrics. See above for details.",
                    fg="yellow",
                )

        if os.path.exists(vocals_path):
            os.remove(vocals_path)
        if os.path.exists(no_silence_file):
            os.remove(no_silence_file)

        temp_dir = AudioProcessor.temp_dir
        success = False

        # generate video
        if generator == "mp":
            VideoGenerator = video_generator_mp.VideoGenerator(
                (audio_file if not karaoke else music_path), clip_path=background
            )
            for segment in words:
                VideoGenerator.add_text(
                    segment["text"], segment["start"], segment["end"]
                )
            VideoGenerator.render_video(output_file_name=output, temp_dir=temp_dir)
            click.secho("Video created using MoviePy.", fg="green")
            success = True
        elif generator == "ps2":
            VideoGenerator = video_generator_ps2.VideoGenerator()
            for segment in words:
                VideoGenerator.add_words(segment)
            VideoGenerator.save(temp_dir)
            VideoGenerator.render_video(
                output_file_name=output,
                audio_file=(audio_file if not karaoke else music_path),
                background_path=background,
            )
            click.secho("Video created using pysubs2 + ffmpeg.", fg="green")
            success = True
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

        # cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

        click.secho(f"Video saved to {output}.mp4", fg="green")

        if is_interactive:
            open_video = questionary.confirm("Open the video now?").ask()
            if open_video:
                video_path = f"{output}.mp4"
                try:
                    if system == "Darwin":
                        subprocess.Popen(
                            ["open", video_path],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                    elif system == "Windows":
                        os.startfile(video_path)
                    elif system == "Linux":
                        subprocess.Popen(
                            ["xdg-open", video_path],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                    else:
                        click.secho(
                            "Unknown system, cannot open video automatically.",
                            fg="yellow",
                        )
                        sys.exit(0)
                    click.secho("Opened video in default player.", fg="green")
                except Exception as e:
                    click.secho(f"Could not open video: {e}", fg="red")
                sys.exit(0)

    except FileNotFoundError as e:
        click.secho(f"Error: File not found - {e}", fg="red")
        sys.exit(1)
    except Exception as e:
        import traceback

        click.secho(f"An unexpected error occurred: {e}", fg="red")
        click.secho(traceback.format_exc(), fg="red")
        sys.exit(1)


if __name__ == "__main__":
    main()
