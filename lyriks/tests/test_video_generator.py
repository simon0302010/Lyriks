from lyriks.core.video_generator import VideoGenerator

data = [
    {
        "text": "Hello world!",
        "words": [[1.0, 1.5, "Hello"], [1.6, 2.0, "world!"]],
        "start": 1.0,
        "end": 2.0,
    },
    {
        "text": "This is a test.",
        "words": [
            [3.0, 3.3, "This"],
            [3.4, 3.6, "is"],
            [3.7, 3.9, "a"],
            [4.0, 4.5, "test."],
        ],
        "start": 3.0,
        "end": 4.5,
    },
]

generator = VideoGenerator(
    "/home/simon/Documents/python/testing/song.mp3", duration=5
)  # change this to the path of your audio
for segment in data:
    coords = generator.add_text(segment["text"], segment["start"], segment["end"])
    generator.place_markers(coords, segment["start"], segment["end"])
generator.render_video("output")
