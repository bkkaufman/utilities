#!/usr/bin/env python3
import os
import re
from abstract_generator import enhance_transcript_with_abstract, AbstractGenerator
import time
import warnings
from datetime import datetime
from pathlib import Path

import ffmpeg
import numpy as np
import torch
import torchaudio
from dotenv import load_dotenv

# Transcription (Apple MLX)
from mlx_whisper import transcribe

# Speaker embeddings
from resemblyzer import VoiceEncoder, preprocess_wav

# Clustering (lightweight diarization path)
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# ======================
# CONFIG
# ======================
MODEL_NAME = "mlx-community/whisper-base-mlx"  # Use base instead of tiny for better accuracy
CHUNK_SEC = 30  # Smaller chunks for better memory management
MIN_SPEAKERS = 2
MAX_SPEAKERS = 5
SIM_THRESHOLD = 0.45

VOICE_MEMOS_FOLDER = Path.home() / "Desktop" / "VoiceMemos"
OUTPUT_FOLDER = Path.home() / "Desktop" / "Transcripts"
REF_DIR = Path(__file__).parent / "voice_refs"

USE_ENROLLMENT = True
USE_PYANNOTE = False  # Disable by default for speed

# Performance optimization for M2
torch.set_num_threads(8)  # Use more threads on M2
warnings.filterwarnings("ignore", category=UserWarning)

# ======================
# ENV / TOKENS
# ======================
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")


# ======================
# HELPERS
# ======================
def convert_to_wav(input_file: Path) -> Path:
    """Convert audio to mono 16 kHz WAV for MLX Whisper / diarizers."""
    output_file = input_file.with_suffix(".wav")
    if output_file.exists():
        return output_file
    print(f"  Converting {input_file.name} to WAV...")
    (
        ffmpeg
        .input(str(input_file))
        .output(str(output_file), ar=16000, ac=1)
        .overwrite_output()
        .run(quiet=True)
    )
    return output_file


def run_transcription_with_diarization(audio_file: Path, duration: float):
    """Single-pass transcription with word-level timestamps for better diarization."""
    print("  Starting transcription with word timestamps...")

    # Use word_timestamps for better alignment
    result = transcribe(
        str(audio_file),
        path_or_hf_repo=MODEL_NAME,
        word_timestamps=True,  # Enable word-level timestamps
        verbose=False
    )

    segments_with_words = []
    for seg in result["segments"]:
        segments_with_words.append({
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"],
            "words": seg.get("words", [])  # Word-level timing if available
        })

    print(f"  ✅ Transcription complete ({len(segments_with_words)} segments)")
    return segments_with_words


# ======================
# ENROLLMENT
# ======================
def load_enrolled() -> dict:
    """Load and embed enrolled speakers from voice_refs/*.wav → {Name: embedding}."""
    enrolled = {}
    if not REF_DIR.exists():
        return enrolled
    encoder = VoiceEncoder()
    for ref_file in REF_DIR.glob("*.wav"):
        name = ref_file.stem.replace("_ref", "").replace("-", " ").strip().title()
        print(f"  🎙️ Loading reference voice for {name} from {ref_file}")
        wav = preprocess_wav(str(ref_file))
        emb = encoder.embed_utterance(wav)
        enrolled[name] = emb
    if not enrolled:
        print("  ⚠️ No reference WAV files found in voice_refs/. Using generic speakers.")
    return enrolled


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


# ======================
# IMPROVED LIGHTWEIGHT DIARIZATION
# ======================
def run_diarization_improved(
        audio_file: Path,
        segments: list,
        duration: float,
        min_speakers: int = MIN_SPEAKERS,
        max_speakers: int = MAX_SPEAKERS,
        enrolled_speakers: dict = None
):
    """Improved diarization that preserves sentence boundaries."""
    print("  Running improved diarization...")
    wav, sr = torchaudio.load(str(audio_file))
    wav = wav.squeeze()

    encoder = VoiceEncoder()
    segment_embeddings = []
    valid_segments = []

    # Process each transcription segment to get speaker embeddings
    for seg in segments:
        start_samp = int(seg["start"] * sr)
        end_samp = int(seg["end"] * sr)

        if end_samp <= start_samp:
            continue

        chunk = wav[start_samp:end_samp]
        wav_np = chunk.cpu().numpy().astype("float32")

        if wav_np.size < sr // 2:  # Skip very short segments
            continue

        try:
            # Get embedding for the entire segment
            emb = encoder.embed_utterance(wav_np)
            segment_embeddings.append(emb)
            valid_segments.append(seg)
        except Exception as e:
            print(f"  ⚠️ Skipping segment: {e}")
            continue

    if not segment_embeddings:
        print("  ⚠️ No valid segments for diarization.")
        return []

    embeddings = np.vstack(segment_embeddings)

    # Estimate number of speakers with better heuristics
    best_k, best_score = min_speakers, -1
    for k in range(min_speakers, min(max_speakers, len(embeddings)) + 1):
        if k >= len(embeddings):
            break
        kmeans = KMeans(n_clusters=k, random_state=0, n_init=10).fit(embeddings)
        if len(set(kmeans.labels_)) > 1:
            score = silhouette_score(embeddings, kmeans.labels_)
            if score > best_score:
                best_k, best_score = k, score

    print(f"  🧭 Estimated speaker count: {best_k}")

    # Final clustering
    kmeans = KMeans(n_clusters=best_k, random_state=0, n_init=10)
    labels = kmeans.fit_predict(embeddings)

    # Merge consecutive segments from same speaker
    speakers = []
    current_speaker = None
    current_start = None
    current_end = None
    current_text = []

    for seg, label, emb in zip(valid_segments, labels, embeddings):
        label_name = f"Speaker {label + 1}"

        # Try to match with enrolled speakers
        if enrolled_speakers:
            best_name, best_sim = None, -1.0
            for name, ref_emb in enrolled_speakers.items():
                sim = cosine_similarity(emb, ref_emb)
                if sim > best_sim:
                    best_name, best_sim = name, sim
            if best_sim > SIM_THRESHOLD:
                label_name = best_name

        # Merge logic: combine consecutive segments from same speaker
        if label_name == current_speaker and current_end is not None:
            # Check if segments are close enough to merge (within 2 seconds)
            if seg["start"] - current_end < 2.0:
                current_end = seg["end"]
                current_text.append(seg["text"])
            else:
                # Save current and start new
                if current_speaker:
                    speakers.append({
                        "speaker": current_speaker,
                        "start": current_start,
                        "end": current_end,
                        "text": " ".join(current_text)
                    })
                current_speaker = label_name
                current_start = seg["start"]
                current_end = seg["end"]
                current_text = [seg["text"]]
        else:
            # Save previous speaker's segment
            if current_speaker:
                speakers.append({
                    "speaker": current_speaker,
                    "start": current_start,
                    "end": current_end,
                    "text": " ".join(current_text)
                })
            # Start new speaker segment
            current_speaker = label_name
            current_start = seg["start"]
            current_end = seg["end"]
            current_text = [seg["text"]]

    # Don't forget the last segment
    if current_speaker:
        speakers.append({
            "speaker": current_speaker,
            "start": current_start,
            "end": current_end,
            "text": " ".join(current_text)
        })

    print(f"  ✅ Diarization complete. Found {best_k} speakers in {len(speakers)} segments.")
    return speakers


# ======================
# PYANNOTE DIARIZATION (optional, for accuracy)
# ======================
def run_diarization_pyannote(
        audio_file: Path,
        segments: list,
        hf_token: str,
        enrolled_speakers: dict | None = None
):
    """Pyannote with segment merging."""
    if not hf_token:
        raise RuntimeError("HF_TOKEN is missing.")

    from pyannote.audio import Pipeline

    print("  Running diarization (Pyannote)...")
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=hf_token)

    # Configure for better performance
    pipeline.instantiate({
        "clustering": {
            "method": "centroid",
            "min_cluster_size": 15,
            "threshold": 0.7
        }
    })

    diar = pipeline(str(audio_file))

    # Convert to our format with text alignment
    speakers = []
    for seg in segments:
        # Find which speaker this segment belongs to
        mid_time = (seg["start"] + seg["end"]) / 2
        speaker = None

        for turn, _, label in diar.itertracks(yield_label=True):
            if turn.start <= mid_time <= turn.end:
                speaker = str(label)
                break

        if speaker:
            # Check if we can merge with previous segment
            if speakers and speakers[-1]["speaker"] == speaker and \
                    seg["start"] - speakers[-1]["end"] < 2.0:
                speakers[-1]["end"] = seg["end"]
                speakers[-1]["text"] += " " + seg["text"]
            else:
                speakers.append({
                    "speaker": speaker,
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"]
                })

    print(f"  ✅ Pyannote diarization complete: {len(speakers)} segments")
    return speakers


# ======================
# OUTPUT (Markdown)
# ======================
NORMALIZE_MAP = {
    "a.b. testing": "A/B testing",
    "modic": "Mautic",
    "mautic": "Mautic",
    "mail cow": "Mailcow",
    "mail cowl": "Mailcow",
    "milk cow": "Mailcow",
    "o.t.c.": "Order-to-Cash",
    "q.a.": "Quality Assurance",
    "doctor": "Docker",
    "cool fun": "Coolify",
    "d.c.": "DKIM",
}

CANDIDATE_TOOLS = [
    "Mautic", "Mailcow", "Coolify", "Docker", "Ansible",
    "Shortcut", "Speckit", "Serena", "Mermaid", "Dash",
    "Pathfinder", "Bartender", "Ice", "Crawl4ai", "Firecrawl",
    "DKIM", "Postfix", "Amazon", "YouTube"
]


def normalize_text(text: str) -> str:
    t = text
    for wrong, right in NORMALIZE_MAP.items():
        t = re.sub(rf"\b{re.escape(wrong)}\b", right, t, flags=re.IGNORECASE)
    return t


def fmt_time(sec: float) -> str:
    m, s = divmod(int(sec), 60)
    return f"{m:02d}:{s:02d}"


def save_transcript(file: Path, segments, speakers):
    """Save transcript with AI-generated abstract and complete speaker turns."""
    output_dir = OUTPUT_FOLDER if OUTPUT_FOLDER else file.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{file.stem}_transcript.md"

    # Get full text for tool detection
    full_text = " ".join(sp.get("text", "") for sp in speakers)

    # Traditional tool detection
    mentioned = []
    for tool in CANDIDATE_TOOLS:
        if re.search(rf"\b{re.escape(tool)}\b", full_text, flags=re.IGNORECASE):
            mentioned.append(tool)

    # Generate AI-powered abstract if Ollama is available
    print("  🤖 Generating AI abstract...")
    abstract_result = enhance_transcript_with_abstract(
        speakers,
        tools_mentioned=mentioned,
        method="structured"  # or "simple" for faster processing
    )

    # Use AI abstract if available, otherwise fallback
    if abstract_result and abstract_result.get("abstract"):
        abstract = abstract_result["abstract"]
        key_points = abstract_result.get("key_points", [])
        decisions = abstract_result.get("decisions", [])
        ai_tools = abstract_result.get("tools", [])

        # Merge AI-detected tools with regex-detected tools
        all_tools = list(set(mentioned + ai_tools))
    else:
        # Fallback to simple abstract
        print("  ⚠️ Using fallback abstract (Ollama not available)")
        abstract = " ".join(normalize_text(sp.get("text", "")) for sp in speakers[:3])[:200] + "..."
        key_points = []
        decisions = []
        all_tools = mentioned

    # Write the enhanced transcript
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# Transcript: {file.stem}\n\n")
        f.write("_Generated with MLX-Whisper + diarization + AI summarization_\n\n")

        # Abstract section
        f.write("## Abstract\n\n")
        f.write(abstract.strip() + "\n\n")

        # Key points if available
        if key_points:
            f.write("## Key Points\n\n")
            for point in key_points:
                f.write(f"- {point}\n")
            f.write("\n")

        # Decisions/Action items if available
        if decisions:
            f.write("## Decisions & Action Items\n\n")
            for decision in decisions:
                f.write(f"- {decision}\n")
            f.write("\n")

        # Tools section
        f.write("## Tools & Technologies Mentioned\n\n")
        if all_tools:
            for tool in sorted(set(all_tools)):
                f.write(f"- {tool}\n")
        else:
            f.write("_No specific tools detected._\n")
        f.write("\n---\n\n")

        # Full transcript
        f.write("## Full Transcript\n\n")
        for sp in speakers:
            speaker = sp["speaker"]
            start = fmt_time(sp["start"])
            end = fmt_time(sp["end"])
            text = normalize_text(sp.get("text", ""))

            f.write(f"- **{speaker}** [{start}–{end}]: {text}\n")

    print(f"  📄 Enhanced transcript saved to {out_path}")



# ======================
# MAIN
# ======================
def main():
    start_time = time.time()
    print(f"\n⏱️ Starting transcription run at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Load enrolled speakers
    enrolled = load_enrolled() if USE_ENROLLMENT else None

    if USE_PYANNOTE and not HF_TOKEN:
        print("❌ USE_PYANNOTE is True but HF_TOKEN is missing.")
        return

    if not VOICE_MEMOS_FOLDER.exists():
        print(f"❌ Voice memos directory not found: {VOICE_MEMOS_FOLDER}")
        return

    input_files = list(VOICE_MEMOS_FOLDER.glob("*.m4a"))
    if not input_files:
        print(f"No .m4a files found in {VOICE_MEMOS_FOLDER}")
        return

    for file in input_files:
        print(f"\n🚀 Processing {file.name}...")
        wav_file = convert_to_wav(file)

        try:
            probe = ffmpeg.probe(str(wav_file))
            duration = float(probe["format"]["duration"])
            print(f"  Duration: {duration:.1f} seconds")
        except Exception:
            duration = 0.0
            print("  ⚠️ Could not determine duration.")

        # Combined transcription and diarization
        t_start = time.time()
        segments = run_transcription_with_diarization(wav_file, duration)
        t_elapsed = time.time() - t_start
        print(f"  ⏱ Transcription took {int(t_elapsed // 60)}m {int(t_elapsed % 60)}s")

        # Diarization
        d_start = time.time()
        if USE_PYANNOTE:
            speakers = run_diarization_pyannote(wav_file, segments, HF_TOKEN, enrolled_speakers=enrolled)
        else:
            speakers = run_diarization_improved(wav_file, segments, duration, enrolled_speakers=enrolled)
        d_elapsed = time.time() - d_start
        print(f"  ⏱ Diarization took {int(d_elapsed // 60)}m {int(d_elapsed % 60)}s")

        # Save transcript
        save_transcript(file, segments, speakers)

    total_elapsed = time.time() - start_time
    mins, secs = divmod(int(total_elapsed), 60)
    print(f"\n✅ Finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱ Total runtime: {mins}m {secs}s")


if __name__ == "__main__":
    main()