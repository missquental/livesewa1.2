import os
import subprocess
import threading
import streamlit as st
import gdown

# ===============================
# STREAMLIT CONFIG
# ===============================
st.set_page_config(
    page_title="YT Live Playlist Streamer",
    page_icon="📺",
    layout="wide"
)

st.title("YouTube Live – Google Drive Playlist Streamer")

# ===============================
# SESSION STATE INIT
# ===============================
if "logs" not in st.session_state:
    st.session_state.logs = []

if "ffmpeg_running" not in st.session_state:
    st.session_state.ffmpeg_running = False


# ===============================
# LOG CALLBACK (THREAD SAFE)
# ===============================
def log_callback(msg):
    st.session_state.logs.append(msg)


# ===============================
# GOOGLE DRIVE DOWNLOAD
# ===============================
def download_drive_video(url, filename):
    file_id = url.split("/d/")[1].split("/")[0]
    if not os.path.exists(filename):
        gdown.download(
            f"https://drive.google.com/uc?id={file_id}",
            filename,
            quiet=False
        )
    return filename


# ===============================
# BUILD PLAYLIST
# ===============================
def build_playlist(video_files):
    playlist = "playlist.txt"
    with open(playlist, "w") as f:
        for v in video_files:
            f.write(f"file '{os.path.abspath(v)}'\n")
    return playlist


# ===============================
# FFMPEG THREAD
# ===============================
def run_ffmpeg_playlist(playlist, stream_key, is_shorts):
    log_callback("Menjalankan FFmpeg playlist...")
    output_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"

    scale = []
    if is_shorts:
        scale = ["-vf", "scale=720:1280"]

    cmd = [
        "ffmpeg",
        "-re",
        "-stream_loop", "-1",
        "-f", "concat",
        "-safe", "0",
        "-i", playlist,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-b:v", "2500k",
        "-maxrate", "2500k",
        "-bufsize", "5000k",
        "-g", "60",
        "-keyint_min", "60",
        "-c:a", "aac",
        "-b:a", "128k",
        *scale,
        "-f", "flv",
        output_url
    ]

    log_callback(" ".join(cmd))

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    for line in process.stdout:
        log_callback(line.strip())

    log_callback("FFmpeg berhenti.")
    st.session_state.ffmpeg_running = False


# ===============================
# UI – PLAYLIST INPUT
# ===============================
st.subheader("Playlist Google Drive")
st.caption("1 link Google Drive per baris (MP4 H264 + AAC)")

drive_links = st.text_area(
    "Link Video",
    height=200,
    placeholder="https://drive.google.com/file/d/XXXXX/view\nhttps://drive.google.com/file/d/YYYYY/view"
)

if st.button("⬇ Download & Buat Playlist"):
    st.session_state.logs.clear()
    links = [l.strip() for l in drive_links.splitlines() if l.strip()]
    videos = []

    for i, link in enumerate(links):
        filename = f"video_{i+1}.mp4"
        log_callback(f"Download {filename}")
        download_drive_video(link, filename)
        videos.append(filename)

    playlist = build_playlist(videos)
    log_callback("Playlist siap: playlist.txt")
    st.success("Playlist berhasil dibuat!")

# ===============================
# STREAM SETTINGS
# ===============================
st.subheader("Streaming Settings")

stream_key = st.text_input("YouTube Stream Key", type="password")
is_shorts = st.checkbox("Mode Shorts (720x1280)")

col1, col2 = st.columns(2)

with col1:
    if st.button("▶ START STREAMING"):
        if not os.path.exists("playlist.txt") or not stream_key:
            st.error("Playlist atau Stream Key belum ada!")
        elif not st.session_state.ffmpeg_running:
            st.session_state.ffmpeg_running = True
            threading.Thread(
                target=run_ffmpeg_playlist,
                args=("playlist.txt", stream_key, is_shorts),
                daemon=True
            ).start()
            st.success("Streaming dimulai!")

with col2:
    if st.button("⛔ STOP STREAMING"):
        os.system("pkill ffmpeg")
        st.session_state.ffmpeg_running = False
        st.warning("Streaming dihentikan.")

# ===============================
# LOG VIEW
# ===============================
st.subheader("Log FFmpeg")
st.text("\n".join(st.session_state.logs[-25:]))
