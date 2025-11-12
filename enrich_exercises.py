#!/usr/bin/env python3
"""
Exercise Enrichment Script
===========================
This script reads exercises from the mock JSON file, enriches them with AI-generated
information (primary muscle, title, description in English and Spanish), and saves
the processed exercises to separate output files.

It maintains a progress file to track which exercises have been processed,
allowing the script to resume from where it left off.

Supports local LLM models from Hugging Face (optimized for CPU)
"""

import json
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
import time
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

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

# Local model constants
MODELS_DIR = os.path.join(BASE_DIR, "models")  # Directory to cache models

# Available models optimized for CPU with low RAM
AVAILABLE_MODELS = {
    "qwen-1.5b": {
        "name": "Qwen/Qwen2-1.5B-Instruct",
        "description": "Qwen 1.5B - Rápido y ligero (1.5B parámetros) [RECOMENDADO]",
        "ram_requirement": "~3GB RAM",
        "speed": "Rápido en CPU",
    },
    "tinyllama-1.1b": {
        "name": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "description": "TinyLlama 1.1B - El más rápido (1.1B parámetros)",
        "ram_requirement": "~2.5GB RAM",
        "speed": "Muy rápido en CPU",
    },
    "phi3-mini": {
        "name": "microsoft/Phi-3-mini-4k-instruct",
        "description": "Phi-3 Mini - Mejor calidad pero más lento (3.8B parámetros)",
        "ram_requirement": "~5-6GB RAM",
        "speed": "Lento en CPU",
    },
}


class LocalLLMProvider:
    """Local LLM provider using Hugging Face transformers (optimized for CPU)."""

    def __init__(self, model_id: str, model_name: str):
        """Initialize the local LLM provider."""
        self.model_id = model_id
        self.model_name = model_name
        self.pipeline = None

        print(f"\n{'='*60}")
        print(f"Inicializando modelo local: {model_name}")
        print(f"{'='*60}\n")

        try:
            from transformers import pipeline, AutoTokenizer
            import torch

            # Check if running on CPU
            device = "cpu"
            print(f"Dispositivo: {device.upper()}")
            print("Descargando/cargando modelo (esto puede tardar la primera vez)...\n")

            # Create cache directory if it doesn't exist
            os.makedirs(MODELS_DIR, exist_ok=True)

            # Load tokenizer first to check if model exists
            tokenizer = AutoTokenizer.from_pretrained(
                model_id,
                cache_dir=MODELS_DIR,
                trust_remote_code=True
            )
            
            # Set pad token if not exists
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token

            # Create text generation pipeline with CPU optimizations
            self.pipeline = pipeline(
                "text-generation",
                model=model_id,
                tokenizer=tokenizer,
                device=device,
                torch_dtype=torch.float32,  # Use float32 for CPU
                trust_remote_code=True,
                model_kwargs={
                    "low_cpu_mem_usage": True,  # Optimize memory usage
                    "cache_dir": MODELS_DIR,  # Move cache_dir to model_kwargs
                    "max_position_embeddings": 4096,  # Increase max sequence length
                }
            )

            print(f"✓ Modelo cargado exitosamente!\n")

        except ImportError as e:
            print(f"Error: Falta instalar dependencias requeridas")
            print(f"Ejecuta: pip install -r requirements.txt")
            sys.exit(1)
        except Exception as e:
            print(f"Error al cargar el modelo: {e}")
            print(f"\nIntenta con un modelo más pequeño o verifica tu conexión a internet.")
            sys.exit(1)

    def generate_response(self, prompt: str) -> Optional[str]:
        """Generate a response using the local LLM."""
        try:
            # Different chat templates for different models
            if "Qwen" in self.model_id:
                messages = [{"role": "user", "content": prompt}]
                formatted_prompt = self.pipeline.tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True
                )
            elif "Phi-3" in self.model_id:
                formatted_prompt = f"<|user|>\n{prompt}<|end|>\n<|assistant|>\n"
            elif "TinyLlama" in self.model_id:
                formatted_prompt = f"<|user|>\n{prompt}</s>\n<|assistant|>\n"
            else:
                formatted_prompt = prompt

            # Check if prompt is too long and truncate if necessary
            max_prompt_length = 1800  # Leave room for generated tokens
            tokens = self.pipeline.tokenizer.encode(formatted_prompt)
            if len(tokens) > max_prompt_length:
                # Truncate prompt to fit within limits
                truncated_tokens = tokens[:max_prompt_length]
                formatted_prompt = self.pipeline.tokenizer.decode(truncated_tokens, skip_special_tokens=True)
                print(f"⚠️  Prompt truncated to fit model limits ({len(tokens)} -> {len(truncated_tokens)} tokens)")

            # Generate response with reduced token count
            outputs = self.pipeline(
                formatted_prompt,
                max_new_tokens=800,  # Reduced from 1200 to leave more room for prompt
                do_sample=True,
                temperature=0.5,  # Lower temperature for more focused responses
                top_p=0.9,
                pad_token_id=self.pipeline.tokenizer.eos_token_id,
                eos_token_id=self.pipeline.tokenizer.eos_token_id,
                truncation=True,  # Enable truncation
            )

            # Extract generated text
            generated_text = outputs[0]["generated_text"]

            # Remove the prompt from the response
            if generated_text.startswith(formatted_prompt):
                response = generated_text[len(formatted_prompt):].strip()
            else:
                response = generated_text.strip()

            # For Phi-3, remove the end token if present
            if "<|end|>" in response:
                response = response.split("<|end|>")[0].strip()

            return response

        except Exception as e:
            raise Exception(f"Error generando respuesta del modelo local: {e}")


class ExerciseEnricher:
    """Class to handle the enrichment of exercises using AI."""

    def __init__(self, provider: LocalLLMProvider, model_name: str):
        """Initialize the enricher with local LLM provider."""
        self.provider = provider
        self.model_name = model_name
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
            "model": self.model_name,
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

        # Get existing names (limit to avoid long prompts)
        existing_info = []
        for trans in translations[:2]:  # Limit to first 2 translations
            name = trans.get("name", "")
            lang = trans.get("language", "")
            if name:
                existing_info.append(f"- Name (lang {lang}): {name}")
            # Skip descriptions to save space

        # Create a shorter, more concise prompt to avoid token limits
        prompt = f"""Fitness expert: Enrich this exercise info as JSON.

Exercise: {exercise_id}
Category: {category}
Equipment: {', '.join(equipment) if equipment else 'None'}

{chr(10).join(existing_info[:2]) if existing_info else 'No existing info'}

Return JSON with this structure:
{{
  "primary_muscle": {{"name": "Spanish", "name_en": "English"}},
  "translations": [
    {{"name": "Title", "description": "2-3 sentences", "language": 2, "aliases": ["Alt1", "Alt2"], "notes": ["Tip1", "Tip2"]}},
    {{"name": "Título", "description": "2-3 oraciones", "language": 4, "aliases": ["Alt1", "Alt2"], "notes": ["Consejo1", "Consejo2"]}}
  ]
}}

Rules: language=int (2=English, 4=Spanish), include 2+ aliases and notes.
- Do not include any markdown formatting, code blocks, or additional text
- Return only the raw JSON object"""

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

            # Validate primary_muscle structure
            if "primary_muscle" not in data or not isinstance(data["primary_muscle"], dict):
                print("Error: Missing or invalid 'primary_muscle' object in response")
                return None

            muscle = data["primary_muscle"]
            if "name" not in muscle or "name_en" not in muscle:
                print("Error: 'primary_muscle' must have both 'name' and 'name_en' properties")
                return None

            # Validate translations structure
            if "translations" not in data or not isinstance(data["translations"], list):
                print("Error: Missing or invalid 'translations' array in response")
                return None

            if len(data["translations"]) != 2:
                print("Error: 'translations' array must contain exactly 2 translations (English and Spanish)")
                return None

            # Validate each translation
            for idx, translation in enumerate(data["translations"]):
                if not isinstance(translation, dict):
                    print(f"Error: Translation {idx} is not a valid object")
                    return None

                # Check required fields
                required_fields = ["name", "description", "language", "aliases", "notes"]
                for field in required_fields:
                    if field not in translation:
                        print(f"Error: Translation {idx} missing required field '{field}'")
                        return None

                # Validate language is integer (2 or 4)
                if not isinstance(translation["language"], int) or translation["language"] not in [2, 4]:
                    print(f"Error: Translation {idx} has invalid language (must be integer 2 or 4)")
                    return None

                # Validate aliases is array
                if not isinstance(translation["aliases"], list):
                    print(f"Error: Translation {idx} 'aliases' must be an array")
                    return None

                # Validate notes is array
                if not isinstance(translation["notes"], list):
                    print(f"Error: Translation {idx} 'notes' must be an array")
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
                "model": self.model_name,
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
        print(f"Modelo: {self.model_name}")
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


def select_model() -> tuple[str, str]:
    """Prompt user to select a local model."""
    print("\n" + "=" * 60)
    print("Selecciona un Modelo Local de LLM")
    print("=" * 60)
    print("\nModelos disponibles optimizados para CPU con poca RAM:")
    print()

    model_keys = list(AVAILABLE_MODELS.keys())
    for idx, key in enumerate(model_keys, 1):
        model_info = AVAILABLE_MODELS[key]
        print(f"  {idx}. {model_info['description']}")
        print(f"     RAM requerida: {model_info['ram_requirement']}")
        print(f"     Velocidad: {model_info['speed']}")
        print()

    while True:
        choice = input(f"Ingresa tu elección (1-{len(model_keys)}): ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(model_keys):
                selected_key = model_keys[idx]
                model_id = AVAILABLE_MODELS[selected_key]["name"]
                model_name = selected_key
                return model_id, model_name
            else:
                print(f"Opción inválida. Por favor ingresa un número entre 1 y {len(model_keys)}.")
        except ValueError:
            print(f"Opción inválida. Por favor ingresa un número entre 1 y {len(model_keys)}.")


def create_local_provider(model_id: str, model_name: str) -> LocalLLMProvider:
    """Create a local LLM provider instance."""
    try:
        return LocalLLMProvider(model_id, model_name)
    except Exception as e:
        raise Exception(f"Error al crear el proveedor de modelo local: {e}")


def main():
    """Main function to run the enrichment process."""
    print(f"\n{'='*60}")
    print(f"Exercise Enrichment Script - Modelos Locales")
    print(f"{'='*60}\n")

    # Select local model
    model_id, model_name = select_model()

    # Create local provider instance
    try:
        provider = create_local_provider(model_id, model_name)
    except Exception as e:
        print(f"Error al inicializar el modelo local: {e}")
        sys.exit(1)

    # Load exercises
    exercises = load_exercises(INPUT_FILE)

    # Initialize enricher
    enricher = ExerciseEnricher(provider, model_name)

    # Process all exercises
    try:
        # Delay can be 0 or very low since we're running locally
        enricher.process_all_exercises(exercises, delay_seconds=0.5)
    except KeyboardInterrupt:
        print("\n\nProceso interrumpido por el usuario. El progreso ha sido guardado.")
        print(f"Ejecuta el script nuevamente para continuar desde donde lo dejaste.")
        sys.exit(0)


if __name__ == "__main__":
    main()
