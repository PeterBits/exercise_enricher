#!/usr/bin/env python3
"""
Exercise Enrichment Script
===========================
This script reads exercises from the mock JSON file, enriches them with AI-generated
information (primary muscle, title, description in English and Spanish), and saves
the processed exercises to separate output files.

It maintains a progress file to track which exercises have been processed,
allowing the script to resume from where it left off.
"""

import json
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
import time

# Try importing the Anthropic library
try:
    from anthropic import Anthropic
except ImportError:
    print("Error: anthropic library not found. Install it with: pip install anthropic")
    sys.exit(1)

# Try importing python-dotenv for .env file support
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "input", "exercicies_mock.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "output", "enriched_exercises.json")
PROGRESS_FILE = os.path.join(BASE_DIR, "output", "processing_progress.json")

# API Configuration
API_KEY_ENV = "ANTHROPIC_API_KEY"
MODEL_NAME = "claude-3-5-sonnet-20241022"  # Using the latest Sonnet model


class ExerciseEnricher:
    """Class to handle the enrichment of exercises using Claude AI."""

    def __init__(self, api_key: str):
        """Initialize the enricher with API credentials."""
        self.client = Anthropic(api_key=api_key)
        self.processed_ids = self._load_progress()
        self.enriched_exercises = self._load_existing_output()

    def _load_progress(self) -> List[int]:
        """Load the list of already processed exercise IDs."""
        if os.path.exists(PROGRESS_FILE):
            try:
                with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("processed_exercise_ids", [])
            except Exception as e:
                print(f"Warning: Could not load progress file: {e}")
        return []

    def _save_progress(self, exercise_id: int):
        """Save progress after processing an exercise."""
        if exercise_id not in self.processed_ids:
            self.processed_ids.append(exercise_id)

        progress_data = {
            "processed_exercise_ids": self.processed_ids,
            "last_updated": datetime.now().isoformat(),
            "total_processed": len(self.processed_ids),
        }

        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)

            with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
                json.dump(progress_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving progress: {e}")

    def _load_existing_output(self) -> List[Dict[str, Any]]:
        """Load existing enriched exercises if the output file exists."""
        if os.path.exists(OUTPUT_FILE):
            try:
                with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load existing output file: {e}")
        return []

    def _save_enriched_exercise(self, enriched_exercise: Dict[str, Any]):
        """Append a newly enriched exercise to the output file."""
        self.enriched_exercises.append(enriched_exercise)

        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(self.enriched_exercises, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving enriched exercise: {e}")

    def _create_prompt(self, exercise: Dict[str, Any]) -> str:
        """Create a prompt for Claude to enrich the exercise."""
        # Extract existing information
        exercise_id = exercise.get("id", "Unknown")
        category = exercise.get("category", {}).get("name", "Unknown")
        equipment = [eq.get("name", "") for eq in exercise.get("equipment", [])]
        translations = exercise.get("translations", [])

        # Get existing names and descriptions
        existing_info = []
        for trans in translations:
            name = trans.get("name", "")
            desc = trans.get("description", "")
            lang = trans.get("language", "")
            if name:
                existing_info.append(f"- Name (lang {lang}): {name}")
            if desc:
                # Remove HTML tags from description
                import re

                clean_desc = re.sub(r"<[^>]+>", "", desc)
                existing_info.append(f"- Description (lang {lang}): {clean_desc}")

        prompt = f"""You are a fitness expert. I need you to enrich the following exercise information.

Exercise ID: {exercise_id}
Category: {category}
Equipment: {', '.join(equipment) if equipment else 'None specified'}

Existing information:
{chr(10).join(existing_info) if existing_info else 'No existing translations'}

Please provide the following information in a structured JSON format:

1. **Primary Muscle**: The main muscle group targeted by this exercise (e.g., "Chest", "Biceps", "Quadriceps", "Core", "Shoulders")
2. **Title (English)**: A clear, concise name for the exercise
3. **Title (Spanish)**: The same title translated to Spanish
4. **Description (English)**: A detailed description of how to perform the exercise (2-4 sentences, including proper form and key points)
5. **Description (Spanish)**: The same description translated to Spanish

Return ONLY a valid JSON object with this exact structure:
{{
  "primary_muscle": "muscle name here",
  "title_en": "exercise title in English",
  "title_es": "exercise title in Spanish",
  "description_en": "detailed description in English",
  "description_es": "detailed description in Spanish"
}}

Do not include any markdown formatting, code blocks, or additional text. Return only the raw JSON object."""

        return prompt

    def _parse_claude_response(self, response_text: str) -> Optional[Dict[str, str]]:
        """Parse Claude's response and extract the enriched data."""
        try:
            # Remove potential markdown code blocks
            text = response_text.strip()
            if text.startswith("```"):
                # Remove markdown code blocks
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

            # Try to parse the response as JSON
            data = json.loads(text)

            # Validate that all required fields are present
            required_fields = [
                "primary_muscle",
                "title_en",
                "title_es",
                "description_en",
                "description_es",
            ]
            for field in required_fields:
                if field not in data or not data[field]:
                    print(f"Error: Missing or empty field '{field}' in response")
                    return None

            return data
        except json.JSONDecodeError as e:
            print(f"Error parsing Claude response as JSON: {e}")
            print(f"Response text: {response_text[:200]}...")
            return None

    def enrich_exercise(self, exercise: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send an exercise to Claude for enrichment."""
        exercise_id = exercise.get("id")

        # Check if already processed
        if exercise_id in self.processed_ids:
            print(f"Skipping exercise {exercise_id} (already processed)")
            return None

        print(f"Processing exercise {exercise_id}...")

        try:
            # Create the prompt
            prompt = self._create_prompt(exercise)

            # Make the API call to Claude
            message = self.client.messages.create(
                model=MODEL_NAME,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract the response text
            response_text = message.content[0].text

            # Parse the response
            enriched_data = self._parse_claude_response(response_text)

            if not enriched_data:
                print(f"Failed to enrich exercise {exercise_id}")
                return None

            # Combine original exercise with enriched data
            enriched_exercise = {
                "id": exercise_id,
                "uuid": exercise.get("uuid"),
                "original_category": exercise.get("category"),
                "original_equipment": exercise.get("equipment"),
                "original_translations": exercise.get("translations", []),
                "enriched_data": enriched_data,
                "processed_at": datetime.now().isoformat(),
            }

            # Save progress
            self._save_progress(exercise_id)
            self._save_enriched_exercise(enriched_exercise)

            print(f"✓ Successfully enriched exercise {exercise_id}")
            return enriched_exercise

        except Exception as e:
            print(f"Error enriching exercise {exercise_id}: {e}")
            return None

    def process_all_exercises(
        self, exercises: List[Dict[str, Any]], delay_seconds: float = 1.0
    ):
        """Process all exercises with a delay between requests."""
        total = len(exercises)
        processed = len(self.processed_ids)
        remaining = total - processed

        print(f"\n{'='*60}")
        print(f"Exercise Enrichment Progress")
        print(f"{'='*60}")
        print(f"Total exercises: {total}")
        print(f"Already processed: {processed}")
        print(f"Remaining: {remaining}")
        print(f"{'='*60}\n")

        if remaining == 0:
            print("All exercises have been processed!")
            return

        for idx, exercise in enumerate(exercises, 1):
            exercise_id = exercise.get("id")

            if exercise_id in self.processed_ids:
                continue

            print(f"\n[{idx}/{total}] Processing exercise {exercise_id}...")

            self.enrich_exercise(exercise)

            # Add a delay to avoid rate limiting
            if idx < total:
                time.sleep(delay_seconds)

        print(f"\n{'='*60}")
        print(f"Processing complete!")
        print(f"Total enriched: {len(self.processed_ids)}")
        print(f"Output file: {OUTPUT_FILE}")
        print(f"Progress file: {PROGRESS_FILE}")
        print(f"{'='*60}\n")


def load_exercises(file_path: str) -> List[Dict[str, Any]]:
    """Load exercises from the JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            exercises = json.load(f)
            print(f"Loaded {len(exercises)} exercises from {file_path}")
            return exercises
    except FileNotFoundError:
        print(f"Error: Input file not found: {file_path}")
        print(
            f"Please copy the exercises file to: {os.path.dirname(file_path)}"
        )
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {e}")
        sys.exit(1)


def main():
    """Main function to run the enrichment process."""
    print(f"\n{'='*60}")
    print(f"Exercise Enrichment Script")
    print(f"{'='*60}\n")

    # Load .env file if python-dotenv is available
    if load_dotenv is not None:
        load_dotenv()

    # Check for API key
    api_key = os.environ.get(API_KEY_ENV)
    if not api_key:
        print(f"Error: {API_KEY_ENV} environment variable not set")
        print(f"Please set your Anthropic API key:")
        print(f"  export {API_KEY_ENV}='your-api-key-here'  # Linux/Mac")
        print(f"  set {API_KEY_ENV}=your-api-key-here       # Windows CMD")
        print(
            f"  $env:{API_KEY_ENV}='your-api-key-here'   # Windows PowerShell"
        )
        sys.exit(1)

    # Load exercises
    exercises = load_exercises(INPUT_FILE)

    # Initialize enricher
    enricher = ExerciseEnricher(api_key)

    # Process all exercises
    try:
        enricher.process_all_exercises(exercises, delay_seconds=1.0)
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user. Progress has been saved.")
        print(f"Run the script again to resume from where you left off.")
        sys.exit(0)


if __name__ == "__main__":
    main()
