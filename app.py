import sys
import subprocess
import threading
import time
import os
import re
import streamlit.components.v1 as components

# ================= INSTALL DEPENDENCY =================
def install_if_missing(pkg):
    try:
        __import__(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

install_if_missing("streamlit")
install_if_missing("gdown")

import streamlit as st
import gdown

# ================= GOOGLE DRIVE DOWNLOAD =================
def download_gdrive(url, log_callback):
    try:
        file_id = None

        # Ambil file ID dari berbagai format URL GDrive
        if "id=" in url:
            file_id = url.split("id=")[1].split("&")[0]
        else:
            match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
            if match:
                file_id = match.group(1)

        if not file_id:
            log_callback("❌ Gagal membaca File ID Google Drive")
            return None

        output = f"gdrive_{file_id}.mp4"
        log_callback(f"⬇️ Download video dari Google Drive...")
        gdown.download(f"https://drive.google.com/uc?id={file_id}", output, quiet=False)
        log_callback("✅ Download selesai")

        return output
    except Exception as e:
        log_callback(f"❌ Error download: {e}")
        return None

# ================= FFMPEG STREAM =================
def run_ffmpeg(video_path, stream_key, is_shorts, log_callback):
    output_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"
    scale = "-vf scale=720:1280" if is_shorts else ""

    cmd = [
        "ffmpeg", "-re", "-stream_loop", "-1",
        "-i", video_path,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-b:v", "2500k",
        "-maxrate", "2500k",
        "-bufsize", "5000k",
        "-g", "60",
        "-keyint_min", "60",
        "-c:a", "aac",
        "-b:a", "128k",
        "-f", "flv"
    ]

    if scale:
        cmd += scale.split()

    cmd.append(output_url)
    log_callback(f"▶️ Menjalankan FFmpeg")

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        for line in process.stdout:
            log_callback(line.strip())
        process.wait()
    except Exception as e:
        log_callback(f"❌ Error FFmpeg: {e}")
    finally:
        log_callback("⛔ Streaming berhenti")

# ================= MAIN APP =================
def main():
    st.set_page_config(
        page_title="Streaming YT by didinchy",
        page_icon="📡",
        layout="wide"
    )

    st.title("🎥 Live Streaming YouTube (Google Drive Support)")

    # ================= IKLAN =================
    show_ads = st.checkbox("Tampilkan Iklan", value=True)
    if show_ads:
        components.html(
            """
            <div style="background:#f0f2f6;padding:15px;border-radius:10px;text-align:center">
            <script type='text/javascript'
            src='//pl26562103.profitableratecpm.com/28/f9/95/28f9954a1d5bbf4924abe123c76a68d2.js'></script>
            </div>
            """,
            height=250
        )

    # ================= LOG AREA =================
    log_box = st.empty()
    logs = []

    def log_callback(msg):
        logs.append(msg)
        log_box.text("\n".join(logs[-25:]))

    # ================= VIDEO SOURCE =================
    st.subheader("📁 Sumber Video")

    gdrive_url = st.text_input(
        "Link Google Drive",
        placeholder="https://drive.google.com/file/d/xxxx/view"
    )

    uploaded_file = st.file_uploader(
        "Upload Video Lokal (mp4/flv)",
        type=["mp4", "flv"]
    )

    video_files = [f for f in os.listdir(".") if f.endswith((".mp4", ".flv"))]
    selected_video = st.selectbox("Video Lokal", video_files) if video_files else None

    video_path = None

    if st.button("⬇️ Download dari Google Drive"):
        if not gdrive_url:
            st.error("Masukkan URL Google Drive")
        else:
            video_path = download_gdrive(gdrive_url, log_callback)
            if video_path:
                st.success("Video siap digunakan!")

    if uploaded_file:
        with open(uploaded_file.name, "wb") as f:
            f.write(uploaded_file.read())
        video_path = uploaded_file.name

    if selected_video:
        video_path = selected_video

    # ================= STREAM CONFIG =================
    st.subheader("⚙️ Pengaturan Streaming")

    stream_key = st.text_input("YouTube Stream Key", type="password")
    is_shorts = st.checkbox("Mode Shorts (720x1280)")

    # ================= STREAM CONTROL =================
    if st.button("🚀 Mulai Streaming"):
        if not video_path or not stream_key:
            st.error("Video & Stream Key wajib diisi!")
        else:
            threading.Thread(
                target=run_ffmpeg,
                args=(video_path, stream_key, is_shorts, log_callback),
                daemon=True
            ).start()
            st.success("Streaming dimulai")

    if st.button("⛔ Stop Streaming"):
        os.system("pkill ffmpeg")
        st.warning("Streaming dihentikan")

if __name__ == "__main__":
    main()
