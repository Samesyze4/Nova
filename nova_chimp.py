import os
import time
import json
import threading
import random
import tempfile

# Debug: Check GPU availability with PyTorch
try:
    import torch
    print("CUDA available:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("GPU device name:", torch.cuda.get_device_name(0))
    else:
        print("No CUDA GPU detected!")
except Exception as e:
    print("Error checking CUDA:", e)

import nova_overlay  # Your overlay module (if you want visuals)
import sounddevice as sd
import simpleaudio as sa
from pydub import AudioSegment
from scipy.io import wavfile as wav
from google.cloud import texttospeech
from PIL import Image  # For image resizing
import io
import speech_recognition as sr
import pyaudio
import numpy as np

def get_valid_input_device():
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info.get('maxInputChannels') > 0:
            print(f"✅ Using microphone [{i}] {info['name']}")
            return i
    raise RuntimeError("❌ No valid input devices found.")

device_index = get_valid_input_device()
recognizer = sr.Recognizer()

# Global memory dictionary
memory = {
    "user_inputs": [],
    "nova_responses": [],
    "last_topics": [],
    "custom_responses": {},
    "unknown_inputs": []
}
MEMORY_FILE = "nova_memory.json"
VOICE_NAME = "en-US-Wavenet-F"  # This is our chosen TTS voice
AUDIO_FILE = "nova_speech.wav"
last_spoken_time = 0
is_listening = True
SILENT_TIMEOUT = 20
RANDOM_FACT_COOLDOWN = 60  # seconds
last_random_fact_time = 0

def load_memory():
    global memory
    if os.path.exists(MEMORY_FILE):
        try:
            memory = json.load(open(MEMORY_FILE, "r"))
            if "user_inputs" not in memory:
                memory["user_inputs"] = []
            if "nova_responses" not in memory:
                memory["nova_responses"] = []
            if "last_topics" not in memory:
                memory["last_topics"] = []
            if "custom_responses" not in memory:
                memory["custom_responses"] = {}
            if "unknown_inputs" not in memory:
                memory["unknown_inputs"] = []
            print("Memory loaded successfully.")
        except Exception as e:
            print("Failed to load memory:", e)
    else:
        print("No memory file found; starting fresh.")

def save_memory():
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(memory, f, indent=2)
        print("Memory saved.")
    except Exception as e:
        print("Failed to save memory:", e)

def resize_overlay(image_path, target_height):
    try:
        overlay_image = Image.open(image_path)
    except Exception as e:
        print("Error opening overlay image:", e)
        return None
    width, height = overlay_image.size
    scale_factor = target_height / height
    new_size = (int(width * scale_factor), target_height)
    resized_image = overlay_image.resize(new_size)
    resized_image.save("resized_overlay.png")
    return "resized_overlay.png"

def get_random_fact():
    facts = [
        "Chimpanzees share about 98% of their DNA with humans.",
        "A chimp's brain weighs roughly 400 grams.",
        "Chimpanzees can use tools to crack nuts.",
        "They have complex social structures and communicate in many ways.",
        "Chimpanzees are among our closest living relatives."
    ]
    return random.choice(facts)

def setup_tray():
    print("[TRAY] Setup placeholder.")
    class DummyTray:
        def run(self):
            print("Tray icon would be running now.")
    return DummyTray()

def record_with_sounddevice(duration=5, samplerate=16000, mic_index=None):
    if mic_index is None:
        print("🎤 Scanning available input devices...")
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            print(f"[{i}] {device['name']} - inputs: {device['max_input_channels']}")
        mic_index = next((i for i, d in enumerate(devices) if d['max_input_channels'] > 0), None)
    if mic_index is None:
        raise RuntimeError("❌ No valid input device found. Please check your mic or audio interface.")
    print(f"✅ Using input device index {mic_index}")
    try:
        audio = sd.rec(int(duration * samplerate),
                       samplerate=samplerate,
                       channels=1,
                       dtype='int16',
                       device=mic_index)
        sd.wait()
    except Exception as e:
        print("💥 Failed to open input stream:", e)
        raise RuntimeError("❌ Could not access microphone. Check your sound box or input config.")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        wav.write(f.name, samplerate, audio)
        print(f"Audio recorded to {f.name}")
        return f.name

def listen_loop():
    try:
        recognizer = sr.Recognizer()
        print("🎧 NOVA is listening for your voice...")
        while True:
            if is_listening:
                try:
                    wav_path = record_with_sounddevice(duration=5, mic_index=device_index)
                    with sr.AudioFile(wav_path) as source:
                        recognizer.adjust_for_ambient_noise(source, duration=1.5)
                        print("Energy threshold set to:", recognizer.energy_threshold)
                        audio = recognizer.record(source)
                    try:
                        text = recognizer.recognize_google(audio)
                        print("You said:", text)
                        memory["user_inputs"].append(text)
                        if text.lower().startswith("teach nova:"):
                            try:
                                _, content = text.split("teach nova:", 1)
                                trigger_phrase, desired_answer = content.split("=>", 1)
                                trigger_phrase = trigger_phrase.strip().lower()
                                desired_answer = desired_answer.strip()
                                memory["custom_responses"][trigger_phrase] = desired_answer
                                speak("Got it. I'll remember that.")
                                save_memory()
                            except Exception as teach_error:
                                speak("I couldn't learn that. Please use the format: 'teach nova: trigger phrase => desired answer'")
                        elif any(trigger in text.lower() for trigger in memory["custom_responses"]):
                            for trigger, custom_response in memory["custom_responses"].items():
                                if trigger in text.lower():
                                    speak(custom_response)
                                    break
                        elif "nova" in text.lower() or "hello" in text.lower():
                            speak("Yes, jungle boss!")
                        else:
                            response = learn_and_respond(text)
                            speak(response)
                            save_memory()
                    except sr.UnknownValueError:
                        print("Google Speech Recognition could not understand audio")
                    except sr.RequestError as req_err:
                        print("Could not request results from Google Speech Recognition service; Error:", req_err)
                    except Exception as e:
                        print("Unexpected error during recognition:", e)
                except Exception as e:
                    print("Speech recognition error:", e)
    except Exception as e:
        print("💥 listen_loop crashed:", e)

def learn_and_respond(text):
    for trigger, custom_response in memory["custom_responses"].items():
        if trigger in text.lower():
            return custom_response
    memory["unknown_inputs"].append(text)
    save_memory()
    return f"I don't have a learned response for '{text}' yet. I'll learn soon!"

def refresh_facts():
    try:
        while True:
            time.sleep(60)
    except Exception as e:
        print("💥 refresh_facts crashed:", e)

def speak(text):
    global last_spoken_time, is_listening
    print("NOVA:", text)
    
    was_listening = is_listening
    is_listening = False
    print("Listening disabled for speaking.")
    
    try:
        nova_overlay.set_speaking(True)
    except Exception as e:
        print("Overlay error (start):", e)
    
    resized_image_path = resize_overlay("TheNova.png", target_height=240)
    if resized_image_path:
        try:
            overlay_instance = nova_overlay.get_overlay_instance()
            if overlay_instance is not None:
                overlay_instance.update_image(resized_image_path)
            else:
                print("No overlay instance available to update image.")
        except Exception as e:
            print("Overlay update error:", e)
    else:
        print("No resized image available.")
    
    # Use SSML to adjust prosody for a more natural output.
    ssml_text = f"<speak><prosody rate='medium' pitch='-5st'>{text}</prosody></speak>"
    synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)
    voice = texttospeech.VoiceSelectionParams(language_code="en-AU", name=VOICE_NAME)
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000
    )
    tts_client = texttospeech.TextToSpeechClient()
    response = tts_client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    with open(AUDIO_FILE, "wb") as out:
        out.write(response.audio_content)
    
    try:
        wave_obj = sa.WaveObject.from_wave_file(AUDIO_FILE)
        play_obj = wave_obj.play()
        play_obj.wait_done()
    except Exception as e:
        print("Playback error:", e)
    
    try:
        nova_overlay.set_speaking(False)
    except Exception as e:
        print("Overlay error (end):", e)
    
    last_spoken_time = time.time()
    time.sleep(2)
    is_listening = was_listening
    print("Listening re-enabled.")

def silence_monitor():
    global last_random_fact_time
    try:
        while True:
            time.sleep(5)
            if is_listening and time.time() - last_spoken_time > SILENT_TIMEOUT:
                if time.time() - last_random_fact_time > RANDOM_FACT_COOLDOWN:
                    speak(get_random_fact())
                    last_random_fact_time = time.time()
    except Exception as e:
        print("💥 silence_monitor crashed:", e)

if __name__ == "__main__":
    load_memory()
    print("Starting Nova...")
    
    def start_background_systems():
        threading.Thread(target=silence_monitor, daemon=True).start()
        print("✅ silence_monitor started")
        threading.Thread(target=refresh_facts, daemon=True).start()
        print("✅ refresh_facts started")
        threading.Thread(target=listen_loop, daemon=True).start()
        print("✅ listen_loop started")
        tray_icon = setup_tray()
        tray_icon.run()
    
    threading.Thread(target=start_background_systems, daemon=True).start()
    print("Background systems started. Launching overlay...")
    try:
        nova_overlay.launch_overlay()
        print("Overlay launched.")
    except Exception as overlay_error:
        print("Error launching overlay:", overlay_error)
    
    print("Nova is running. Waiting for voice input...")
    while True:
        print("Nova is still running...")
        time.sleep(30)
