import os
import subprocess
from pydub import AudioSegment
from utils.openai_utils import generate_audio_response


def run_ffmpeg(cmd: list[str]):
    """
    Run an ffmpeg command, raising CalledProcessError on failure.
    """
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def extract_video_segment(input_path: str, start: float, end: float, output_path: str) -> str:
    """
    Extract a segment from `input_path` starting at `start` seconds.
    If `end` is provided, uses duration = end - start via -t; otherwise extracts until EOF.
    Always uses -ss before -i for accurate copy and seeks on keyframes.
    Paths are converted to absolute forward-slash style.
    """
    # compute duration for -t
    duration = None if end is None else end - start
    # prepare absolute paths
    abs_input = os.path.abspath(input_path).replace("\\", "/")
    abs_output = os.path.abspath(output_path).replace("\\", "/")

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-i", abs_input
    ]
    if duration is not None:
        cmd += ["-t", str(duration)]
    cmd += ["-c", "copy", abs_output]

    run_ffmpeg(cmd)
    return output_path


def generate_tts_audio(text: str, output_path: str) -> str:
    """
    Generate TTS audio for `text`. If `output_path` ends with .mp3,
    generates a WAV then converts to MP3 at 16kHz mono; else produces WAV.
    """
    base_ext = os.path.splitext(output_path)[1].lower()
    if base_ext == ".mp3":
        wav_temp = output_path.replace('.mp3', '.wav')
        generate_audio_response(text, output_path=wav_temp)
        cmd = [
            "ffmpeg", "-y",
            "-i", os.path.abspath(wav_temp).replace("\\", "/"),
            "-codec:a", "libmp3lame",
            "-qscale:a", "2",
            "-ar", "16000",
            "-ac", "1",
            os.path.abspath(output_path).replace("\\", "/")
        ]
        run_ffmpeg(cmd)
        os.remove(wav_temp)
    else:
        generate_audio_response(text, output_path=output_path)
    return output_path


def get_audio_duration(audio_path: str) -> float:
    """Return the duration (in seconds) of any audio file."""
    return AudioSegment.from_file(audio_path).duration_seconds


def capture_frame(video_path: str, timestamp: float, frame_path: str) -> str:
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(timestamp),
        "-i", os.path.abspath(video_path).replace("\\", "/"),
        "-vframes", "1",
        frame_path
    ]
    run_ffmpeg(cmd)
    return frame_path


def create_freeze_frame_video(frame_path: str,
                              audio_path: str,
                              output_path: str,
                              post_freeze_pause: float = 0.5) -> str:
    """Hold frame static while playing audio (16kHz mono), then pause."""
    duration = get_audio_duration(audio_path)
    total = duration + post_freeze_pause
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", frame_path,
        "-i", os.path.abspath(audio_path).replace("\\", "/"),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-ar", "16000",
        "-ac", "1",
        "-b:a", "192k",
        "-t", str(total),
        "-pix_fmt", "yuv420p",
        output_path
    ]
    run_ffmpeg(cmd)
    return output_path


def write_concat_file(segment_paths: list[str], list_file: str) -> str:
    dirpath = os.path.dirname(list_file)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    with open(list_file, "w", encoding="utf-8") as fh:
        for seg in segment_paths:
            fh.write(f"file '{os.path.abspath(seg).replace('\\', '/')}'\n")
    return list_file


def concatenate_segments(list_file: str, output_path: str) -> str:
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", os.path.abspath(list_file).replace("\\", "/"),
        "-c:v", "libx264",
        "-c:a", "aac",
        "-ar", "16000",
        "-ac", "1",
        os.path.abspath(output_path).replace("\\", "/")
    ]
    run_ffmpeg(cmd)
    return output_path


def edit_video_with_tts(video_path: str,
                        data: dict,
                        output_path: str,
                        temp_dir: str = "./tts",
                        audio_ext: str = "mp3") -> str:
    os.makedirs(temp_dir, exist_ok=True)
    if not output_path.lower().endswith(".mp4"):
        output_path += ".mp4"

    entries = sorted(data["entries"]["pings"]["entries"], key=lambda e: e["start"])
    segments = []
    last_time = 0.0

    for idx, entry in enumerate(entries):
        start = entry["start"]
        eid = entry["id"]
        freeze_point = start + 0.5

        # segment before freeze
        seg_path = os.path.join(temp_dir, f"segment_{idx}.mp4")
        extract_video_segment(video_path, last_time, freeze_point, seg_path)
        segments.append(seg_path)

        # TTS
        audio_path = os.path.join(temp_dir, f"tts_{eid}.{audio_ext}")
        generate_tts_audio(entry["debunking_information"], audio_path)

        # frame
        frame_path = os.path.join(temp_dir, f"frame_{eid}.png")
        capture_frame(video_path, start, frame_path)

        # freeze video
        freeze_vid = os.path.join(temp_dir, f"freeze_{eid}.mp4")
        create_freeze_frame_video(frame_path, audio_path, freeze_vid)
        segments.append(freeze_vid)

        last_time = freeze_point

    # tail
    final_seg = os.path.join(temp_dir, "segment_final.mp4")
    extract_video_segment(video_path, last_time, None, final_seg)
    segments.append(final_seg)

    # concat
    list_file = os.path.join(temp_dir, "concat_list.txt")
    write_concat_file(segments, list_file)
    concatenate_segments(list_file, output_path)

    return output_path
