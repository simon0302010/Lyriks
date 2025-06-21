# Lyriks

Lyriks is an automated lyrics video generator. It transcribes the audio and automatically creates a video using MoviePy.

---

## Features

- **Automatic vocal separation** using [Demucs](https://github.com/facebookresearch/demucs)
- **Transcription** with [OpenAI Whisper](https://github.com/openai/whisper) and [whisper-timestamped](https://github.com/linto-ai/whisper-timestamped)
- **Synchronized lyrics video** generation with [MoviePy](https://zulko.github.io/moviepy/)

---

## Requirements

- A NVIDIA GPU
- 10GB of free disk space
- Python 3.11

---


## Installation

```bash
pip install lyriks-video
```

---

## Usage

```bash
python -m lyriks generate path/to/song.mp3 path/to/lyrics.json -m WHISPER_MODEL_SIZE -d DEVICE -o OUTPUT_FILE_NAME
```
Note: This process can take up to 20 minutes on lower end hardware.

---

## TODO

- Fix up lyrics using Gemini
- Per-word highlighting in videos
- Fancier video styles and effects
- Add more robust error handling

---

## Credits

This project uses [Demucs](https://github.com/facebookresearch/demucs) for music vocal separation.

```bibtex
@inproceedings{rouard2022hybrid,
  title={Hybrid Transformers for Music Source Separation},
  author={Rouard, Simon and Massa, Francisco and D{'e}fossez, Alexandre},
  booktitle={ICASSP 23},
  year={2023}
}

@inproceedings{defossez2021hybrid,
  title={Hybrid Spectrogram and Waveform Source Separation},
  author={D{'e}fossez, Alexandre},
  booktitle={Proceedings of the ISMIR 2021 Workshop on Music Source Separation},
  year={2021}
}