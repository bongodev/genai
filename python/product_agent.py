"""Simple product query agent.

Chat with Gemini. When it needs product info, it asks us to run a tool,
we run it against products.json, and send the result back.

Run:  GEMINI_API_KEY=... python product_agent.py
"""

import json
import os
from pathlib import Path

from google import genai
from google.genai import types

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
MAX_TURNS = 10  # max model calls per question, so a tool loop can't run forever
PRODUCTS_FILE = Path(__file__).with_name("products.json")
PRODUCTS = json.loads(PRODUCTS_FILE.read_text())

SYSTEM_PROMPT = (
    "You help shoppers find products in our catalog. "
    "Always use the tools to look up products. Never invent products, prices or stock. "
    "Keep answers short and list product names with their prices."
)


# --- Tools: plain Python functions the model can ask us to run ---

def search_products(query: str = "", max_price: float | None = None, category: str | None = None) -> list[dict]:
    """Return products whose name, category or description contain every word in the query."""
    words = query.lower().split()
    results = []
    for p in PRODUCTS:
        text = f"{p['name']} {p['category']} {p['description']}".lower()
        if not all(word in text for word in words):
            continue
        if max_price is not None and p["price"] > max_price:
            continue
        if category and p["category"] != category.lower():
            continue
        results.append({"id": p["id"], "name": p["name"], "category": p["category"],
                        "price": p["price"], "in_stock": p["in_stock"]})
    return results


def get_product(product_id: str) -> dict:
    """Return full details for one product."""
    for p in PRODUCTS:
        if p["id"] == product_id:
            return p
    return {"error": f"No product with id {product_id}"}


TOOL_FUNCTIONS = {
    "search_products": search_products,
    "get_product": get_product,
}

# Tell Gemini what the tools are and what arguments they take.
TOOLS = types.Tool(function_declarations=[
    types.FunctionDeclaration(
        name="search_products",
        description="Search the product catalog by keywords, with optional max price and category.",
        parameters=types.Schema(type="OBJECT", properties={
            "query": types.Schema(type="STRING", description="Keywords, e.g. 'wireless headphones'"),
            "max_price": types.Schema(type="NUMBER", description="Maximum price in dollars"),
            "category": types.Schema(type="STRING", description="Category: electronics, accessories, sports, kitchen or home"),
        }),
    ),
    types.FunctionDeclaration(
        name="get_product",
        description="Get full details for one product by its id.",
        parameters=types.Schema(type="OBJECT", properties={
            "product_id": types.Schema(type="STRING", description="Product id, e.g. 'p001'"),
        }, required=["product_id"]),
    ),
])


# --- The harness: run tools and loop until Gemini gives a text answer ---

def run_tool(call) -> types.Part:
    """Run one tool call and wrap the result so Gemini can read it."""
    func = TOOL_FUNCTIONS.get(call.name)
    try:
        if func is None:
            result = {"error": f"Unknown tool {call.name}"}
        else:
            result = func(**dict(call.args or {}))
    except Exception as e:  # send errors back to the model instead of crashing
        result = {"error": str(e)}
    return types.Part.from_function_response(name=call.name, response={"result": result})


def run_agent(client: genai.Client, history: list) -> str:
    """Send the conversation to Gemini, running tools until it returns plain text or MAX_TURNS is hit."""
    config = types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, tools=[TOOLS])
    for _ in range(MAX_TURNS):
        response = client.models.generate_content(model=MODEL, contents=history, config=config)
        model_content = response.candidates[0].content
        history.append(model_content)

        calls = [part.function_call for part in (model_content.parts or []) if part.function_call]
        if not calls:
            return response.text or "(no answer)"

        result_parts = []
        for call in calls:
            print(f"  [tool] {call.name}({dict(call.args or {})})")
            result_parts.append(run_tool(call))
        history.append(types.Content(role="user", parts=result_parts))
    return f"(stopped after {MAX_TURNS} turns without a final answer)"


def main():
    if not os.environ.get("GEMINI_API_KEY"):
        print("Set GEMINI_API_KEY first, e.g. export GEMINI_API_KEY=your-key")
        return

    client = genai.Client()
    history = []  # the whole conversation, so follow-ups like "cheaper ones?" work
    print("Product agent ready. Ask about products, or type 'quit' to exit.")

    while True:
        question = input("\nyou> ").strip()
        if question.lower() in ("quit", "exit"):
            break
        if not question:
            continue

        history.append(types.Content(role="user", parts=[types.Part(text=question)]))
        print(f"\nagent> {run_agent(client, history)}")


if __name__ == "__main__":
    main()
