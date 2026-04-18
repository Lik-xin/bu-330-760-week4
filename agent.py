"""Math agent that solves questions using tools in a ReAct loop."""

import json
import math
import os
from pathlib import Path
import re
import time

from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelHTTPError
from calculator import calculate

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)

# Configure your model below. Examples:
#   "google-gla:gemini-2.5-flash"    (needs GOOGLE_API_KEY)
#   "openai:gpt-4o-mini"             (needs OPENAI_API_KEY)
#   "anthropic:claude-sonnet-4-6"    (needs ANTHROPIC_API_KEY)
MODEL = os.getenv("MODEL", "google-gla:gemini-2.5-flash-lite")

if not os.getenv("GOOGLE_API_KEY"):
    raise RuntimeError("Missing GOOGLE_API_KEY in .env. Add your Google AI Studio key and run again.")

agent = Agent(
    MODEL,
    system_prompt=(
        "You are a helpful assistant. Solve each question step by step. "
        "Use the calculator tool for arithmetic. "
        "Use the product_lookup tool when a question mentions products from the catalog. "
        "If a question cannot be answered with the information given, say so."
    ),
)


@agent.tool_plain
def calculator_tool(expression: str) -> str:
    """Evaluate a math expression and return the result.

    Examples: "847 * 293", "10000 * (1.07 ** 5)", "23 % 4"
    """
    return calculate(expression)


@agent.tool_plain
def product_lookup(product_name: str) -> str:
    """Look up the price of a product by name.
    Use this when a question asks about product prices from the catalog.
    """
    with open(BASE_DIR / "products.json", encoding="utf-8") as f:
        products = json.load(f)

    product_name = product_name.strip()

    if product_name in products:
        return str(products[product_name])

    normalized_products = {name.lower(): name for name in products}
    matched_name = normalized_products.get(product_name.lower())
    if matched_name:
        return str(products[matched_name])

    available_products = ", ".join(products.keys())
    return f"Product not found. Available products: {available_products}"


def load_questions(path: str = "math_questions.md") -> list[str]:
    """Load numbered questions from the markdown file."""
    questions = []
    with open(BASE_DIR / path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and line[0].isdigit() and ". " in line[:4]:
                questions.append(line.split(". ", 1)[1])
    return questions


def extract_retry_delay(error: ModelHTTPError) -> int:
    """Extract a provider-suggested retry delay in seconds, with a safe fallback."""
    body = getattr(error, "body", None)
    if isinstance(body, dict):
        details = body.get("error", {}).get("details", [])
        for detail in details:
            if not isinstance(detail, dict):
                continue
            retry_delay = detail.get("retryDelay")
            if isinstance(retry_delay, str):
                match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)s", retry_delay)
                if match:
                    return math.ceil(float(match.group(1))) + 1

        message = body.get("error", {}).get("message")
        if isinstance(message, str):
            match = re.search(r"retry in ([0-9.]+)s", message, re.IGNORECASE)
            if match:
                return math.ceil(float(match.group(1))) + 1

    return 60


def run_question(question: str, max_attempts: int = 5):
    """Run one question, waiting and retrying on temporary provider rate limits."""
    for attempt in range(1, max_attempts + 1):
        try:
            return agent.run_sync(question)
        except ModelHTTPError as error:
            if error.status_code != 429 or attempt == max_attempts:
                raise

            wait_seconds = extract_retry_delay(error)
            print(
                f"[Rate limit] Provider quota hit. Waiting {wait_seconds} seconds "
                f"before retry {attempt + 1}/{max_attempts}...\n"
            )
            time.sleep(wait_seconds)


def main():
    questions = load_questions()
    for i, question in enumerate(questions, 1):
        print(f"## Question {i}")
        print(f"> {question}\n")

        result = run_question(question)

        print("### Trace")
        for message in result.all_messages():
            for part in message.parts:
                kind = part.part_kind
                if kind in ("user-prompt", "system-prompt"):
                    continue
                elif kind == "text":
                    print(f"- **Reason:** {part.content}")
                elif kind == "tool-call":
                    print(f"- **Act:** `{part.tool_name}({part.args})`")
                elif kind == "tool-return":
                    print(f"- **Result:** `{part.content}`")

        print(f"\n**Answer:** {result.output}\n")
        print("---\n")


if __name__ == "__main__":
    main()
