import re
import json
import logging
from datetime import datetime
from typing import Any
from utils.bedrock_wrapper import call_claude, fetch_embedding
from services.field_mapping import FIELD_LABEL_TO_ID

# Load precomputed field embeddings
with open("utils/field_embeddings.json", "r") as f:
    FIELD_EMBEDDINGS = json.load(f)


# --- Helper Functions ---
def normalize_date(value: str) -> str:
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return value


def fuzzy_match_value(user_value: str, allowed: list[str]) -> str | None:
    from difflib import get_close_matches
    matches = get_close_matches(user_value.strip().lower(), [a.lower() for a in allowed], n=1, cutoff=0.6)
    if matches:
        for original in allowed:
            if original.lower() == matches[0]:
                return original
    return None


def resolve_field_id_fuzzy(user_label: str, instruction: str) -> tuple[str, str] | None:
    logging.info(f"🔍 [START] Trying to resolve field for user_label: '{user_label}'")

    try:
        logging.info(f"📦 Generating embedding for: '{user_label}'")
        user_embedding = fetch_embedding(user_label)
        logging.info(f"🔢 Embedding shape: {len(user_embedding)} values")

        distances = []
        for record in FIELD_EMBEDDINGS:
            label = record["field_label"]
            field_id = record["field_id"]
            embedding = record["embedding"]

            dot = sum(a * b for a, b in zip(user_embedding, embedding))
            norm_a = sum(a * a for a in user_embedding) ** 0.5
            norm_b = sum(b * b for b in embedding) ** 0.5
            similarity = dot / (norm_a * norm_b + 1e-6)
            distance = 1 - similarity  # lower = closer

            distances.append((distance, label, field_id))

        distances.sort()
        top_5 = distances[:5]

        logging.info("🔝 Top 5 closest field labels:")
        for dist, label, _ in top_5:
            logging.info(f" → {label} (distance: {dist:.4f})")

        labels_only = [label for _, label, _ in top_5]
        prompt = (
            f"You are an assistant that helps identify the best matching Jira field.\n"
            f"The user instruction is: \"{instruction}\"\n"
            f"Which of the following field labels best matches this instruction?\n"
            + "\n".join(f"- {label}" for label in labels_only) +
            "\n\nRespond with just the best matching label."
        )

        chosen_label = call_claude(
            system_prompt="You help map user instructions to correct Jira field labels.",
            user_input=prompt
        ).strip()

        logging.info(f"🤖 LLM selected: '{chosen_label}'")

        for _, label, fid in top_5:
            if label.lower() == chosen_label.lower():
                return label, fid

        logging.warning(f"❌ LLM selected label '{chosen_label}' not found in top-5.")
        return None

    except Exception as e:
        logging.warning(f"⚠️ Embedding-based field resolution failed: {e}")
        return None



def format_value_for_field(field_schema: dict, value: Any, current_values: Any = None, action: str = "replace") -> Any:
    field_type = field_schema.get("schema", {}).get("type")

    if field_type in ["option", "option-with-child"]:
        allowed = [opt["value"] for opt in field_schema.get("allowedValues", []) if "value" in opt]
        matched = fuzzy_match_value(str(value), allowed)
        if not matched:
            raise ValueError(f"Invalid option value '{value}'. Allowed: {allowed}")
        return {"value": matched}

    if field_type == "array" and field_schema["schema"].get("items") == "option":
        allowed = [opt["value"] for opt in field_schema.get("allowedValues", []) if "value" in opt]
        values = value if isinstance(value, list) else [value]
        updated = set(current_values or [])

        for v in values:
            match = fuzzy_match_value(str(v), allowed)
            if not match:
                raise ValueError(f"Invalid option value '{v}'. Allowed: {allowed}")

            if action == "add":
                updated.add(match)
            elif action == "remove":
                updated.discard(match)
            elif action == "replace":
                updated = {match}
            else:
                raise ValueError(f"Unknown action: {action}")

        return [{"value": v} for v in sorted(updated)]

    if field_type == "date":
        return normalize_date(str(value))

    if field_type in ["string", "number"]:
        return value

    return value
