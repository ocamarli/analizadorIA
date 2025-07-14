// src/services/OpenAIService.js
import { AzureOpenAI } from "openai";

/**
 * Genera una respuesta utilizando Azure OpenAI.
 * @param {string} input - Texto de entrada del usuario.
 * @param {string} promptChat - Instrucción para el modelo.
 * @param {Object} openAiConfig - Configuración del modelo OpenAI.
 * @returns {Promise<Object>} - Respuesta en formato JSON.
 */
const openAiApiKey = process.env.REACT_APP_OPENAI_API_KEY;
const openAiEndpoint = process.env.REACT_APP_OPENAI_ENDPOINT;
const openAiVersion = process.env.REACT_APP_OPENAI_VERSION;
const promptChat = process.env.REACT_APP_PROMPT_CHAT;
// Configura el cliente de OpenAI

export const generateOpenAIResponse = async (contextAzureSearch,input) => {
  try {
    const client = new AzureOpenAI({
        dangerouslyAllowBrowser: true,
        apiKey: openAiApiKey,
        endpoint: openAiEndpoint,
        apiVersion: openAiVersion
  });
    console.log("Contexto",contextAzureSearch)
    const response = await client.chat.completions.create({
      messages: [
        { role: "system", content: promptChat },
        { role: "system", content: contextAzureSearch },
        { role: "user", content: input },
      ],
      model: "gpt-4",
      temperature: 0.6,
    });

    console.log(promptChat)

    const fullResponse = response.choices[0]?.message?.content || "";

    return fullResponse;

  } catch (error) {
    console.error("Error en la solicitud de OpenAI:", error);
    throw new Error("No se pudo generar la respuesta con OpenAI.");
  }
};
