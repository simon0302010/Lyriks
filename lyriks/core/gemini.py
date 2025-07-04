import json
import os
import time

from google import genai
from google.genai import types


def generate(whisper_transcript, lyrics):
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-1.5-flash"
    prompt = f"""
Given the following Whisper transcript (with word-level timestamps) and the original song lyrics, generate a JSON array as described below.

Whisper transcript:
{whisper_transcript}

Original lyrics:
{lyrics}

Each JSON object should have:
- "text": the lyric line or segment,
- "words": an array of objects with "start", "end", and "word" from the transcript,
- "start": start time of the segment (first word),
- "end": end time of the segment (last word).

Align each lyric line to the corresponding words and their timestamps. Output a valid JSON array following this schema.
YOU HAVE TO IMPROVE BOTH THE WORDS AND TEXTS!
NO MATTER HOW MESSED UP THE WHISPER TRANSCRIPT IS YOU ARE OBLIGATED TO USE THOSE TIMINGS AND THE CORRECT LYRICS!
MAKE 100% SURE THAT YOU HAVE TIMESTAMPS + CORRECT LYRICS AT THE END!
"""

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
        max_output_tokens=16384,
    )

    start_time = time.time()

    # collect chunks
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
    result_str = "".join(result_chunks).strip()

    # parse json
    try:
        result_json = json.loads(result_str)
        #print(json.dumps(result_json, indent=2, ensure_ascii=False))
        return result_json
    except Exception as e:
        print("Failed to parse JSON:", e)
        print("Raw output:")
        print(result_str)
        return False

    print(f"Took: {round(time.time() - start_time, 2)}s")
