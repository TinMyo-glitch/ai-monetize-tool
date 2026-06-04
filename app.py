import streamlit as st
import google.generativeai as genai
import asyncio
import edge_tts
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip, afx
import os
import time
import nest_asyncio
import tkinter as tk
from tkinter import filedialog

# Asyncio Error ကာကွယ်ရန်
nest_asyncio.apply()

st.set_page_config(page_title="AI Ultra Recap - PC Monetization Pro", layout="centered")

st.title("🛡️ AI Ultra Recap - PC Monetization Pro (Local Edition)")
st.write("PC ပေါ်တွင် ဗီဒီယိုဖိုင်ဆိုဒ် အကြီးကြီးများကို Error လုံးဝမရှိဘဲ အမြန်ဆုံး Render ဆင်းနိုင်ရန် ဖန်တီးထားပါသည်။")

# --- SIDEBAR PROPERTIES ---
with st.sidebar:
    st.header("✨ Copyright-Free Effects")
    mirror_effect = st.toggle("Mirror Effect", value=True)
    zoom_effect = st.toggle("Ken Burns Zoom", value=True)
    color_grading = st.toggle("Color Grading", value=True)
    speed_shift = st.slider("Video Speed", 0.95, 1.05, 1.02)
    pitch_shift = st.toggle("Audio Pitch Shift", value=True)
    
    st.markdown("---")
    st.header("🤖 Gemini AI Smart Features")
    enable_ai_script = st.toggle("AI Auto Script & Voiceover ဖွင့်မည်", value=False)
    
    api_key = ""
    voice_name = "my-MM-ThihaNeural"
    
    if enable_ai_script:
        api_key = st.text_input("Gemini API Key ကိုထည့်ပါ", type="password")
        voice_option = st.selectbox(
            "AI အသံရွေးချယ်ပါ",
            ["my-MM-ThihaNeural (အမျိုးသား)", "my-MM-NwayNeural (အမျိုးသမီး)"]
        )
        voice_name = voice_option.split(" ")[0]

# --- FILE SELECTION USING NATIVE WINDOWS DIALOG ---
st.header("📂 Select Files From PC")

# ဗီဒီယိုဖိုင်ရွေးရန် ခလုတ်
video_path = st.text_input("ဗီဒီယိုဖိုင်လမ်းကြောင်း (သို့မဟုတ် အောက်ကခလုတ်ဖြင့် ရွေးပါ)", "")
if st.button("📁 Browse Video File"):
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True) # Window ကို အပေါ်ဆုံးမှာ ပြရန်
    selected_video = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.mov")])
    if selected_video:
        video_path = selected_video
        st.success(f"ရွေးချယ်ပြီး - {video_path}")

# BGM ဖိုင်ရွေးရန် ခလုတ်
bgm_path = st.text_input("နောက်ခံ BGM ဖိုင်လမ်းကြောင်း (လိုအပ်မှသာ ခလုတ်ဖြင့်ရွေးပါ)", "")
if st.button("🎵 Browse BGM File"):
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    selected_bgm = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav")])
    if selected_bgm:
        bgm_path = selected_bgm
        st.success(f"ရွေးချယ်ပြီး - {bgm_path}")

# --- AI TTS Helper ---
async def generate_voiceover(text, output_audio_path, voice):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_audio_path)

# --- CORE VIDEO PROCESSING ---
def process_advanced_video(v_path, b_path, output_path):
    clip = VideoFileClip(v_path)
    fps = clip.fps if clip.fps else 24
    
    if mirror_effect:
        clip = clip.image_transform(lambda frame: frame[:, ::-1])
    
    if speed_shift != 1.0:
        clip = clip.with_fps(clip.fps * speed_shift).with_duration(clip.duration / speed_shift)
    
    generated_audio_path = None
    if enable_ai_script and api_key:
        try:
            genai.configure(api_key=api_key)
            with st.spinner("🔄 AI က ဗီဒီယိုကို ဖတ်ရှုနေပါသည်..."):
                video_file = genai.upload_file(path=v_path)
                while video_file.state.name == "PROCESSING":
                    time.sleep(2)
                    video_file = genai.get_file(name=video_file.name)
            
            with st.spinner("✍️ Gemini AI က မြန်မာဇာတ်ညွှန်း ရေးနေပါသည်..."):
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = "ဒီဗီဒီယိုကို ကြည့်ပြီး စိတ်ဝင်စားစရာကောင်းသော မြန်မာလို Movie Recap ဇာတ်ကြောင်းပြော (Narration Script) စာသားသက်သက်ပဲ ရေးပေးပါ။ အချိန်မှတ် သို့မဟုတ် Scene 1 စာလုံးတွေ လုံးဝမပါစေရ။"
                response = model.generate_content([video_file, prompt])
                script_text = response.text
                
                st.subheader("📝 AI ရေးသားလိုက်သော ဇာတ်ညွှန်း")
                st.info(script_text)
            
            with st.spinner("🎙️ မြန်မာစကားပြော AI Voiceover ပြောင်းနေပါသည်..."):
                generated_audio_path = "temp_ai_voice.mp3"
                asyncio.run(generate_voiceover(script_text, generated_audio_path, voice_name))
                
        except Exception as ai_err:
            st.error(f"⚠️ AI စနစ် Error: {ai_err}")

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
    
    if generated_audio_path and os.path.exists(generated_audio_path):
        final_audio = AudioFileClip(generated_audio_path)
        if final_audio.duration > final_clip.duration:
            final_audio = final_audio.subclipped(0, final_clip.duration)
    else:
        final_audio = final_clip.audio
        if final_audio is not None and pitch_shift:
            final_audio = final_audio.with_fps(final_audio.fps * 1.02)

    if final_audio is not None and b_path:
        bgm = AudioFileClip(b_path)
        if bgm.duration < final_clip.duration:
            bgm = bgm.with_effects([afx.AudioLoop(duration=final_clip.duration)])
        else:
            bgm = bgm.subclipped(0, final_clip.duration)
        bgm = bgm.transform(lambda get_frame, t: get_frame(t) * 0.1)
        final_audio = CompositeAudioClip([final_audio, bgm])

    if final_audio is not None:
        final_clip = final_clip.with_audio(final_audio)

    new_w, new_h = final_clip.w, final_clip.h
    if new_w % 2 != 0: new_w -= 1
    if new_h % 2 != 0: new_h -= 1
    final_clip = final_clip.resized(new_size=(new_w, new_h))

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

# --- RUN BUTTON ---
if video_path:
    if enable_ai_script and not api_key:
        st.sidebar.warning("⚠️ AI စနစ်သုံးရန် API Key ထည့်ပါ။")
    else:
        if st.button("🚀 Start Process Movie Recap", type="primary"):
            if os.path.exists(video_path):
                output_f = os.path.join(os.path.dirname(video_path), "monetize_pro_output.mp4")
                try:
                    with st.spinner("🎬 PC စွမ်းဆောင်ရည်ဖြင့် ဗီဒီယိုကို အမြန်ဆုံး Render လုပ်နေပါသည်..."):
                        process_advanced_video(video_path, bgm_path if bgm_path else None, output_f)
                    st.success(f"🎉 အောင်မြင်စွာ ပြုပြင်ပြီးပါပြီ။ ဗီဒီယိုကို အောက်ပါလမ်းကြောင်းတွင် သွားရောက်ယူနိုင်ပါသည် -\n{output_f}")
                except Exception as e:
                    st.error(f"Error တက်သွားပါသည်: {e}")
            else:
                st.error("❌ ပေးထားသော ဗီဒီယိုဖိုင်လမ်းကြောင်း မှားယွင်းနေပါသည်။")
