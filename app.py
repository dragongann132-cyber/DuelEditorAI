import hashlib
import json
import re
import socket
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import pandas as pd
import streamlit as st
from faster_whisper import WhisperModel

# Store user projects outside the bundled application directory.
APP_HOME = Path.home() / "DuelEditorAI"
PROJECTS_DIR = APP_HOME / "projects"
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="Duel Editor AI · Phase 1", page_icon="🎬", layout="wide")
st.title("🎬 Duel Editor AI — Giai đoạn 1")
st.caption("Phân tích video, nhận diện lời nói và đề xuất đoạn cần xem xét. Bản này KHÔNG tự xóa audio.")

FILLER_RE = re.compile(r"(?i)(?<!\w)(à|ừ|ờ|ừm|ờm|uh|um|erm|hmm)(?!\w)")

def ffmpeg_path():
    return imageio_ffmpeg.get_ffmpeg_exe()

def run_ffmpeg(args):
    proc = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-3000:] or "FFmpeg gặp lỗi.")
    return proc

def fmt_time(seconds):
    ms = int(round(seconds * 1000))
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

def make_srt(segments):
    lines = []
    for i, seg in enumerate(segments, 1):
        start = fmt_time(seg["start"]).replace(".", ",")
        end = fmt_time(seg["end"]).replace(".", ",")
        lines += [str(i), f"{start} --> {end}", seg["text"].strip(), ""]
    return "\n".join(lines)

@st.cache_resource(show_spinner=False)
def load_model(model_size, device):
    if device == "GPU (NVIDIA)":
        return WhisperModel(model_size, device="cuda", compute_type="float16")
    return WhisperModel(model_size, device="cpu", compute_type="int8")

def analyze_audio(audio_path, model_size, language, device):
    model = load_model(model_size, device)
    lang = None if language == "Tự nhận diện" else language
    segments, info = model.transcribe(
        str(audio_path), language=lang, vad_filter=True,
        word_timestamps=True, beam_size=5
    )
    result = []
    for seg in segments:
        words = []
        if seg.words:
            for word in seg.words:
                token = word.word.strip()
                words.append({
                    "word": token,
                    "start": round(float(word.start), 3),
                    "end": round(float(word.end), 3),
                    "possible_filler": bool(FILLER_RE.search(token))
                })
        text = seg.text.strip()
        result.append({
            "start": round(float(seg.start), 3),
            "end": round(float(seg.end), 3),
            "text": text,
            "words": words,
            "possible_filler_text": bool(FILLER_RE.search(text))
        })
    return result, info

with st.sidebar:
    st.header("Cài đặt phân tích")
    model_size = st.selectbox("Mô hình Whisper", ["base", "small", "medium"], index=1,
                              help="Bắt đầu với small. Nếu máy chậm hoặc thiếu bộ nhớ, thử base.")
    language = st.selectbox("Ngôn ngữ", ["Tự nhận diện", "vi", "en", "ja"], index=1)
    device = st.selectbox("Thiết bị xử lý", ["CPU (ổn định, khuyến nghị lúc đầu)", "GPU (NVIDIA)"], index=0)
    st.caption("GPU cần driver và CUDA/cuDNN tương thích. Hãy dùng CPU trước ở bản Portable.")

uploaded = st.file_uploader("Chọn video gốc", type=["mp4", "mov", "mkv", "avi", "webm"])

if uploaded:
    raw = uploaded.getvalue()
    digest = hashlib.sha256(raw).hexdigest()[:12]
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(uploaded.name).name)
    project_dir = PROJECTS_DIR / f"{Path(safe_name).stem}_{digest}"
    project_dir.mkdir(parents=True, exist_ok=True)
    video_path = project_dir / safe_name
    if not video_path.exists():
        video_path.write_bytes(raw)

    st.success(f"Đã nhận video: {uploaded.name}")
    st.video(str(video_path))

    audio_path = project_dir / "audio_16k_mono.wav"
    if st.button("1. Tách âm thanh từ video", type="primary"):
        try:
            with st.spinner("Đang tách âm thanh..."):
                run_ffmpeg([
                    ffmpeg_path(), "-y", "-i", str(video_path),
                    "-vn", "-ac", "1", "-ar", "16000",
                    "-c:a", "pcm_s16le", str(audio_path)
                ])
            st.session_state["audio_path"] = str(audio_path)
            st.session_state["project_dir"] = str(project_dir)
            st.success("Đã tách audio WAV 16 kHz mono.")
        except Exception as e:
            st.error(f"Không thể tách âm thanh: {e}")

    if st.session_state.get("audio_path") and Path(st.session_state["audio_path"]).exists():
        st.audio(st.session_state["audio_path"])
        if st.button("2. Nhận diện giọng nói và phân tích lời thoại"):
            try:
                with st.spinner("Whisper đang phân tích. Lần đầu có thể cần tải mô hình về..."):
                    rows, info = analyze_audio(
                        Path(st.session_state["audio_path"]), model_size, language,
                        "GPU (NVIDIA)" if device.startswith("GPU") else "CPU"
                    )
                st.session_state["transcript_rows"] = rows
                st.session_state["detected_language"] = info.language
                st.session_state["language_probability"] = float(info.language_probability)
                st.success(f"Hoàn tất. Ngôn ngữ: {info.language} "
                           f"(độ tin cậy {info.language_probability:.0%}).")
            except Exception as e:
                st.error(f"Không thể phân tích: {e}")
                st.info("Nếu chọn GPU và gặp lỗi CUDA/cuDNN, hãy chuyển về CPU.")

if st.session_state.get("transcript_rows"):
    rows = st.session_state["transcript_rows"]
    st.divider()
    st.subheader("3. Kết quả nhận diện")
    st.caption("Các dấu mốc từ đệm chỉ là gợi ý. Hãy nghe lại trước khi quyết định cắt.")
    st.metric("Số đoạn lời nói", len(rows))
    st.metric("Số đoạn có dấu hiệu từ đệm", sum(1 for r in rows if r["possible_filler_text"]))

    table_rows = []
    for i, r in enumerate(rows):
        flagged = [w for w in r["words"] if w["possible_filler"]]
        table_rows.append({
            "Đoạn": i + 1, "Bắt đầu (giây)": r["start"],
            "Kết thúc (giây)": r["end"], "Lời thoại": r["text"],
            "Từ có thể là từ đệm": ", ".join(w["word"] for w in flagged)
        })
    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

    st.subheader("4. Nghe và kiểm tra đoạn")
    selected = st.number_input("Chọn số thứ tự đoạn", min_value=1, max_value=len(rows), value=1, step=1)
    r = rows[int(selected) - 1]
    st.write(f"**{fmt_time(r['start'])} → {fmt_time(r['end'])}**")
    st.write(r["text"])
    audio_path = st.session_state.get("audio_path")
    if audio_path:
        st.audio(audio_path)
    st.caption("Bản đầu phát toàn bộ audio; chưa có chức năng cắt riêng từng đoạn.")

    project_dir = Path(st.session_state["project_dir"])
    transcript_json = json.dumps({
        "detected_language": st.session_state.get("detected_language"),
        "language_probability": st.session_state.get("language_probability"),
        "segments": rows
    }, ensure_ascii=False, indent=2)
    srt_text = make_srt(rows)
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("Tải transcript JSON", transcript_json, file_name="transcript.json",
                           mime="application/json")
    with c2:
        st.download_button("Tải phụ đề SRT", srt_text, file_name="subtitles.srt",
                           mime="text/plain")
    (project_dir / "transcript.json").write_text(transcript_json, encoding="utf-8")
    (project_dir / "subtitles.srt").write_text(srt_text, encoding="utf-8")
    st.info("Video gốc không bị thay đổi. Giai đoạn 1 chỉ tạo audio, transcript và gợi ý; chưa tự động cắt lời nói.")
else:
    st.info("Bắt đầu bằng cách tải video lên, sau đó nhấn nút tách âm thanh.")
