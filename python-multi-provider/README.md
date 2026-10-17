# Product Agent

A small command-line shopping assistant. You chat with Gemini or Z.ai's GLM models in your terminal, and it looks up products in a local catalog (`products.json`) to answer your questions. The model calls our search tools when it needs product info, so answers come from the catalog rather than from the model's memory.

## Features

- Works with Gemini or Z.ai (GLM), chosen with `LLM_PROVIDER`
- Search products by keyword, with optional max price and category filters
- Get full details for a single product by ID
- Keeps the whole conversation, so follow-ups like "cheaper ones?" work
- Stops tool loops after a fixed number of turns (`MAX_TURNS`, default 10)

## Project structure

```
.
├── product_agent.py   # the agent: tools, Gemini client, chat loop
├── products.json      # the product catalog
├── requirements.txt   # Python dependencies
├── .env.example       # template for environment variables
├── .gitignore
├── run.sh             # sets up the environment and runs the app
└── README.md
```

## Requirements

- Python 3.10 or newer (the code uses `float | None` type hints)
- An API key for one provider:
  - Gemini: from [Google AI Studio](https://aistudio.google.com/apikey)
  - Z.ai (GLM): from [z.ai](https://z.ai)
- The packages in `requirements.txt` (`google-genai`, `zai-sdk`, `pydantic`)

## Quick start

The fastest way is the `run.sh` script. From the project directory:

```bash
./run.sh
```

On the first run it creates a virtual environment in `.venv/`, installs the dependencies, and creates `.env` from `.env.example`. If the API key for your provider is still the placeholder, it stops and asks you to edit `.env`. Once the key is set, run `./run.sh` again.

| Command            | What it does                                                              |
|--------------------|---------------------------------------------------------------------------|
| `./run.sh`         | Runs setup if it hasn't been done yet, then starts the app (same as `run`) |
| `./run.sh setup`   | Creates `.venv/`, installs dependencies, creates `.env` if missing        |
| `./run.sh run`     | Loads `.env` and starts the app (runs setup first if needed)              |
| `./run.sh help`    | Shows usage                                                               |

`run.sh` loads `.env` for you, so you don't need to export variables. You can also follow the manual steps below.

## Manual setup

1. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Set your API key. Copy the template and fill in your key:

   ```bash
   cp .env.example .env
   ```

   The script reads variables from the shell environment and does not load `.env` on its own, so export the values before running. For Gemini (the default):

   ```bash
   export GEMINI_API_KEY=your-key-here
   ```

   For Z.ai (GLM), also export its key:

   ```bash
   export ZAI_API_KEY=your-key-here
   ```

   You choose the provider when the app starts.

   Optionally pick a different model with `GEMINI_MODEL` or `ZAI_MODEL`.

## Running the app

With the script:

```bash
./run.sh
```

Or run it directly, after completing the manual setup:

```bash
python product_agent.py
```

Or pass the key inline for a single run:

```bash
GEMINI_API_KEY=your-key-here python product_agent.py
```

You'll first be asked which provider to use:

```
Choose an LLM provider:
  1) gemini (default)
  2) zai
Enter 1-2 or a name [gemini]:
```

Type a number or name, or press Enter for the default. Then you'll see:

```
Product agent ready. Ask about products, or type 'quit' to exit.

you> wireless headphones under $100
  [tool] search_products({'query': 'wireless headphones', 'max_price': 100.0})

agent> ...
```

Type `quit` or `exit` to stop. If `GEMINI_API_KEY` is not set, the app prints a message and exits.

## Configuration

| Variable         | Required                 | Default            | Description                                              |
|------------------|--------------------------|--------------------|----------------------------------------------------------|
| `LLM_PROVIDER`   | No                       | `gemini`           | Default provider shown at the startup prompt: `gemini` or `zai` |
| `GEMINI_API_KEY` | Yes, if using Gemini     | —                  | Your Gemini API key                                      |
| `GEMINI_MODEL`   | No                       | `gemini-3.8-flash` | Gemini model used for chat                               |
| `ZAI_API_KEY`    | Yes, if using Z.ai       | —                  | Your Z.ai API key                                        |
| `ZAI_MODEL`      | No                       | `glm-5.3`          | Z.ai model used for chat; must support function calling  |

`MAX_TURNS` is set in `product_agent.py`. It limits how many model calls one question can trigger.

## Product catalog

`products.json` is a list of products. Each entry has:

- `id`: such as `p001`
- `name`, `category`, `description`
- `price`: in dollars
- `in_stock`: boolean

Categories are `electronics`, `accessories`, `sports`, `kitchen`, and `home`. To change the catalog, edit `products.json`. The file is loaded once at startup, so restart the app after editing it.

## Troubleshooting

- **`GEMINI_API_KEY is not set`** (from `run.sh`): edit `.env` and replace the placeholder with your key.
- **`Set GEMINI_API_KEY first`** (from `python product_agent.py`): the variable isn't set in the shell you're using. Export it or pass it inline.
- **`python3 not found` or `Python 3.10 or newer is required`**: install a newer Python, then run `./run.sh setup` again.
- **`Permission denied: ./run.sh`**: run `chmod +x run.sh` once.
- **`ZAI_API_KEY is not set`**: you picked zai at the prompt. Set `ZAI_API_KEY` in `.env` (or export it) and run again.
- **`ModuleNotFoundError: No module named 'google'`**: run `pip install -r requirements.txt`.
- **`TypeError` about `float | None`**: upgrade to Python 3.10 or newer.
- **`(stopped after 10 turns without a final answer)`**: the model kept calling tools without giving a final answer. Try rephrasing the question.
