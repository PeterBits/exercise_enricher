#!/usr/bin/env python3
"""
Exercise Enrichment Script
===========================
This script reads exercises from the mock JSON file, enriches them with AI-generated
information (primary muscle, title, description in English and Spanish), and saves
the processed exercises to separate output files.

It maintains a progress file to track which exercises have been processed,
allowing the script to resume from where it left off.

Supports multiple AI providers: Claude (Anthropic) and OpenAI (GPT-4)
"""

import json
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
import time
import getpass

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

# AI Provider constants
PROVIDER_CLAUDE = "claude"
PROVIDER_OPENAI = "openai"
PROVIDER_GROQ = "groq"

# Environment variable names
ENV_ANTHROPIC_KEY = "ANTHROPIC_API_KEY"
ENV_OPENAI_KEY = "OPEN_AI_API_KEY"
ENV_GROQ_KEY = "GROQ_API_KEY"


class AIProvider:
    """Base class for AI providers."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate_response(self, prompt: str) -> Optional[str]:
        """Generate a response from the AI provider."""
        raise NotImplementedError


class ClaudeProvider(AIProvider):
    """Claude (Anthropic) AI provider."""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        try:
            from anthropic import Anthropic

            self.client = Anthropic(api_key=api_key)
            self.model = "claude-3-5-sonnet-20241022"
        except ImportError:
            print(
                "Error: anthropic library not found. Install it with: pip install anthropic"
            )
            sys.exit(1)

    def generate_response(self, prompt: str) -> Optional[str]:
        """Generate a response using Claude."""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except Exception as e:
            raise Exception(f"Claude API error: {e}")


class OpenAIProvider(AIProvider):
    """OpenAI (GPT) AI provider."""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        try:
            from openai import OpenAI

            self.client = OpenAI(api_key=api_key)
            self.model = "gpt-4o"  # Using GPT-4o (most capable and cost-effective)
        except ImportError:
            print(
                "Error: openai library not found. Install it with: pip install openai"
            )
            sys.exit(1)

    def generate_response(self, prompt: str) -> Optional[str]:
        """Generate a response using OpenAI."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {e}")


class GroqProvider(AIProvider):
    """Groq AI provider (FREE)."""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        try:
            from groq import Groq

            self.client = Groq(api_key=api_key)
            # Using Llama 3.3 70B - Latest model available on Groq
            self.model = "llama-3.3-70b-versatile"
        except ImportError:
            print("Error: groq library not found. Install it with: pip install groq")
            sys.exit(1)

    def generate_response(self, prompt: str) -> Optional[str]:
        """Generate a response using Groq."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Groq API error: {e}")


class ExerciseEnricher:
    """Class to handle the enrichment of exercises using AI."""

    def __init__(self, provider: AIProvider, provider_name: str):
        """Initialize the enricher with AI provider."""
        self.provider = provider
        self.provider_name = provider_name
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
            "ai_provider": self.provider_name,
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
        """Create a prompt for AI to enrich the exercise."""
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

    def _parse_response(self, response_text: str) -> Optional[Dict[str, str]]:
        """Parse AI response and extract the enriched data."""
        try:
            # Remove potential markdown code blocks
            text = response_text.strip()
            if text.startswith("```"):
                # Remove markdown code blocks
                lines = text.split("\n")
                text = "\n".join(
                    line for line in lines if not line.strip().startswith("```")
                )
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
            print(f"Error parsing AI response as JSON: {e}")
            print(f"Response text: {response_text[:200]}...")
            return None

    def enrich_exercise(self, exercise: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send an exercise to AI for enrichment."""
        exercise_id = exercise.get("id")

        # Check if already processed
        if exercise_id in self.processed_ids:
            print(f"Skipping exercise {exercise_id} (already processed)")
            return None

        print(f"Processing exercise {exercise_id}...")

        try:
            # Create the prompt
            prompt = self._create_prompt(exercise)

            # Make the API call
            response_text = self.provider.generate_response(prompt)

            if not response_text:
                print(f"Failed to get response for exercise {exercise_id}")
                return None

            # Parse the response
            enriched_data = self._parse_response(response_text)

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
                "ai_provider": self.provider_name,
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
        print(f"AI Provider: {self.provider_name.upper()}")
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
        print(f"Please copy the exercises file to: {os.path.dirname(file_path)}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {e}")
        sys.exit(1)


def select_ai_provider() -> str:
    """Prompt user to select AI provider."""
    print("\n" + "=" * 60)
    print("Select AI Provider")
    print("=" * 60)
    print("\nAvailable AI providers:")
    print("  1. Claude (Anthropic) - Claude 3.5 Sonnet [PAID]")
    print("  2. OpenAI - GPT-4o [PAID]")
    print("  3. Groq - Llama 3.1 70B [FREE] ⭐")
    print()

    while True:
        choice = input("Enter your choice (1, 2, or 3): ").strip()
        if choice == "1":
            return PROVIDER_CLAUDE
        elif choice == "2":
            return PROVIDER_OPENAI
        elif choice == "3":
            return PROVIDER_GROQ
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


def get_api_key_from_env(provider: str) -> Optional[str]:
    """Try to get API key from environment variables."""
    if provider == PROVIDER_CLAUDE:
        return os.environ.get(ENV_ANTHROPIC_KEY)
    elif provider == PROVIDER_OPENAI:
        return os.environ.get(ENV_OPENAI_KEY)
    elif provider == PROVIDER_GROQ:
        return os.environ.get(ENV_GROQ_KEY)
    return None


def prompt_for_api_key(provider: str) -> str:
    """Prompt user for API key."""
    if provider == PROVIDER_CLAUDE:
        provider_name = "Claude (Anthropic)"
        url = "https://console.anthropic.com/settings/keys"
    elif provider == PROVIDER_OPENAI:
        provider_name = "OpenAI"
        url = "https://platform.openai.com/api-keys"
    elif provider == PROVIDER_GROQ:
        provider_name = "Groq (FREE)"
        url = "https://console.groq.com/keys"
    else:
        provider_name = "Unknown"
        url = ""

    print(f"\n{'='*60}")
    print(f"API Key Configuration")
    print(f"{'='*60}")
    print(f"Provider: {provider_name}\n")
    print("API key not found in .env file.\n")

    if url:
        print(f"Get your API key from: {url}")

    print()

    # Use getpass for secure input (won't show the key as user types)
    api_key = getpass.getpass("Enter your API key: ").strip()

    if not api_key:
        print("Error: API key cannot be empty")
        sys.exit(1)

    return api_key


def create_provider(provider_type: str, api_key: str) -> AIProvider:
    """Create an AI provider instance."""
    if provider_type == PROVIDER_CLAUDE:
        return ClaudeProvider(api_key)
    elif provider_type == PROVIDER_OPENAI:
        return OpenAIProvider(api_key)
    elif provider_type == PROVIDER_GROQ:
        return GroqProvider(api_key)
    else:
        raise ValueError(f"Unknown provider: {provider_type}")


def main():
    """Main function to run the enrichment process."""
    print(f"\n{'='*60}")
    print(f"Exercise Enrichment Script")
    print(f"{'='*60}\n")

    # Load .env file if python-dotenv is available
    if load_dotenv is not None:
        load_dotenv()

    # Select AI provider
    provider_type = select_ai_provider()

    # Try to get API key from environment, otherwise prompt user
    api_key = get_api_key_from_env(provider_type)
    if api_key:
        if provider_type == PROVIDER_CLAUDE:
            provider_name = "Claude (Anthropic)"
        elif provider_type == PROVIDER_OPENAI:
            provider_name = "OpenAI"
        elif provider_type == PROVIDER_GROQ:
            provider_name = "Groq (FREE)"
        else:
            provider_name = "Unknown"
        print(f"\n✓ API key loaded from .env file for {provider_name}")
    else:
        api_key = prompt_for_api_key(provider_type)

    # Create provider instance
    try:
        provider = create_provider(provider_type, api_key)
    except Exception as e:
        print(f"Error initializing AI provider: {e}")
        sys.exit(1)

    # Load exercises
    exercises = load_exercises(INPUT_FILE)

    # Initialize enricher
    enricher = ExerciseEnricher(provider, provider_type)

    # Process all exercises
    try:
        enricher.process_all_exercises(exercises, delay_seconds=1.0)
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user. Progress has been saved.")
        print(f"Run the script again to resume from where you left off.")
        sys.exit(0)


if __name__ == "__main__":
    main()
