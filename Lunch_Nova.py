
import speech_recognition as sr
import pyttsx3
import threading
import time
import os
import random
import requests
from bs4 import BeautifulSoup
from pathlib import Path

# === CONFIG ===
SILENT_TIMEOUT = 20  # seconds of silence before random topic
FACT_REFRESH = 3600  # refresh weird facts every hour
VB_CABLE_DEVICE_NAME = "CABLE Input (VB-Audio Virtual Cable)"

# === INIT ===
recognizer = sr.Recognizer()
tts = pyttsx3.init()
voices = tts.getProperty('voices')
facts = []
last_spoken_time = time.time()

# Set VB-Cable as output device for TTS
for voice in voices:
    if VB_CABLE_DEVICE_NAME.lower() in voice.name.lower():
        tts.setProperty('voice', voice.id)
        break
else:
    print("VB-Cable voice not found. Defaulting to system voice.")

# Speak function with timestamp update
def speak(text):
    global last_spoken_time
    print("NOVA:", text)
    tts.say(text)
    tts.runAndWait()
    last_spoken_time = time.time()

# Get random weird fact from scraped data
def get_random_fact():
    if not facts:
        return "I couldn't find anything weird. Maybe check your connection?"
    return random.choice(facts)

# Scrape Ripley's weird facts
def scrape_ripleys():
    try:
        url = "https://www.ripleys.com/weird-news/"
        res = requests.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = soup.find_all("h3", class_="entry-title")
        return [a.get_text(strip=True) for a in articles[:10]]
    except Exception as e:
        print("Ripley's scrape error:", e)
        return []

# Scrape Ancient Aliens episode titles
def scrape_aliens():
    try:
        url = "https://www.history.com/shows/ancient-aliens/season-1"
        res = requests.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        titles = soup.find_all("h3", class_="episode-title")
        return [t.get_text(strip=True) for t in titles[:10]]
    except Exception as e:
        print("Ancient Aliens scrape error:", e)
        return []

# Background: Monitor silence
def silence_monitor():
    while True:
        time.sleep(5)
        if time.time() - last_spoken_time > SILENT_TIMEOUT:
            fact = get_random_fact()
            speak(fact)

# Background: Refresh facts
def refresh_facts():
    global facts
    while True:
        new_facts = scrape_ripleys() + scrape_aliens()
        if new_facts:
            facts = new_facts
        time.sleep(FACT_REFRESH)

# Voice recognition loop
def listen_loop():
    global last_spoken_time
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        print("NOVA is listening...")
        while True:
            try:
                audio = recognizer.listen(source, timeout=5)
                text = recognizer.recognize_google(audio)
                print("You said:", text)
                last_spoken_time = time.time()
                # Basic response for now
                if "nova" in text.lower():
                    speak("Yes? I'm here.")
                elif "hello" in text.lower():
                    speak("Hey there, space cowboy.")
                else:
                    speak("That's interesting. Tell me more.")
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except Exception as e:
                print("Voice error:", e)

# Launch threads
threading.Thread(target=silence_monitor, daemon=True).start()
threading.Thread(target=refresh_facts, daemon=True).start()
listen_loop()
