import os
import sys
import platform
import subprocess

def get_video_duration(input_video_path: str) -> float:
    """Uses ffprobe to get the exact video duration in seconds."""
    command = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        input_video_path
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())

def get_default_font_arg() -> str:
    """Locates a bold system font across Windows, macOS, and Linux and escapes it for FFmpeg."""
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf",                        # Windows
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",   # macOS
        "/System/Library/Fonts/Helvetica.ttc",                 # macOS fallback
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" # Linux
    ]
    for path in candidates:
        if os.path.exists(path):
            escaped_path = path.replace("\\", "/").replace(":", "\\:")
            return f"fontfile='{escaped_path}':"
    return ""

def get_gpu_encoder_args(hardware: str = "auto", quality: int = 20) -> list:
    """Returns FFmpeg video encoder flags for NVIDIA, Apple Silicon, Intel, AMD, or CPU."""
    if hardware == "auto":
        if platform.system() == "Darwin":
            hardware = "apple"
        else:
            res = subprocess.run(
                ["ffmpeg", "-hide_banner", "-encoders"],
                capture_output=True, text=True
            )
            encoders_out = res.stdout
            if "h264_nvenc" in encoders_out:
                hardware = "nvidia"
            elif "h264_qsv" in encoders_out:
                hardware = "intel"
            elif "h264_amf" in encoders_out:
                hardware = "amd"
            else:
                hardware = "cpu"

    print(f"Using encoder profile: {hardware.upper()}")

    if hardware == "nvidia":
        return ["-c:v", "h264_nvenc", "-preset", "p4", "-rc", "vbr", "-cq", str(quality), "-b:v", "0"]
    elif hardware == "apple":
        apple_q = max(1, min(100, 100 - int(quality * 1.75)))
        return ["-c:v", "h264_videotoolbox", "-q:v", str(apple_q), "-allow_sw", "1"]
    elif hardware == "intel":
        return ["-c:v", "h264_qsv", "-preset", "fast", "-global_quality", str(quality)]
    elif hardware == "amd":
        return ["-c:v", "h264_amf", "-quality", "balanced", "-rc", "cqp", "-qp_i", str(quality), "-qp_p", str(quality)]
    else:
        return ["-c:v", "libx264", "-preset", "fast", "-crf", str(quality)]

def ffmpeg_gpu_shorts_generator(
    input_video_path: str,
    output_folder: str,
    clip_length: int = 30,
    keep_remainder: bool = False,
    hardware: str = "auto",
    quality: int = 20,
    bar_height: int = 12,
    bar_color: str = "#FF0050",
    bar_position: str = "video_bottom",
    title_prefix: str = "",
    banner_y: int = 440,
    font_size: int = 64
):
    os.makedirs(output_folder, exist_ok=True)
    output_pattern = os.path.join(output_folder, "%03d.mp4")

    progress_x_expr = f"-W+W*(t/{clip_length}-floor(t/{clip_length}))"

    safe_prefix = title_prefix.replace(":", "\\:").replace("'", "\\'")
    # Fully escaped eif expression with both required arguments (expression and format :d)
    part_text_expr = f"{safe_prefix}Part %{{eif\\:trunc((t+0.01)/{clip_length})+1\\:d}}"
    font_arg = get_default_font_arg()

    drawtext_filter = (
        f"drawtext={font_arg}"
        f"text='{part_text_expr}':"
        f"fontcolor=white:fontsize={font_size}:"
        f"box=1:boxcolor=black@0.75:boxborderw=24:"
        f"x=(w-text_w)/2:y={banner_y}"
    )

    if bar_position == "video_bottom":
        filter_complex = (
            f"[0:v]split=3[bg][fg][bar_src];"
            f"[bg]scale=270:480:force_original_aspect_ratio=increase,"
            f"crop=270:480,gblur=sigma=10,scale=1080:1920:flags=bicubic[bg_blurred];"
            f"[fg]scale=1080:-2,"
            f"drawbox=x=0:y=ih-{bar_height}:w=iw:h={bar_height}:color=black@0.45:t=fill[fg_track];"
            f"[bar_src]scale=1080:{bar_height},drawbox=color={bar_color}:t=fill[bar];"
            f"[fg_track][bar]overlay=x='{progress_x_expr}':y=H-h[fg_with_bar];"
            f"[bg_blurred][fg_with_bar]overlay=(W-w)/2:(H-h)/2,"
            f"{drawtext_filter},format=yuv420p[outv]"
        )
    else:
        y_pos = "0" if bar_position == "screen_top" else f"1920-{bar_height}"
        filter_complex = (
            f"[0:v]split=3[bg][fg][bar_src];"
            f"[bg]scale=270:480:force_original_aspect_ratio=increase,"
            f"crop=270:480,gblur=sigma=10,scale=1080:1920:flags=bicubic[bg_blurred];"
            f"[fg]scale=1080:-2[fg_scaled];"
            f"[bg_blurred][fg_scaled]overlay=(W-w)/2:(H-h)/2,"
            f"drawbox=x=0:y={y_pos}:w=1080:h={bar_height}:color=black@0.45:t=fill[canvas_track];"
            f"[bar_src]scale=1080:{bar_height},drawbox=color={bar_color}:t=fill[bar];"
            f"[canvas_track][bar]overlay=x='{progress_x_expr}':y={y_pos},"
            f"{drawtext_filter},format=yuv420p[outv]"
        )

    command = [
        "ffmpeg",
        "-y",
        "-hwaccel", "auto",
        "-i", input_video_path,
    ]

    if not keep_remainder:
        total_duration = get_video_duration(input_video_path)
        usable_duration = (int(total_duration) // clip_length) * clip_length
        if usable_duration == 0:
            raise ValueError(f"Video '{input_video_path}' is shorter than {clip_length} seconds.")
        command.extend(["-t", str(usable_duration)])

    command.extend([
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "0:a?",
        *get_gpu_encoder_args(hardware=hardware, quality=quality),
        "-c:a", "aac",
        "-b:a", "192k",
        "-force_key_frames", f"expr:gte(t,n_forced*{clip_length})",
        "-f", "segment",
        "-segment_time", str(clip_length),
        "-segment_start_number", "1",
        "-reset_timestamps", "1",
        output_pattern
    ])

    print(f"Rendering clips into: {output_folder}")
    subprocess.run(command, check=True)
    print(f"Done! Clips saved to '{output_folder}'.")

if __name__ == "__main__":
    input_path = sys.argv[1] if len(sys.argv) > 1 else "input_video.mp4"

    if not os.path.exists(input_path):
        print(f"Error: File not found -> {input_path}")
        sys.exit(1)

    video_dir = os.path.dirname(os.path.abspath(input_path))
    video_stem = os.path.splitext(os.path.basename(input_path))[0]
    auto_output_folder = os.path.join(video_dir, f"{video_stem}_shorts")

    ffmpeg_gpu_shorts_generator(
        input_video_path=input_path,
        output_folder=auto_output_folder,
        clip_length=30,
        keep_remainder=False,
        hardware="auto",
        bar_height=12,
        bar_color="#FF0050",
        bar_position="video_bottom",
        title_prefix="",
        banner_y=440
    )