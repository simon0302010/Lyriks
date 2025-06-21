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

---


## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/simon0302010/Lyriks.git
   cd Lyriks
   ```

2. **(Optional) Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Lyriks:**
   ```bash
   pip install .
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