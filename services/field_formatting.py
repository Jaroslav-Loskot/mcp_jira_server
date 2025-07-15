from difflib import get_close_matches
from datetime import datetime


def normalize_date(value: str) -> str:
    """Try multiple date formats and return a normalized YYYY-MM-DD string."""
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return value


def fuzzy_match_value(user_value: str, allowed: list[str]) -> str | None:
    # fuzzy_match_value
    user_value = user_value.strip().lower()
    normalized_allowed = {a.lower(): a for a in allowed}

    matches = get_close_matches(user_value, normalized_allowed.keys(), n=1, cutoff=0.6)
    if matches:
        return normalized_allowed[matches[0]]


def format_value_for_field(field_schema: dict, value: any, current_values: list[str] = None, action: str = "replace") -> any:
    field_type = field_schema.get("schema", {}).get("type")
    items_type = field_schema["schema"].get("items")
    allowed_values = [opt["value"] for opt in field_schema.get("allowedValues", []) if "value" in opt]

    # --- Handle option and option-with-child ---
    if field_type in ["option", "option-with-child"]:
        matched = fuzzy_match_value(str(value), allowed_values)
        if not matched:
            raise ValueError(f"Invalid option value '{value}'. Allowed: {allowed_values}")
        return {"value": matched}

    # --- Handle array of options ---
    if field_type == "array" and items_type == "option":
        values = value if isinstance(value, list) else [value]
        current_values = current_values or []
        action = action.lower()

        updated = set(current_values)

        for v in values:
            match = fuzzy_match_value(str(v), allowed_values)
            if not match:
                raise ValueError(f"Invalid option value '{v}'. Allowed: {allowed_values}")

            if action == "add":
                updated.add(match)
            elif action == "remove":
                updated.discard(match)
            elif action == "replace":
                updated = {match}
            else:
                raise ValueError(f"Unknown action: {action}")

        return [{"value": v} for v in sorted(updated)]

    # --- Handle date ---
    if field_type == "date":
        return normalize_date(str(value))

    # --- String / Number ---
    if field_type in ["string", "number"]:
        return value

    return value  # fallback
