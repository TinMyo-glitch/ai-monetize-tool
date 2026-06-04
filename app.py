import streamlit as st
import google.generativeai as genai
import asyncio
import edge_tts
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip, afx
import os
import time
import nest_asyncio

# Streamlit Local မောင်းနှင်စဉ် အဆင်ပြေစေရန်
nest_asyncio.apply()

st.set_page_config(page_title="AI Ultra Recap - Local Pro", layout="centered")

st.title("🛡️ AI Ultra Recap - Monetization Pro")
st.write("PC ပေါ်တွင် ဗီဒီယိုတင်ပြီး စိတ်ကြိုက် Copyright ဖြတ်နိုင်သော စနစ် ဖြစ်ပါသည်။")

# --- SIDEBAR PROPERTIES (နဂိုအတိုင်း အလုပ်လုပ်မည့် Effects များ) ---
with st.sidebar:
    st.header("✨ Copyright-Free Effects")
    mirror_effect = st.toggle("Mirror Effect", value=True)
    zoom_effect = st.toggle("Ken Burns Zoom", value=True)
    color_grading = st.toggle("Color Grading", value=True)
    speed_shift = st.slider("Video Speed", 0.95, 1.05, 1.02)
    pitch_shift = st.toggle("Audio Pitch Shift", value=True)
    
    st.markdown("---")
    st.header("🤖 Gemini AI Smart Features")
    # အမှားကင်းစေရန် ရိုးရှင်းသော Toggle စနစ်တစ်ခုတည်းသာ သုံးထားသည်
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

# PC ပေါ်တွင် Error အကင်းဆုံးဖြစ်သော မူရင်း File Uploader စနစ်ကိုပဲ စနစ်တကျ ပြန်သုံးထားပါသည်
uploaded_video = st.file_uploader("🎬 Recap ဗီဒီယိုတင်ပါ (MP4)", type=["mp4", "mov"])
uploaded_bgm = st.file_uploader("🎵 နောက်ခံ BGM တင်ပါ (MP3)", type=["mp3", "wav"])

# --- AI TTS Helper ---
async def generate_voiceover(text, output_audio_path, voice):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_audio_path)

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
    
    # ၃။ AI Smart Script & Voiceover Processing (Indentation အမှားများအားလုံးကို ရာနှုန်းပြည့် ရှင်းလင်းပြီး)
    generated_audio_path = None
    if enable_ai_script and api_key:
        try:
            genai.configure(api_key=api_key)
            
            # (A) Video Upload to Gemini
            with st.spinner("🔄 AI ထံ ဗီဒီယို ပေးပို့ပြီး ခွဲခြမ်းစိတ်ဖြာနေပါသည်..."):
                video_file = genai.upload_file(path=video_path)
                while video_file.state.name == "PROCESSING":
                    time.sleep(2)
                    video_file = genai.get_file(name=video_file.name)
            
            # (B) Generate Script
            with st.spinner("✍️ Gemini AI က ဗီဒီယိုကိုကြည့်ပြီး မြန်မာဇာတ်ညွှန်း ရေးနေပါသည်..."):
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = "ဒီဗီဒီယိုကို သေချာကြည့်ပြီး စိတ်ဝင်စားစရာကောင်းသော မြန်မာလို Movie Recap ဇာတ်ကြောင်းပြော (Narration Script) စာသားသက်သက်ပဲ ရေးပေးပါ။ အချိန်မှတ် (Timestamp) တွေ သို့မဟုတ် 'Scene 1' စတဲ့ စာလုံးတွေ လုံးဝမပါစေရ။"
                response = model.generate_content([video_file, prompt])
                script_text = response.text
                
                st.subheader("📝 AI ရေးသားလိုက်သော ဇာတ်ညွှန်း")
                st.info(script_text)
            
            # (C) Generate Audio
            with st.spinner("🎙️ မြန်မာစကားပြော AI Voiceover အဖြစ် ပြောင်းလဲနေပါသည်..."):
                generated_audio_path = "temp_ai_voice.mp3"
                asyncio.run(generate_voiceover(script_text, generated_audio_path, voice_name))
                
        except Exception as ai_err:
            st.error(f"⚠️ AI စနစ်တွင် Error တက်သွားပါသည် - {ai_err}")

    # ၄။ Segment Cut Processing (ဗီဒီယိုကို ၄ စက္ကန့်စီဖြတ်ပြီး Freeze Frame ခံသည့် စနစ်)
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
    
    # ၅။ Audio Logic စနစ် ညှိနှိုင်းခြင်း
    if generated_audio_path and os.path.exists(generated_audio_path):
        final_audio = AudioFileClip(generated_audio_path)
        if final_audio.duration > final_clip.duration:
            final_audio = final_audio.subclipped(0, final_clip.duration)
    else:
        final_audio = final_clip.audio
        if final_audio is not None and pitch_shift:
            final_audio = final_audio.with_fps(final_audio.fps * 1.02)

    # ၆။ BGM (နောက်ခံတေးဂီတ) Logic
    if final_audio is not None and bgm_path:
        bgm = AudioFileClip(bgm_path)
        if bgm.duration < final_clip.duration:
            bgm = bgm.with_effects([afx.AudioLoop(duration=final_clip.duration)])
        else:
            bgm = bgm.subclipped(0, final_clip.duration)
        bgm = bgm.transform(lambda get_frame, t: get_frame(t) * 0.1) # Volume 10%
        final_audio = CompositeAudioClip([final_audio, bgm])

    if final_audio is not None:
        final_clip = final_clip.with_audio(final_audio)

    # Resolution Check
    new_w, new_h = final_clip.w, final_clip.h
    if new_w % 2 != 0: new_w -= 1
    if new_h % 2 != 0: new_h -= 1
    final_clip = final_clip.resized(new_size=(new_w, new_h))

    # ၇။ Output File ရေးသားခြင်း
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
    if enable_ai_script and not api_key:
        st.sidebar.warning("⚠️ AI Feature ကိုသုံးရန် Sidebar တွင် Gemini API Key ထည့်ပေးပါရန်။")
    else:
        if st.button("Generate Ultra Copyright-Free Video", type="primary"):
            with st.spinner("ဗီဒီယိုကို စတင်ပြုပြင်နေပါသည်..."):
                # ယာယီဖိုင်အဖြစ် PC ထဲတွင် စနစ်တကျသိမ်းဆည်းခြင်း
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
                    
                    # ဒေါင်းလုဒ်ဆွဲရန် ခလုတ်ပြသခြင်း
                    with open(output_f, "rb") as f:
                        st.download_button("🎬 ဗီဒီယိုဒေါင်းလုဒ်ဆွဲရန်", f, file_name="monetize_pro.mp4")
                    st.success("🎉 အောင်မြင်စွာ ပြုပြင်ပြီးပါပြီ။")
                except Exception as e:
                    st.error(f"Error တက်သွားပါသည်: {e}")
