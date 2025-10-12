import { Type } from "@google/genai";
import { searchProducts } from "@/services";

const searchProductsDefinition = {
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

export const searchProductsTool = {
  definition: searchProductsDefinition,
  execute: async ({ query }: { query: string }) => {
    return searchProducts({ query });
  },
}