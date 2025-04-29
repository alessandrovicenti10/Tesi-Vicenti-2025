"""

Key changes
-----------
* **Structured messages** – system ➜ assistant (rules) ➜ user (data)
  instead of one long user prompt.
* **response_format="json_object"** – forces strict JSON from the
  model, eliminating brittle post‑processing.
* **Explicit output schema** – reiterated in both the rules and the
  OpenAI parameter, so the model can’t drift.
* **Hidden chain‑of‑thought** – the model is asked to reason
  internally but reveal **only** the JSON object.
* **Retry with exponential back‑off** – robustness for batch runs.
* **Parametrised model / temperature** – easy to experiment.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Union

import openai
from tenacity import retry, wait_random_exponential, stop_after_attempt

# --------------------------------------------------------------------------- #
# Configuration – replace with env vars or CLI flags as needed
# --------------------------------------------------------------------------- #
API_KEY: str = "APIKEY" 
MODEL: str = "gpt-4.1-2025-04-14"

openai_client = openai.OpenAI(api_key=API_KEY)


# --------------------------------------------------------------------------- #
# Prompt builder
# --------------------------------------------------------------------------- #

def _build_messages(product_data: Dict[str, Any]) -> List[Dict[str, str]]:
    """Return a list of messages ready for chat.completions.create."""

    SYSTEM_PROMPT = (
        "You are a senior Life‑Cycle‑Assessment (LCA) practitioner specialising in "
        "cradle‑to‑grave carbon footprinting of electronic devices. "
        "Your task is to prepare a concise JSON disclosure for a public sustainability database."
    )

    RULES = (
        "# OBJECTIVE\n"
        "Provide the best available estimate of the cradle‑to‑grave greenhouse‑gas emissions (kg CO₂e).\n\n"
        "# INSTRUCTIONS\n"
        "1. **Official data first** – look for Environmental Product Declarations (EPDs) or official carbon‑footprint reports that exactly match the product. If found, use those values.\n"
        "2. **Fallback estimation** – if no official data exists, estimate following these standards *in order of precedence*: GHG‑Protocol Product Standard ▶ ISO 14040/44 ▶ PAS 2050 ▶ ISO/TS 14067.\n"
        "3. **Include all lifecycle stages** – materials, manufacturing, transport, use‑phase energy (assume 4‑year EU grid mix if unspecified) and end‑of‑life.\n"
        "4. **Be transparent** – state clearly whether you used *Manufacturer report* or *Estimated* values and cite external datasets (e.g. ecoinvent v3.10).\n"
        "5. **Think step‑by‑step internally** but **output only** the JSON described below.\n\n"
        "# OUTPUT FORMAT\n"
        "Return *exactly* one JSON object with two keys:\n"
        "  • `co2e_kg`   – number (float)\n"
        "  • `explanation` – string (≤ 300 words)\n"
        "No markdown, no additional keys, no extra text."
    )

    product_block = (
        "# PRODUCT DATA\n"
        "```json\n"
        f"{json.dumps(product_data, ensure_ascii=False, indent=2)}\n"
        "```"
    )

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "assistant", "content": RULES},
        {"role": "user", "content": product_block},
    ]


# --------------------------------------------------------------------------- #
# LLM invocation with retry logic
# --------------------------------------------------------------------------- #

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def _call_llm(messages: List[Dict[str, str]], *, model: str = MODEL, temperature: float = 0.0) -> str:
    """Call the chat completion endpoint and return the raw JSON string."""

    response = openai_client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        response_format={"type": "json_object"},
    )

    return response.choices[0].message.content.strip()


# --------------------------------------------------------------------------- #
# Public helper
# --------------------------------------------------------------------------- #

def estimate_co2_for_product(product_data: Dict[str, Any], *, llm_model: str = MODEL) -> Dict[str, Any]:
    """Estimate the carbon footprint for a single product."""

    messages = _build_messages(product_data)

    try:
        raw = _call_llm(messages, model=llm_model)
        result = json.loads(raw)

        if not (
            isinstance(result, dict)
            and "co2e_kg" in result
            and "explanation" in result
        ):
            raise ValueError("Schema mismatch – JSON keys missing.")

        return result

    except Exception as exc:
        return {
            "co2e_kg": None,
            "explanation": f"Error: {exc}",
        }


# --------------------------------------------------------------------------- #
# Batch driver / CLI
# --------------------------------------------------------------------------- #

def main(num_rows: int = 26, dataset_path: str = "../dataset/Multi_products.jsonl") -> None:
    products: List[Dict[str, Any]] = []

    with open(dataset_path, "r", encoding="utf-8") as fp:
        for i, line in enumerate(fp):
            if i >= num_rows:
                break
            products.append(json.loads(line))

    results: List[Dict[str, Union[str, float, None]]] = []

    for product in products:
        res = estimate_co2_for_product(product)
        results.append(
            {
                "product_name": product.get("title", "Unknown"),
                "co2e_kg": res.get("co2e_kg"),
                "explanation": res.get("explanation"),
            }
        )

    out_path = Path("CookBookgpt4.1_4.json")
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Saved {len(results)} results to {out_path.resolve()}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Estimate product CO₂e using GPT‑4.1")
    parser.add_argument("--rows", type=int, default=26, help="Number of rows to process")
    parser.add_argument("--dataset", type=str, default="../dataset/Multi_products.jsonl", help="Path to .jsonl dataset")
    parser.add_argument("--model", type=str, default=MODEL, help="Chat model name")
    args = parser.parse_args()

    MODEL = args.model  # override global if provided
    main(args.rows, args.dataset)
