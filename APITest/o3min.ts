import OpenAI from 'openai';

const ROUTER_API_KEY = "sk-CXbt4BTfTTubL4sZra0wfWDOafAHpYtfeNCfRkNWaD+QScjwpFCujmTxXpi075doH6o8HniaZqPkegwucz+rZ9idphoxDiR88K58rVa8WAs=";

// Initialize the client
const client = new OpenAI({
    apiKey: ROUTER_API_KEY,
    baseURL: "https://router.requesty.ai/v1"
});

async function main() {
    try {
        // Make your API call
        const response = await client.chat.completions.create({
            model: "cline/o3-mini:high",
            messages: [
                {
                    role: "system",
                    content: "You are a helpful assistant."
                },
                {
                    role: "user",
                    content: "Hello! How can you help me today?"
                }
            ]
        });

        // Print the assistant's response
        console.log("Assistant:", response.choices[0].message.content);

    } catch (error) {
        if (error instanceof OpenAI.APIError) {
            console.error("OpenAI API error:", error);
        } else {
            console.error("Unexpected error:", error);
        }
    }
}

main();