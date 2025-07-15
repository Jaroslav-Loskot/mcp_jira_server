import logging
import sys
import os
import json
from bedrock_wrapper import fetch_embedding
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.field_mapping import FIELD_LABEL_TO_ID
from utils.bedrock_wrapper import fetch_embedding


load_dotenv()

OUTPUT_FILE = "field_embeddings.json"

def generate_embeddings():
    result = []

    for label, field_id in FIELD_LABEL_TO_ID.items():
        try:
            print(f"🔄 Embedding: {label}")
            embedding = fetch_embedding(label)

            result.append({
                "field_label": label,
                "field_id": field_id,
                "embedding": embedding
            })

        except Exception as e:
            logging.warning(f"❌ Failed to embed '{label}': {e}")

    with open(OUTPUT_FILE, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n✅ Done! Embeddings saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_embeddings()
