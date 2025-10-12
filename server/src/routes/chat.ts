import express, { type Request, type Response } from "express";

import { ChatMessage, genAI } from "@/llm";
import { SYSTEM_PROMPT } from "@/prompts";
import { searchProductsDefinition } from "@/tools";
import { searchProducts } from "@/services";

const router = express.Router();

const chatHistory: ChatMessage[] = [];

const toolMap = {
  search_products: searchProducts,
};

router.post("/chat", async (req: Request, res: Response) => {
  let userMessage = req.body.message.trim();

  if (!userMessage) {
    return res.status(400).json({
      error: "Message is required",
    });
  }

  const chat = genAI.chats.create({
    model: "gemini-2.5-flash",
    history: chatHistory,
    config: {
      systemInstruction: SYSTEM_PROMPT,
      tools: [
        {
          functionDeclarations: [searchProductsDefinition],
        },
      ],
    },
  });

  chatHistory.push({
    role: "user",
    parts: [
      {
        text: userMessage,
      },
    ],
  });

  let finalResponse = "";
  let currentMessage = userMessage;
  while (true) {
    const response = await chat.sendMessage({
      message: currentMessage,
    });

    console.log(
      "=====>>> Response candidates:",
      JSON.stringify(response.candidates, null, 2)
    );

    if (response.functionCalls && response.functionCalls.length > 0) {
      const functionCall = response.functionCalls[0];
      const toolName = functionCall.name;

      console.log("=====>>> Tool call detected:", toolName, functionCall.args);

      if (!toolName || !(toolName in toolMap)) {
        throw new Error(`Tool ${toolName} not found`);
      }

      // @ts-expect-error
      const toolResult = await toolMap[toolName](functionCall.args);

      console.log("=====>>> Tool result:", toolResult);

      currentMessage = `
      Here is the response of the ${toolName} tool: ${JSON.stringify(
        toolResult
      )}
      `;
      continue;
    }

    chatHistory.push({
      role: "model",
      parts: [
        {
          text: response.text,
        },
      ],
    });
    finalResponse = response.text || "";
    break;
  }

  console.log("Chat history:", JSON.stringify(chatHistory, null, 2));

  return res.json({
    message: finalResponse,
  });
});

export default router;
