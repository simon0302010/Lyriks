import json
import os
import time

import click
from google import genai
from google.genai import types

from .spinner import Spinner


def generate(whisper_transcript, lyrics):
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-2.5-flash"
    prompt = f"""
You are a forced aligner that must fix the Whisper transcript (word-level timestamps) to match the correct lyrics below.

--- Context ---
Whisper transcript (with possible errors):
{whisper_transcript}

Correct lyrics:
{lyrics}
----------------

You MUST:
1. Use *all* word-level timestamps from the transcript (the "start" and "end" times for each word).  
2. Output the correct lyrics text in the "text" field, precisely as in the reference lyrics, even if Whisper got them wrong.  
3. If Whisper is missing words, replicate or expand the transcript's closest timestamps so the "words" array matches the correct lyrics text.  
4. If Whisper has extra words not in the correct lyrics, remove or merge them, but preserve the rest of the timestamps.  
5. Output valid JSON (no markdown) in the format:
[
  {{
    "text": "...",
    "words": [
      {{"start": float, "end": float, "word": "..."}},
      ...
    ],
    "start": float,
    "end": float
  }},
  ...
]

This JSON must reflect the correct lyrics text, but each word must be assigned a start/end time from the Whisper transcript. 
If you must guess or merge timings, do so gracefully. 
NEVER output invalid JSON. 
"""

    system_prompt = "You are a forced aligner. Always follow the instructions exactly and output valid JSON as described."

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text=prompt,
                ),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=genai.types.Schema(
            type=genai.types.Type.ARRAY,
            items=genai.types.Schema(
                type=genai.types.Type.OBJECT,
                properties={
                    "text": genai.types.Schema(type=genai.types.Type.STRING),
                    "words": genai.types.Schema(
                        type=genai.types.Type.ARRAY,
                        items=genai.types.Schema(
                            type=genai.types.Type.OBJECT,
                            properties={
                                "start": genai.types.Schema(
                                    type=genai.types.Type.NUMBER
                                ),
                                "end": genai.types.Schema(type=genai.types.Type.NUMBER),
                                "word": genai.types.Schema(
                                    type=genai.types.Type.STRING
                                ),
                            },
                            required=["start", "end", "word"],
                        ),
                    ),
                    "start": genai.types.Schema(type=genai.types.Type.NUMBER),
                    "end": genai.types.Schema(type=genai.types.Type.NUMBER),
                },
                required=["text", "words", "start", "end"],
            ),
        ),
        max_output_tokens=65536,
        system_instruction=[
            types.Part.from_text(text=system_prompt),
        ],
    )

    start_time = time.time()

    # collect chunks

    click.secho("Fixing up lyrics... (This may take up to 5 minutes)", fg="blue")
    result_str = ""
    try:
        with Spinner():
            result_chunks = []
            for chunk in client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
            ):
                if hasattr(chunk, "text"):
                    result_chunks.append(chunk.text)
                elif hasattr(chunk, "data"):
                    result_chunks.append(chunk.data)
            result_str = "".join(
                [str(chunk) for chunk in result_chunks if chunk is not None]
            ).strip()
    except Exception as e:
        click.secho(f"Error during Gemini API call: {e}", fg="red")
        return False

    if not result_str.endswith("]"):
        click.secho(
            "Gemini returned invalid JSON. This might indicate the song is too long.",
            fg="red",
        )
        click.secho(f"Response length: {len(result_str)} characters", fg="yellow")
        return False

    # parse json
    try:
        result_json = json.loads(result_str)
        # print(json.dumps(result_json, indent=2, ensure_ascii=False))
        click.secho(f"Gemini took: {round(time.time() - start_time, 2)}s", fg="blue")
        return result_json
    except json.JSONDecodeError as e:
        click.secho(f"Failed to parse JSON from Gemini: {e}", fg="red")
        click.secho("Raw output:", fg="yellow")
        click.secho(result_str, fg="yellow")
        return False
    except Exception as e:
        click.secho(f"An unexpected error occurred during JSON parsing: {e}", fg="red")
        click.secho("Raw output:", fg="yellow")
        click.secho(result_str, fg="yellow")
        return False
