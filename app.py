import streamlit as st
import google.generativeai as genai
import asyncio
import edge_tts
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip, afx
import os
import time
import nest_asyncio

# Streamlit/Cloud ပေါ်တွင် Asyncio Error မတက်စေရန်
nest_asyncio.apply()

# Page Config
st.set_page_config(page_title="AI Ultra Recap - Monetization Pro", layout="centered")

st.title("🛡️ AI Ultra Recap - Monetization Pro")

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
    # AI Feature ခလုတ် (လိုအပ်မှဖွင့်ရန်)
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

uploaded_video = st.file_uploader("Recap ဗီဒီယိုတင်ပါ", type=["mp4", "mov"])
uploaded_bgm = st.file_uploader("BGM တင်ပါ", type=["mp3", "wav"])

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
    
    # ၃။ AI Smart Script & Voiceover Processing (ခလုတ်ဖွင့်ထားမှ အလုပ်လုပ်မည်)
    generated_audio_path = None
    if enable_ai_script and api_key:
        try:
            # Cloud နှင့် ကိုက်ညီသော ဖွဲ့စည်းမှုပုံစံဖြင့် ချိတ်ဆက်ခြင်း
            genai.configure(api_key=api_key)
            
            # (A) ဗီဒီယိုကို Gemini API ထံ Upload တင်ခြင်း (genai မှ တိုက်ရိုက်ခေါ်ရန် ပြင်ဆင်ပြီး)
            with st.spinner("🔄 AI ထံ ဗီဒီယို ပေးပို့ပြီး ခွဲခြမ်းစိတ်ဖြာနေပါသည်..."):
                video_file = genai.upload_file(path=video_path)
                while video_file.state.name == "PROCESSING":
                    time.sleep(2)
                    video_file = genai.get_file(name=video_file.name)
                
                if video_file.state.name != "ACTIVE":
                    st.error("Gemini က ဗီဒီယိုကို ဖတ်ရတာ အဆင်မပြေဖြစ်သွားပါတယ်။")
            
            # (B) Gemini 1.5 Flash ဖြင့် မြန်မာ Script ရေးခိုင်းခြင်း
            with st.spinner("✍️ Gemini AI က ဗီဒီယိုကိုကြည့်ပြီး မြန်မာဇာတ်ညွှန်း ရေးနေပါသည်..."):
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = "ဒီဗီဒီယိုကို သေချာကြည့်ပြီး စိတ်ဝင်စားစရာကောင်းသော မြန်မာလို Movie Recap ဇာတ်ကြောင်းပြော (Narration Script) စာသားသက်သက်ပဲ ရေးပေးပါ။ အချိန်မှတ် (Timestamp) တွေ သို့မဟုတ် 'Scene 1' စတဲ့ စာလုံးတွေ လုံးဝမပါစေရ။"
                
                response = model.generate_content([video_file, prompt])
                script_text = response.text
                
                # ရလာတဲ့ Script ကို UI မှာ ပြသခြင်း
                st.subheader("📝 AI ရေးသားလိုက်သော ဇာတ်ညွှန်း")
                st.info(script_text)
            
            # (C) ရလာတဲ့ စာသားကို Edge-TTS ဖြင့် မြန်မာ AI အသံပြောင်းခြင်း
            with st.spinner("🎙️ မြန်မာစကားပြော AI Voiceover အဖြစ် ပြောင်းလဲနေပါသည်..."):
                generated_audio_path = "temp_ai_voice.mp3"
                asyncio.run(generate_voiceover(script_text, generated_audio_path, voice_name))
                
        except Exception as ai_err:
            st.error(f"⚠️ AI စနစ်တွင် Error တက်သွားပါသည် (Key မမှန်ပါက ဖြစ်နိုင်သည်) - {ai_err}")

    # ၄။ Segment Cut Processing (နဂိုရှိပြီးသား Copyright-Free Cut စနစ်)
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
        # AI Voiceover ဖွင့်ထားရင် မူရင်းဗီဒီယိုအသံအစား AI အသံကို သုံးမည်
        final_audio = AudioFileClip(generated_audio_path)
        if final_audio.duration > final_clip.duration:
            final_audio = final_audio.subclipped(0, final_clip.duration)
    else:
        # AI ပိတ်ထားရင် မူရင်းဗီဒီယိုအသံကိုပဲ သုံးမည်
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

    # Resolution Check (width divisible by 2 error ကာကွယ်ရန်)
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
            with st.spinner("ဗီဒီယိုကို အဆင့်မြှင့်တင်နေပါသည်..."):
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
                    st.success("အောင်မြင်စွာ ပြုပြင်ပြီးပါပြီ။")
                except Exception as e:
                    st.error(f"Error တက်သွားပါသည်: {e}")
