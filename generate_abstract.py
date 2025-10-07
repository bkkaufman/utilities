import re
import os
import argparse
from pathlib import Path


def generate_abstract(transcript_file, debug=False):
    """Generate an abstract from a transcript markdown file."""

    if debug:
        print(f"📄 Processing: {os.path.basename(transcript_file)}")

    # Read the transcript file
    with open(transcript_file, 'r', encoding='utf-8') as file:
        content = file.read()
        lines = content.split('\n')

    if debug:
        print(f"   DEBUG: Parsing {len(lines)} lines")

    # Extract title from filename
    title = os.path.splitext(os.path.basename(transcript_file))[0]
    if debug:
        print(f"   DEBUG: Found title: {title}")

    # Try different patterns to find speakers
    speaker_patterns = [
        r'^([A-Z][a-z]+):',  # Simple "Name:" pattern
        r'^([A-Z][a-z]+ [A-Z][a-z]+):',  # "First Last:" pattern
        r'^\*\*([A-Z][a-z]+(?: [A-Z][a-z]+)?)\*\*:',  # "**Name**:" pattern
        r'^([A-Z][a-z]+(?: [A-Z][a-z]+)?):',  # Combined first and first last pattern
        r'^Speaker \d+:',  # "Speaker 1:" pattern
        r'^\d+:\d+\s+([A-Z][a-z]+(?: [A-Z][a-z]+)?):',  # Timestamp followed by name
    ]

    speakers = set()
    dialogue = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Try each pattern to find speakers
        speaker_found = False
        for pattern in speaker_patterns:
            match = re.match(pattern, line)
            if match:
                speaker = match.group(1)
                speakers.add(speaker)
                # Extract dialogue content (everything after the speaker label)
                dialogue_content = re.sub(pattern, '', line).strip()
                dialogue.append((speaker, dialogue_content))
                speaker_found = True
                break

        # If no speaker pattern matched but there's content, it might be continuation
        if not speaker_found and dialogue and line:
            # Append to the last speaker's dialogue
            last_speaker, last_dialogue = dialogue[-1]
            dialogue[-1] = (last_speaker, f"{last_dialogue} {line}")

    if not speakers:
        if debug:
            print("   ⚠️ No speaker data found, skipping...")
        return None

    if debug:
        print(f"   DEBUG: Found speakers: {', '.join(speakers)}")
        print(f"   DEBUG: Extracted {len(dialogue)} dialogue entries")

    # Generate abstract by combining key dialogue points
    abstract_lines = []

    # Get the first few dialogue entries as a summary
    for speaker, text in dialogue[:5]:
        abstract_lines.append(f"{speaker}: {text[:100]}...")

    abstract = "\n".join(abstract_lines)

    # Create the abstract file
    abstract_file = os.path.join(
        os.path.dirname(transcript_file),
        f"{title}_abstract.md"
    )

    with open(abstract_file, 'w', encoding='utf-8') as file:
        file.write(f"# {title} - Abstract\n\n")
        file.write(f"## Speakers: {', '.join(speakers)}\n\n")
        file.write("## Summary\n\n")
        file.write(abstract)

    if debug:
        print(f"   ✅ Abstract generated: {os.path.basename(abstract_file)}")

    return abstract_file


def main():
    parser = argparse.ArgumentParser(description="Generate abstracts from transcript markdown files.")
    parser.add_argument("transcript_file", help="Path to the transcript markdown file")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    args = parser.parse_args()

    generate_abstract(args.transcript_file, args.debug)


if __name__ == "__main__":
    main()