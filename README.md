# 🎬 Automated 9:16 Shorts, Reels & TikTok Clip Generator

A zero-dependency, GPU-accelerated Python & FFmpeg tool that automatically converts widescreen (16:9) videos into numbered, 30-second vertical (9:16) clips ready for **TikTok, Instagram Reels, and YouTube Shorts**.

---

## ⚙️ How This Works

Instead of decoding and re-encoding video frames slowly in Python, this tool builds a **single-pass FFmpeg `filter_complex` pipeline** and executes it directly on your GPU:

1. **Single-Pass Stream Cloning (`split=3`):**
   FFmpeg reads the input video once and splits the video stream in memory into three synchronized paths: the background layer, the foreground layer, and the progress bar source.
2. **Fast 4x Downscale-Blur Background (`1080x1920`):**
   Applying a heavy Gaussian blur to a full 1080p frame on the CPU creates a major bottleneck. The pipeline scales the background down by 4x (`270x480`), applies a compact Gaussian blur (`gblur=sigma=10`), and scales it back up to `1080x1920` using bicubic interpolation. This looks identical to a heavy 1080p blur while rendering **over 10x faster**.
3. **Centered 16:9 Foreground:**
   Your original widescreen video is scaled to `1080` pixels wide (preserving its aspect ratio) and overlaid dead-center on top of the blurred vertical canvas—so nothing on the left or right edges gets cut off.
4. **Animated Resetting Progress Bar:**
   Because FFmpeg's `drawbox` cannot animate width frame-by-frame, the script generates a solid color bar (`#FF0050`) and slides it across a semi-transparent dark track using the timestamp formula:
   ```text
   x = -W + W * (t/30 - floor(t/30))
   ```
   This smoothly fills the progress bar from `0%` to `100%` over 30 seconds and automatically resets to `0%` at `30s`, `60s`, `90s`, etc.
5. **Auto-Incrementing "Part X" Banner:**
   Using FFmpeg's dynamic expression evaluation (`%{eif:trunc((t+0.01)/30)+1:d}`), the `drawtext` filter calculates which 30-second segment is currently rendering and automatically updates the header badge (`Part 1`, `Part 2`, `Part 3`...) inside a semi-transparent pill box above the video.
6. **Hardware GPU Encoding & Frame-Exact Splitting:**
   * **Auto GPU Detection:** Queries your system and selects hardware encoding automatically—supporting **NVIDIA NVENC** (`h264_nvenc`), **Apple Silicon VideoToolbox** (`h264_videotoolbox`), **Intel QuickSync** (`h264_qsv`), **AMD AMF** (`h264_amf`), or CPU fallback (`libx264`).
   * **Exact Cuts:** Forces keyframes at exact 30-second intervals (`-force_key_frames`) and uses FFmpeg's `segment` muxer to output sequentially numbered files (`001.mp4`, `002.mp4`, `003.mp4`...) without dropping or duplicating frames.

---

## 🚀 How to Set Up (Windows 10 & Windows 11)

### Step 1: Install Python and FFmpeg
1. Press **Win + X** and select **Terminal (Admin)** (Windows 11) or **Windows PowerShell (Admin)** (Windows 10).
2. Run the following commands to install Python and FFmpeg and automatically add them to your system `PATH`:
   ```powershell
   winget install -e --id Python.Python.3.12
   winget install -e --id Gyan.FFmpeg
   ```
   *(If you are on an older Windows 10 build without `winget`, install Python from [python.org](https://www.python.org/downloads/windows/) with **"Add python.exe to PATH"** checked, and extract FFmpeg from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) to `C:\ffmpeg\bin` and add it to your Windows `Path` environment variable).*
3. **Close and reopen** your terminal window, then verify both tools are installed:
   ```powershell
   python --version
   ffmpeg -version
   ffprobe -version
   ```

### Step 2: Set Up the Project Folder
Create a folder (e.g., `C:\ShortsGenerator`) containing these two files:

```text
C:\ShortsGenerator\
├── make_shorts.py        # Main Python + FFmpeg generator script
├── Drop_Video_Here.bat   # Drag-and-drop Windows batch launcher
└── README.md             # Documentation
```

*(Note: When saving `make_shorts.py` and `Drop_Video_Here.bat` in Notepad, set **Save as type** to **All Files (`*.*`)** so Windows does not append `.txt` to the filenames).*

### Step 3: Run the Generator

#### Option A: Drag and Drop (Recommended)
1. Drag one or more video files (`.mp4`, `.mkv`, `.mov`) directly onto **`Drop_Video_Here.bat`** (or create a shortcut to `Drop_Video_Here.bat` on your Desktop).
2. A folder named `<videoname>_shorts` will automatically be created right next to your source video containing `001.mp4`, `002.mp4`, `003.mp4`, etc.

#### Option B: Command Line
Run the script from Command Prompt or PowerShell by passing the path to any video file:
```cmd
python make_shorts.py "C:\path\to\my_video.mp4"
```

---

## 🎨 Customization Options

You can customize the look and behavior at the bottom of `make_shorts.py` inside the `ffmpeg_gpu_shorts_generator(...)` call:

| Parameter | Default | Description |
| :--- | :--- | :--- |
| `clip_length` | `30` | Duration of each output clip in seconds. |
| `keep_remainder` | `False` | `False` drops any leftover tail shorter than `clip_length`; `True` exports the final partial clip. |
| `hardware` | `"auto"` | `"auto"`, `"nvidia"`, `"apple"`, `"intel"`, `"amd"`, or `"cpu"`. |
| `quality` | `20` | Encoding quality target (`18`–`24` recommended; lower number = higher visual quality). |
| `bar_height` | `12` | Thickness of the animated progress bar in pixels. |
| `bar_color` | `"#FF0050"` | Hex color or name for the progress bar (e.g., `"#FF0050"`, `"#00F2FE"`, `"white"`). |
| `bar_position` | `"video_bottom"` | `"video_bottom"` (flush with 16:9 clip), `"screen_top"`, or `"screen_bottom"`. |
| `title_prefix` | `""` | Optional text before the part number (e.g., `"Highlights - "` renders `"Highlights - Part 1"`). |
| `banner_y` | `440` | Vertical Y-coordinate of the title banner on the `1080x1920` canvas. |
| `font_size` | `64` | Font size of the `"Part X"` banner text. |

---

## 🛠️ Troubleshooting

* **`'ffmpeg' is not recognized as an internal or external command`:**
  Close all open terminal windows and open a new one so Windows reloads your `PATH`.
* **`Python was not found; run without arguments to install from the Microsoft Store`:**
  Go to **Windows Settings -> Apps -> Advanced app settings -> App execution aliases** and toggle **Off** `python.exe` and `python3.exe`.
* **`Driver does not support the required nvenc API version`:**
  Update your NVIDIA GPU drivers via the NVIDIA App, or set `hardware="cpu"` in `make_shorts.py`.