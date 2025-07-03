![PyPI - Version](https://img.shields.io/pypi/v/lyriks-video)
![PyPI - License](https://img.shields.io/pypi/l/lyriks-video)
![](https://hackatime-badge.hackclub.com/U08HC7N4JJW/Lyriks)


<div align="left">
  <a href="https://shipwrecked.hackclub.com/?t=ghrm" target="_blank">
    <img src="https://hc-cdn.hel1.your-objectstorage.com/s/v3/739361f1d440b17fc9e2f74e49fc185d86cbec14_badge.png" 
         alt="This project is part of Shipwrecked, the world's first hackathon on an island!" 
         style="width: 35%;">
  </a>
</div>


# Lyriks

Lyriks is an automated lyrics video generator. It transcribes the audio and automatically creates a video using MoviePy.

---

## Features

- **Automatic vocal separation** using [Demucs](https://github.com/facebookresearch/demucs)
- **Transcription** with [OpenAI Whisper](https://github.com/openai/whisper) and [whisper-timestamped](https://github.com/linto-ai/whisper-timestamped)
- **Synchronized lyrics video** generation with [MoviePy](https://zulko.github.io/moviepy/)

---

## Requirements

- Linux
- A NVIDIA GPU
- 10GB of free disk space
- Python 3.11

---

## Installation

It is highly recommended to use a virtual environment for isolation:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Then install Lyriks with pip:

```bash
pip install lyriks-video
```

---

## Usage

```bash
python -m lyriks generate AUDIO_FILE LYRICS_FILE [OPTIONS]
```

### Parameters

- **AUDIO_FILE**: Path to the input audio file (e.g., `song.mp3`).  
- **LYRICS_FILE**: Path to the lyrics file (plain text).

### Options

You will be interactively prompted in the CLI for any options you leave unspecified.

- `--output`, `-o`  
  Output video file name (without extension).  
  *Example:* `-o my_lyrics_video`

- `--model_size`, `-m`  
  Sets the Whisper model size.  
  *Options:* `tiny`, `base`, `small`, `medium`, `large`  
  *Default:* `small`

- `--device`, `-d`  
  Which device to use for Whisper model inference.  
  *Options:* `cpu`, `cuda`  
  *Default:* `cpu` (use `cuda` for GPU acceleration)

---

### Example

```bash
python -m lyriks generate path/to/song.mp3 path/to/lyrics.txt -m small -d cuda -o output_video
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
```