import re
import subprocess

from tqdm import tqdm


def parse_time(timestr):
    # format: HH:MM:SS.xx
    h, m, s = re.match(r"(\d+):(\d+):([\d.]+)", timestr).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


def ffmpeg_progress(cmd, total_duration):
    process = subprocess.Popen(
        cmd, stderr=subprocess.PIPE, universal_newlines=True, text=True
    )
    pbar = tqdm(
        total=total_duration,
        unit="s",
        bar_format="{l_bar}{bar}| {n:.1f}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]",
    )
    last_time = 0
    stderr_output = []
    for line in process.stderr:
        stderr_output.append(line)
        match_time = re.search(r"time=(\d+:\d+:\d+\.\d+)", line)
        match_fps = re.search(r"fps=\s*([\d.]+)", line)
        if match_time:
            current_time = parse_time(match_time.group(1))
            pbar.update(current_time - last_time)
            last_time = current_time
        if match_fps:
            try:
                fps = float(match_fps.group(1))
                pbar.set_postfix_str(f"fps={fps:.2f}")
            except ValueError:
                pass
    pbar.close()
    process.wait()
    if process.returncode != 0:
        raise subprocess.CalledProcessError(
            process.returncode, cmd, output=None, stderr="".join(stderr_output)
        )
