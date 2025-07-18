import json
import logging
import os

import boto3
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv(override=True)

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")

MODEL_ID = os.getenv("BEDROCK_MODEL_ID")  
# INFERENCE_ARN = os.getenv("BEDROCK_INFERENCE_CONFIG_ARN")  

bedrock_client = boto3.client(
    service_name="bedrock-runtime",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)


# --- Claude Generation via signed HTTP request ---
def call_claude(system_prompt: str, user_input: str) -> str:
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "temperature": 0.7,
        "system": system_prompt,  
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": user_input}]}
        ],
    }

    try:
        response = bedrock_client.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )

        raw = response["body"].read().decode()
        parsed = json.loads(raw)
        return parsed["content"][0]["text"].strip()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Claude request failed: {str(e)}")


# --- Titan Embedding ---
bedrock_client = boto3.client(
    service_name="bedrock-runtime",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)


def fetch_embedding(text: str) -> list[float]:
    """
    Fetch embedding using Amazon Titan model.
    """
    if not text.strip():
        raise HTTPException(status_code=400, detail="Input text is empty.")

    try:
        payload = {"inputText": text}
        response = bedrock_client.invoke_model(
            modelId="amazon.titan-embed-text-v2:0",
            body=json.dumps(payload),
            contentType="application/json",
            accept="application/json",
        )
        body = response["body"].read().decode()
        logging.info(f"Bedrock response body: {body}")
        result = json.loads(body)

        embedding = result.get("embedding")
        if not embedding or not isinstance(embedding, list):
            logging.error(f"Invalid embedding structure: {result}")
            raise HTTPException(
                status_code=500, detail="Embedding response invalid or missing."
            )

        return embedding

    except Exception as e:
        logging.error(f"Embedding generation failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Embedding generation failed: {str(e)}"
        )
