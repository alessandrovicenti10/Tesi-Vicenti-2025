from together import Together

client = Together(api_key = "api_key")

response = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    messages=[{"role": "user", "content": "Stimami l'impatto ambientale in termini di C02 emessa relativamente al processo di produzione, per un monitor philips 27 pollici ed un monitor LG 27 pollici"}],
)
print(response.choices[0].message.content)