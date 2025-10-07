#!/usr/bin/env python3
"""
abstract_generator.py - Generate conversation abstracts using local LLMs via Ollama
"""

import json
import re
from typing import List, Dict, Optional
import requests
from pathlib import Path

# ======================
# CONFIGURATION
# ======================
OLLAMA_URL = "http://localhost:11434"  # Default Ollama endpoint
DEFAULT_MODEL = "qwen2.5:7b"  # Your local model
MAX_CONTEXT_LENGTH = 4000  # Tokens to send to the model
ABSTRACT_LENGTH = 150  # Target words for abstract
BULLET_POINTS = 5  # Number of key points to extract


# ======================
# OLLAMA CLIENT
# ======================
class OllamaClient:
    """Simple client for Ollama API"""

    def __init__(self, base_url: str = OLLAMA_URL, model: str = DEFAULT_MODEL):
        self.base_url = base_url
        self.model = model
        self.api_generate = f"{base_url}/api/generate"
        self.api_chat = f"{base_url}/api/chat"

    def is_available(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except:
            return False

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 500) -> str:
        """Generate text using Ollama"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "temperature": temperature,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "stop": ["</summary>", "\n\n\n"]
                }
            }

            response = requests.post(self.api_generate, json=payload)
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                print(f"Error from Ollama: {response.status_code}")
                return ""
        except Exception as e:
            print(f"Error calling Ollama: {e}")
            return ""

    def chat(self, messages: List[Dict], temperature: float = 0.7) -> str:
        """Chat completion using Ollama"""
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "stream": False
            }

            response = requests.post(self.api_chat, json=payload)
            if response.status_code == 200:
                return response.json()["message"]["content"]
            else:
                print(f"Error from Ollama: {response.status_code}")
                return ""
        except Exception as e:
            print(f"Error calling Ollama: {e}")
            return ""


# ======================
# ABSTRACT GENERATION
# ======================
class AbstractGenerator:
    """Generate abstracts and summaries from conversation transcripts"""

    def __init__(self, model: str = DEFAULT_MODEL):
        self.client = OllamaClient(model=model)
        if not self.client.is_available():
            print("⚠️ Warning: Ollama is not running. Start it with: ollama serve")

    def prepare_transcript(self, speakers: List[Dict]) -> str:
        """Convert speaker segments to readable text"""
        text_parts = []
        for segment in speakers:
            speaker = segment.get("speaker", "Unknown")
            text = segment.get("text", "").strip()
            if text:
                # Simplify speaker labels for the model
                if "SPEAKER_" in speaker:
                    speaker = f"Person {speaker.split('_')[1]}"
                text_parts.append(f"{speaker}: {text}")

        return "\n".join(text_parts)

    def truncate_to_context(self, text: str, max_words: int = 3000) -> str:
        """Truncate text to fit context window"""
        words = text.split()
        if len(words) > max_words:
            # Take first third and last two-thirds to capture beginning and recent context
            first_part = words[:max_words // 3]
            last_part = words[-(2 * max_words // 3):]
            return " ".join(first_part) + "\n[...]\n" + " ".join(last_part)
        return text

    def generate_abstract(self, speakers: List[Dict], method: str = "structured") -> Dict:
        """
        Generate an abstract from speaker segments

        Args:
            speakers: List of speaker segments with text
            method: "structured" for detailed analysis, "simple" for basic summary

        Returns:
            Dictionary with abstract, key points, topics, and action items
        """
        if not self.client.is_available():
            return self._fallback_abstract(speakers)

        # Prepare transcript
        transcript = self.prepare_transcript(speakers)
        transcript = self.truncate_to_context(transcript)

        if method == "structured":
            return self._generate_structured_abstract(transcript)
        else:
            return self._generate_simple_abstract(transcript)

    def _generate_structured_abstract(self, transcript: str) -> Dict:
        """Generate a structured abstract with multiple components"""

        # System message for chat mode
        system_msg = {
            "role": "system",
            "content": "You are an expert at analyzing conversations and creating concise, informative summaries. Focus on technical discussions, decisions made, and action items."
        }

        # User message with the transcript
        user_msg = {
            "role": "user",
            "content": f"""Analyze this conversation transcript and provide a structured summary.

TRANSCRIPT:
{transcript}

Please provide:
1. A brief abstract (2-3 sentences) summarizing the main topic and outcome
2. Key technical points discussed (3-5 bullet points)
3. Any decisions made or action items identified
4. Tools, technologies, or systems mentioned

Format your response as JSON with keys: abstract, key_points, decisions, tools"""
        }

        # Get response from Ollama
        response = self.client.chat([system_msg, user_msg], temperature=0.3)

        # Try to parse JSON response
        try:
            # Extract JSON from response (model might add explanation)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result
        except:
            pass

        # If JSON parsing fails, use structured prompting
        return self._generate_fallback_structured(transcript)

    def _generate_fallback_structured(self, transcript: str) -> Dict:
        """Fallback method using separate prompts for each component"""

        # Generate abstract
        abstract_prompt = f"""Summarize this conversation in 2-3 sentences. Focus on the main topic and outcome:

{transcript[:2000]}

Summary:"""
        abstract = self.client.generate(abstract_prompt, temperature=0.3, max_tokens=100)

        # Extract key points
        points_prompt = f"""List the 3-5 most important technical points from this conversation:

{transcript[:2000]}

Key points:"""
        points_text = self.client.generate(points_prompt, temperature=0.3, max_tokens=200)
        key_points = [p.strip() for p in points_text.split('\n') if p.strip() and len(p.strip()) > 10][:5]

        # Extract tools/technologies
        tools_prompt = f"""List all tools, technologies, and systems mentioned in this conversation (one per line):

{transcript[:2000]}

Tools mentioned:"""
        tools_text = self.client.generate(tools_prompt, temperature=0.1, max_tokens=100)
        tools = [t.strip() for t in tools_text.split('\n') if t.strip() and len(t.strip()) > 2]

        return {
            "abstract": abstract.strip(),
            "key_points": key_points,
            "decisions": [],  # Could add another prompt for this
            "tools": tools
        }

    def _generate_simple_abstract(self, transcript: str) -> Dict:
        """Generate a simple abstract - faster but less detailed"""

        prompt = f"""Write a brief summary of this conversation in 3-4 sentences. Include the main topic, key points discussed, and any conclusions or next steps:

{transcript[:3000]}

Summary:"""

        summary = self.client.generate(prompt, temperature=0.5, max_tokens=200)

        return {
            "abstract": summary.strip(),
            "key_points": [],
            "decisions": [],
            "tools": []
        }

    def _fallback_abstract(self, speakers: List[Dict]) -> Dict:
        """Fallback when Ollama is not available"""
        # Just use the first few segments
        text_parts = []
        for segment in speakers[:3]:
            text = segment.get("text", "").strip()
            if text:
                text_parts.append(text)

        abstract = " ".join(text_parts)[:200] + "..."

        return {
            "abstract": abstract,
            "key_points": [],
            "decisions": [],
            "tools": []
        }

    def generate_meeting_minutes(self, speakers: List[Dict], meeting_title: str = "Meeting") -> str:
        """Generate formatted meeting minutes"""

        if not self.client.is_available():
            return "Ollama not available for meeting minutes generation"

        transcript = self.prepare_transcript(speakers)
        transcript = self.truncate_to_context(transcript)

        prompt = f"""Convert this conversation into professional meeting minutes.

CONVERSATION:
{transcript}

Format as meeting minutes with:
- Meeting Overview
- Participants
- Key Discussion Points
- Decisions Made
- Action Items
- Next Steps

Meeting Minutes for {meeting_title}:"""

        minutes = self.client.generate(prompt, temperature=0.3, max_tokens=800)
        return minutes.strip()


# ======================
# INTEGRATION FUNCTIONS
# ======================
def generate_abstract_from_file(transcript_file: Path, method: str = "structured") -> Dict:
    """Generate abstract from a saved transcript file"""

    if not transcript_file.exists():
        print(f"Transcript file not found: {transcript_file}")
        return {}

    # Parse the markdown file to extract speakers and text
    speakers = []
    with open(transcript_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find the transcript section (after ---)
    in_transcript = False
    for line in lines:
        if line.strip() == "---":
            in_transcript = True
            continue

        if in_transcript and line.startswith("- **"):
            # Parse speaker line format: - **Speaker** [00:00-00:00]: Text
            match = re.match(r'- \*\*([^*]+)\*\* \[([^]]+)\]: (.+)', line)
            if match:
                speaker, time_range, text = match.groups()
                speakers.append({
                    "speaker": speaker,
                    "text": text.strip()
                })

    # Generate abstract
    generator = AbstractGenerator()
    return generator.generate_abstract(speakers, method=method)


def enhance_transcript_with_abstract(
        speakers: List[Dict],
        tools_mentioned: List[str] = None,
        method: str = "structured"
) -> Dict:
    """
    Generate an enhanced abstract for use in the main transcription script

    Args:
        speakers: List of speaker segments
        tools_mentioned: Optional list of tools already detected
        method: "structured" or "simple"

    Returns:
        Dictionary with abstract and metadata
    """
    generator = AbstractGenerator()
    result = generator.generate_abstract(speakers, method=method)

    # Merge with existing tools if provided
    if tools_mentioned and "tools" in result:
        existing_tools = set(tools_mentioned)
        new_tools = set(result.get("tools", []))
        result["tools"] = list(existing_tools | new_tools)

    return result


# ======================
# STANDALONE USAGE
# ======================
def main():
    """Example usage and testing"""
    import sys

    print("🤖 Abstract Generator using Ollama")
    print(f"   Model: {DEFAULT_MODEL}")
    print(f"   Endpoint: {OLLAMA_URL}")

    # Check Ollama availability
    client = OllamaClient()
    if not client.is_available():
        print("\n❌ Ollama is not running!")
        print("   Start it with: ollama serve")
        print("   Make sure you have the model: ollama pull qwen2.5:7b")
        sys.exit(1)

    print("✅ Ollama is running\n")

    # Test with a sample or file argument
    if len(sys.argv) > 1:
        transcript_file = Path(sys.argv[1])
        print(f"📄 Processing: {transcript_file}")
        result = generate_abstract_from_file(transcript_file)

        print("\n=== ABSTRACT ===")
        print(result.get("abstract", "No abstract generated"))

        if result.get("key_points"):
            print("\n=== KEY POINTS ===")
            for point in result["key_points"]:
                print(f"  • {point}")

        if result.get("tools"):
            print("\n=== TOOLS MENTIONED ===")
            for tool in result["tools"]:
                print(f"  - {tool}")
    else:
        # Test with sample data
        sample_speakers = [
            {"speaker": "Brad", "text": "A/B testing would be nice to have."},
            {"speaker": "Darrin",
             "text": "Yeah, Mautic has that A/B testing. We can set it up as a Docker instance in Coolify."},
            {"speaker": "Darrin",
             "text": "I identified Mailcow as a good mail server. It's a Docker image with all core elements needed."},
            {"speaker": "Brad", "text": "That would be easier than what I was looking at before."},
        ]

        generator = AbstractGenerator()
        result = generator.generate_abstract(sample_speakers)

        print("Sample Abstract:")
        print(result.get("abstract", "No abstract generated"))


if __name__ == "__main__":
    main()