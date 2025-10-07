#!/usr/bin/env python3
"""Quick test to see what's slow"""

from pathlib import Path
import whisper
import time

# Settings
FOLDER = Path.home() / "Desktop" / "VoiceMemos"
audio_file = list(FOLDER.glob("*.m4a"))[0]  # Get first file

print(f"Testing with: {audio_file.name}")

# Test tiny model
print("\nLoading tiny model...")
start = time.time()
model = whisper.load_model("tiny")
print(f"Model loaded in {time.time() - start:.1f}s")

print("\nTranscribing...")
start = time.time()
result = model.transcribe(
    str(audio_file),
    language="en",
    fp16=False  # Important for CPU
)
print(f"Transcribed in {time.time() - start:.1f}s")
print(f"First 100 chars: {result['text'][:100]}")