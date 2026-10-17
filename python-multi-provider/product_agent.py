"""Simple product query agent.

Chat with an LLM (Gemini or Z.ai GLM). When it needs product info, it asks us to
run a tool, we run it against products.json, and send the result back.

At startup you choose the provider (gemini or zai). LLM_PROVIDER sets the default choice.

Run:  GEMINI_API_KEY=... python product_agent.py
      LLM_PROVIDER=zai ZAI_API_KEY=... python product_agent.py
"""

import json
import os
from pathlib import Path
from typing import Any, Protocol

from google import genai
from google.genai import types
from pydantic import BaseModel, Field, TypeAdapter
from pydantic_core import to_jsonable_python
from zai import ZaiClient
from zai.types.chat.chat_completion import Completion

PROVIDER = os.environ.get("LLM_PROVIDER", "gemini").lower()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
ZAI_MODEL = os.environ.get("ZAI_MODEL", "glm-5.3")
MAX_TURNS = 10  # max model calls per question, so a tool loop can't run forever
PRODUCTS_FILE = Path(__file__).with_name("products.json")

SYSTEM_PROMPT = (
    "You help shoppers find products in our catalog. "
    "Always use the tools to look up products. Never invent products, prices or stock. "
    "Keep answers short and list product names with their prices."
)


# --- Data models ---

class Product(BaseModel):
    """One entry in products.json."""

    id: str
    name: str
    category: str
    price: float = Field(ge=0)
    rating: float = Field(ge=0, le=5)
    in_stock: bool
    description: str


class ProductSummary(BaseModel):
    """The short view of a product that search returns."""

    id: str
    name: str
    category: str
    price: float
    in_stock: bool

    @classmethod
    def from_product(cls, product: Product) -> "ProductSummary":
        return cls(
            id=product.id,
            name=product.name,
            category=product.category,
            price=product.price,
            in_stock=product.in_stock,
        )


class ErrorResult(BaseModel):
    """Returned by a tool when it cannot answer."""

    error: str


class SearchProductsArgs(BaseModel):
    """Arguments the model may pass to search_products."""

    query: str = ""
    max_price: float | None = None
    category: str | None = None


class GetProductArgs(BaseModel):
    """Arguments the model may pass to get_product."""

    product_id: str


# Load and validate the catalog once at startup. A malformed file fails here, not mid-chat.
PRODUCTS: list[Product] = TypeAdapter(list[Product]).validate_json(PRODUCTS_FILE.read_text())


# --- Tools: plain Python functions the model can ask us to run ---

def search_products(args: SearchProductsArgs) -> list[ProductSummary]:
    """Return products whose name, category or description contain every word in the query."""
    words = args.query.lower().split()
    results: list[ProductSummary] = []
    for product in PRODUCTS:
        text = f"{product.name} {product.category} {product.description}".lower()
        if not all(word in text for word in words):
            continue
        if args.max_price is not None and product.price > args.max_price:
            continue
        if args.category and product.category != args.category.lower():
            continue
        results.append(ProductSummary.from_product(product))
    return results


def get_product(args: GetProductArgs) -> Product | ErrorResult:
    """Return full details for one product."""
    for product in PRODUCTS:
        if product.id == args.product_id:
            return product
    return ErrorResult(error=f"No product with id {args.product_id}")


def execute_tool(name: str, raw_args: dict[str, Any]) -> object:
    """Validate the model's arguments for a tool and run it."""
    if name == "search_products":
        return search_products(SearchProductsArgs.model_validate(raw_args))
    if name == "get_product":
        return get_product(GetProductArgs.model_validate(raw_args))
    return ErrorResult(error=f"Unknown tool {name}")


def call_tool(name: str, raw_args: dict[str, Any]) -> Any:
    """Run a tool and return JSON-ready data. Errors go back to the model instead of crashing."""
    try:
        return to_jsonable_python(execute_tool(name, raw_args))
    except Exception as e:
        return {"error": str(e)}


# The tools in JSON Schema form. Gemini and Z.ai both accept this format.
TOOL_SPECS: list[dict[str, Any]] = [
    {
        "name": "search_products",
        "description": "Search the product catalog by keywords, with optional max price and category.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Keywords, e.g. 'wireless headphones'"},
                "max_price": {"type": "number", "description": "Maximum price in dollars"},
                "category": {
                    "type": "string",
                    "description": "Category: electronics, accessories, sports, kitchen or home",
                },
            },
        },
    },
    {
        "name": "get_product",
        "description": "Get full details for one product by its id.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Product id, e.g. 'p001'"},
            },
            "required": ["product_id"],
        },
    },
]


# --- Providers: each one keeps its own conversation in its own wire format ---

class Assistant(Protocol):
    def ask(self, question: str) -> str: ...


class GeminiAssistant:
    def __init__(self, client: genai.Client) -> None:
        self.client = client
        self.history: list[types.Content] = []
        self.config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[types.Tool(function_declarations=[
                types.FunctionDeclaration(
                    name=spec["name"],
                    description=spec["description"],
                    parameters_json_schema=spec["parameters"],
                )
                for spec in TOOL_SPECS
            ])],
        )

    def ask(self, question: str) -> str:
        self.history.append(types.Content(role="user", parts=[types.Part(text=question)]))
        for _ in range(MAX_TURNS):
            response = self.client.models.generate_content(
                model=GEMINI_MODEL, contents=self.history, config=self.config,
            )
            model_content = response.candidates[0].content if response.candidates else None
            if model_content is None:
                return response.text or "(no answer)"
            self.history.append(model_content)

            calls: list[types.FunctionCall] = []
            for part in model_content.parts or []:
                if part.function_call is not None:
                    calls.append(part.function_call)
            if not calls:
                return response.text or "(no answer)"

            result_parts: list[types.Part] = []
            for call in calls:
                name = call.name or ""
                args = dict(call.args or {})
                print(f"  [tool] {name}({args})")
                result_parts.append(types.Part.from_function_response(
                    name=name, response={"result": call_tool(name, args)},
                ))
            self.history.append(types.Content(role="user", parts=result_parts))
        return f"(stopped after {MAX_TURNS} turns without a final answer)"


class ZaiAssistant:
    def __init__(self, client: ZaiClient) -> None:
        self.client = client
        self.messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.tools = [{"type": "function", "function": spec} for spec in TOOL_SPECS]

    def ask(self, question: str) -> str:
        self.messages.append({"role": "user", "content": question})
        for _ in range(MAX_TURNS):
            response = self.client.chat.completions.create(
                model=ZAI_MODEL, messages=self.messages, tools=self.tools, tool_choice="auto", stream=False,
            )
            if not isinstance(response, Completion):
                raise TypeError("Expected a complete (non-streamed) Z.ai response")
            message = response.choices[0].message
            self.messages.append(message.model_dump(exclude_none=True))

            if not message.tool_calls:
                return message.content or "(no answer)"

            for tool_call in message.tool_calls:
                name = tool_call.function.name
                print(f"  [tool] {name}({tool_call.function.arguments})")
                payload = self._run(name, tool_call.function.arguments)
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(payload, ensure_ascii=False),
                })
        return f"(stopped after {MAX_TURNS} turns without a final answer)"

    @staticmethod
    def _run(name: str, arguments: str) -> Any:
        """Parse the model's JSON arguments, then run the tool."""
        try:
            args = json.loads(arguments or "{}")
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON arguments: {e}"}
        if not isinstance(args, dict):
            return {"error": "Tool arguments must be a JSON object"}
        return call_tool(name, args)


def make_assistant(provider: str) -> Assistant | None:
    """Build the chosen provider's client, or return None with a message if its key is missing."""
    if provider == "gemini":
        if not os.environ.get("GEMINI_API_KEY"):
            print("Set GEMINI_API_KEY first, e.g. export GEMINI_API_KEY=your-key")
            return None
        return GeminiAssistant(genai.Client())
    if provider == "zai":
        api_key = os.environ.get("ZAI_API_KEY")
        if not api_key:
            print("Set ZAI_API_KEY first, e.g. export ZAI_API_KEY=your-key")
            return None
        return ZaiAssistant(ZaiClient(api_key=api_key))
    print(f"Unknown LLM_PROVIDER '{provider}'. Use gemini or zai.")
    return None


PROVIDERS = ("gemini", "zai")


def choose_provider() -> str:
    """Ask which provider to use. Enter accepts the default (from LLM_PROVIDER, else gemini)."""
    default = PROVIDER if PROVIDER in PROVIDERS else "gemini"
    print("Choose an LLM provider:")
    for number, name in enumerate(PROVIDERS, start=1):
        suffix = " (default)" if name == default else ""
        print(f"  {number}) {name}{suffix}")
    while True:
        choice = input(f"Enter 1-{len(PROVIDERS)} or a name [{default}]: ").strip().lower()
        if not choice:
            return default
        if choice.isdigit() and 1 <= int(choice) <= len(PROVIDERS):
            return PROVIDERS[int(choice) - 1]
        if choice in PROVIDERS:
            return choice
        print("Please enter a number from the list or a provider name.")


def main() -> None:
    assistant = make_assistant(choose_provider())
    if assistant is None:
        return

    print("Product agent ready. Ask about products, or type 'quit' to exit.")
    while True:
        question = input("\nyou> ").strip()
        if question.lower() in ("quit", "exit"):
            break
        if not question:
            continue
        print(f"\nagent> {assistant.ask(question)}")


if __name__ == "__main__":
    main()
