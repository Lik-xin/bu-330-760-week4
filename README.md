# Week 4: Math Agent with Tool Use

This project implements a ReAct-style math agent using `pydantic-ai`. The agent uses:

- `calculator_tool` for arithmetic
- `product_lookup` for reading prices from `products.json`

The completed agent can answer all 8 questions in `math_questions.md`, including the catalog-price questions.

## Walkthrough Video

Replace the placeholder below with your final video URL after recording:

`VIDEO_LINK_HERE`

## Setup

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).
2. Copy `.env.example` to `.env`.
3. Add your API key to `.env`.

```bash
cp .env.example .env
```

Keep your real API key only in `.env` and do not commit it to GitHub.

The starter defaults to Google AI Studio:

```env
GOOGLE_API_KEY=your-key-here
```

If you want to use a different provider, update the `MODEL` value in `agent.py` and set the matching environment variable in `.env`.

## Run

```bash
uv run agent.py
```

The program prints the ReAct trace for each question:

- `Reason`
- `Act`
- `Result`

## Project Files

- `agent.py` - main ReAct agent and registered tools
- `calculator.py` - calculator tool implementation
- `products.json` - product catalog
- `math_questions.md` - 8 assignment questions
- `pyproject.toml` - project dependencies
- `.env.example` - API key template
- `.gitignore` - ignores `.env`, `.venv`, and cache files
