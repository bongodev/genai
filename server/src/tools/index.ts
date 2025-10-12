import { Type } from "@google/genai";

export const searchProductsDefinition = {
  name: "search_products",
  description: "Search for products by name, description, or specifications",
  parameters: {
    type: Type.OBJECT,
    properties: {
      query: { type: Type.STRING, description: "The query to search for" },
    },
    required: ["query"],
  },
};
