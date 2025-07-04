import json
import time
import os

from google import genai
from google.genai import types


def generate():
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-2.0-flash"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text="""Generate a JSON array of objects, where each object represents a segment of transcribed audio. Each segment should have 'text', 'words' (an array of [start_time, end_time, word_text]), 'start', and 'end' properties. For example, transcribe the following: We are the Champions"""
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
        print(json.dumps(result_json, indent=2, ensure_ascii=False))
    except Exception as e:
        print("Failed to parse JSON:", e)
        print("Raw output:")
        print(result_str)

    print(f"Took: {round(time.time() - start_time, 2)}s")

if __name__ == "__main__":
    generate()
