import requests
import json

# Imposta la tua API Key
API_KEY = "W76RQY11KN68Z9759W0FKFMDVW"
API_URL = "https://api.climatiq.io/data/v1/search"

# Materiale da cercare (ad esempio "steel")
query_material = "steel"

# Parametri della richiesta API
params = {
    "query": query_material,
    "data_version": "^3"
}

# Intestazioni della richiesta
headers = {
    "Authorization": f"Bearer {API_KEY}"
}

# Esegui la richiesta API
response = requests.get(API_URL, params=params, headers=headers)

if response.status_code == 200:
    data = response.json()

    # Debug: stampiamo la struttura della risposta
    print(json.dumps(data, indent=2))

    # Estrai i risultati con i dati di emissione
    results = []
    for entry in data.get("results", []):
        name = entry.get("name", "Unknown Material")
        unit = entry.get("unit", "Unknown Unit")
        emission_factor = entry.get("emission_factor", {})

        co2e_value = emission_factor.get("co2e", "N/A")
        co2e_unit = emission_factor.get("co2e_unit", "N/A")

        results.append(f"{name}: {unit} - {co2e_value} {co2e_unit}")

    # Stampa i materiali trovati con il valore di CO₂e
    if results:
        print("\nMateriali trovati:")
        for result in results:
            print(result)
    else:
        print("Nessun materiale elettronico trovato.")

else:
    print(f"Errore nella richiesta API: {response.status_code}, {response.text}")
