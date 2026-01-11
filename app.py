import sys
import subprocess
import threading
import time
import os
import streamlit.components.v1 as components

# ===============================
# Auto install dependencies
# ===============================
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import streamlit as st
except ImportError:
    install("streamlit")
    import streamlit as st

try:
    import gdown
except ImportError:
    install("gdown")
    import gdown


# ===============================
# Download video dari Google Drive
# ===============================
def download_from_gdrive(file_id, output):
    if not os.path.exists(output):
        url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(url, output, quiet=False)
    return output


# ===============================
# FFmpeg Streaming
# ===============================
def run_ffmpeg(video_path, stream_key, is_shorts, log_callback):
    output_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"
    scale = ["-vf", "scale=720:1280"] if is_shorts else []

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
        "-f", "flv",
        *scale,
        output_url
    ]

    log_callback("Menjalankan FFmpeg:")
    log_callback(" ".join(cmd))

    try:
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        for line in process.stdout:
            log_callback(line.strip())
        process.wait()
    except Exception as e:
        log_callback(f"Error: {e}")
    finally:
        log_callback("Streaming dihentikan.")


# ===============================
# Streamlit UI
# ===============================
def main():
    st.set_page_config(
        page_title="Streaming YT by didinchy",
        page_icon="📡",
        layout="wide"
    )

    st.title("Live Streaming YouTube (Google Drive Source)")

    # ===============================
    # Iklan
    # ===============================
    show_ads = st.checkbox("Tampilkan Iklan", value=True)
    if show_ads:
        components.html(
            """
            <div style="background:#f0f2f6;padding:20px;border-radius:10px;text-align:center">
                <script type='text/javascript'
                        src='//pl26562103.profitableratecpm.com/28/f9/95/28f9954a1d5bbf4924abe123c76a68d2.js'>
                </script>
                <p style="color:#888">Iklan Sponsor</p>
            </div>
            """,
            height=250
        )

    # ===============================
    # Google Drive Video
    # ===============================
    st.subheader("Sumber Video Google Drive")

    gdrive_url = st.text_input(
        "Link Google Drive",
        value="https://drive.google.com/file/d/1IyJ_NPHRUAIXTRl9loEp8W1yAhylHP1K/view?usp=sharing"
    )

    output_video = "drive_video.mp4"

    video_path = None
    if st.button("Download Video dari Drive"):
        try:
            file_id = gdrive_url.split("/d/")[1].split("/")[0]
            with st.spinner("Mengunduh video dari Google Drive..."):
                video_path = download_from_gdrive(file_id, output_video)
            st.success("Video berhasil diunduh!")
        except Exception as e:
            st.error(f"Gagal download: {e}")

    if os.path.exists(output_video):
        video_path = output_video
        st.video(video_path)

    # ===============================
    # Streaming Settings
    # ===============================
    st.subheader("Pengaturan Streaming")

    stream_key = st.text_input("Stream Key YouTube", type="password")
    is_shorts = st.checkbox("Mode Shorts (720x1280)")

    log_placeholder = st.empty()
    logs = []

    def log_callback(msg):
        logs.append(msg)
        log_placeholder.text("\n".join(logs[-20:]))

    if "ffmpeg_thread" not in st.session_state:
        st.session_state.ffmpeg_thread = None

    col1, col2 = st.columns(2)

    with col1:
        if st.button("▶ Jalankan Streaming"):
            if not video_path or not stream_key:
                st.error("Video dan Stream Key wajib diisi!")
            else:
                st.session_state.ffmpeg_thread = threading.Thread(
                    target=run_ffmpeg,
                    args=(video_path, stream_key, is_shorts, log_callback),
                    daemon=True
                )
                st.session_state.ffmpeg_thread.start()
                st.success("Streaming dimulai!")

    with col2:
        if st.button("⛔ Stop Streaming"):
            os.system("pkill ffmpeg")
            st.warning("Streaming dihentikan!")

    log_placeholder.text("\n".join(logs[-20:]))


if __name__ == "__main__":
    main()
