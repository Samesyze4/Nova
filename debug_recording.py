import sounddevice as sd
import numpy as np
import soundfile as sf

samplerate = 16000  # Sample rate in Hz
duration = 5        # Duration in seconds

print(f"Recording for {duration} seconds...")
# Record audio: 1 channel, 16-bit integers
audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
sd.wait()  # Wait until recording is finished
print("Recording complete.")

# Save the recording to a WAV file
filename = "debug_recording.wav"
sf.write(filename, audio, samplerate)
print(f"Audio saved as {filename}.")

# Play back the recording
print("Playing back the recorded audio...")
data, fs = sf.read(filename, dtype='int16')
sd.play(data, fs)
sd.wait()
print("Playback finished.")
