import streamlit as st
from moviepy import VideoFileClip, concatenate_videoclips, afx
import os

st.set_page_config(page_title="AI Ultra Recap - Monetization Pro", layout="centered")

st.title("🛡️ AI Ultra Recap - Monetization Pro")
st.write("ဗီဒီယိုတင်လိုက်ရုံဖြင့် TikTok/Reels အတွက် Copyright လွတ်အောင် စက္ကန့်ပိုင်းအတွင်း ပြုပြင်ပေးမည့်စနစ် ဖြစ်သည်။")

# --- SIDEBAR PROPERTIES ---
with st.sidebar:
    st.header("✨ Copyright-Free Effects")
    mirror_effect = st.toggle("Mirror Effect", value=True)
    zoom_effect = st.toggle("Ken Burns Zoom", value=True)
    color_grading = st.toggle("Color Grading", value=True)
    speed_shift = st.slider("Video Speed", 0.95, 1.05, 1.02)
    pitch_shift = st.toggle("Audio Pitch Shift", value=True)

uploaded_video = st.file_uploader("🎬 Recap ဗီဒီယိုတင်ပါ (MP4)", type=["mp4", "mov"])
uploaded_bgm = st.file_uploader("🎵 နောက်ခံ BGM တင်ပါ (MP3)", type=["mp3", "wav"])

# --- CORE VIDEO PROCESSING ---
def process_advanced_video(video_path, bgm_path, output_path):
    clip = VideoFileClip(video_path)
    fps = clip.fps if clip.fps else 24
    
    # ၁။ Mirror Effect
    if mirror_effect:
        clip = clip.image_transform(lambda frame: frame[:, ::-1])
    
    # ၂။ Speed Shift
    if speed_shift != 1.0:
        clip = clip.with_fps(clip.fps * speed_shift).with_duration(clip.duration / speed_shift)
    
    # ၃။ Segment Cut Processing
    segments = []
    interval = 4
    freeze_dur = 0.5
    duration = clip.duration
    current_t = 0
    
    while current_t < duration:
        end_t = min(current_t + interval, duration)
        sub_clip = clip.subclipped(current_t, end_t)
        
        if color_grading:
            sub_clip = sub_clip.image_transform(lambda frame: (frame * 1.1).clip(0, 255).astype('uint8'))
        
        if zoom_effect:
            sub_clip = sub_clip.resized(lambda t: 1 + 0.05 * (t/sub_clip.duration))
            
        segments.append(sub_clip)
        
        if end_t < duration:
            freeze_frame = sub_clip.to_ImageClip(t=sub_clip.duration - 0.1).with_duration(freeze_dur).with_fps(fps)
            segments.append(freeze_frame)
            
        current_t = end_t

    final_clip = concatenate_videoclips(segments, method="compose")
    
    # ၄။ Audio Logic & Pitch Shift
    final_audio = final_clip.audio
    if final_audio is not None and pitch_shift:
        final_audio = final_audio.with_fps(final_audio.fps * 1.02)

    # ၅။ BGM (နောက်ခံတေးဂီတ) Logic
    if final_audio is not None and bgm_path:
        from moviepy import AudioFileClip, CompositeAudioClip
        bgm = AudioFileClip(bgm_path)
        if bgm.duration < final_clip.duration:
            bgm = bgm.with_effects([afx.AudioLoop(duration=final_clip.duration)])
        else:
            bgm = bgm.subclipped(0, final_clip.duration)
        bgm = bgm.transform(lambda get_frame, t: get_frame(t) * 0.1) # Volume 10%
        final_audio = CompositeAudioClip([final_audio, bgm])

    if final_audio is not None:
        final_clip = final_clip.with_audio(final_audio)

    # Resolution Check (Width/Height divisible by 2 error ကာကွယ်ရန်)
    new_w, new_h = final_clip.w, final_clip.h
    if new_w % 2 != 0: new_w -= 1
    if new_h % 2 != 0: new_h -= 1
    final_clip = final_clip.resized(new_size=(new_w, new_h))

    # ၆။ Output File ရေးသားခြင်း
    final_clip.write_videofile(
        output_path, 
        fps=fps, 
        codec="libx264", 
        audio_codec="aac",
        pixel_format="yuv420p",
        ffmpeg_params=["-profile:v", "main", "-level", "3.1"],
        temp_audiofile="temp-audio-render.m4a",
        remove_temp=True
    )
    clip.close()

# --- UI LOGIC ---
if uploaded_video is not None:
    if st.button("Generate Ultra Copyright-Free Video", type="primary"):
        with st.spinner("ဗီဒီယိုကို စတင်ပြုပြင်နေပါသည်..."):
            with open("temp_vid.mp4", "wb") as f:
                f.write(uploaded_video.getbuffer())
            
            bgm_p = None
            if uploaded_bgm:
                bgm_p = "temp_bgm.mp3"
                with open(bgm_p, "wb") as f:
                    f.write(uploaded_bgm.getbuffer())
            
            output_f = "ultra_recap_final.mp4"
            try:
                process_advanced_video("temp_vid.mp4", bgm_p, output_f)
                
                with open(output_f, "rb") as f:
                    st.download_button("🎬 ပြုပြင်ပြီးဗီဒီယို ဒေါင်းလုဒ်ဆွဲရန်", f, file_name="monetize_pro.mp4")
                st.success("🎉 အောင်မြင်စွာ ပြုပြင်ပြီးပါပြီ။")
            except Exception as e:
                st.error(f"Error တက်သွားပါသည်: {e}")
