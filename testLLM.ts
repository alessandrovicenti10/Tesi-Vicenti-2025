
import Together from "together-ai";

const together = new Together({ apiKey: "5a49da191ec54d69ba99d57d9f6413d527a061172fbd48d51cfbeee2e7561568" });

async function run() {
    const response = await together.chat.completions.create({
        messages: [{ "role": "user", "content": "What are some fun things to do in New York?" }],
        model: "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    });

    console.log(response.choices?.[0]?.message?.content ?? "Nessuna risposta ricevuta!");

}

run();
