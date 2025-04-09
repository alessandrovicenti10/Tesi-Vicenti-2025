#!/usr/bin/env python3
import json
import argparse
import os
import requests
from typing import List, Dict, Any, Optional

class LLMEmissionsEstimator:
    """
    Classe per stimare le emissioni di CO2 di prodotti elettronici utilizzando un LLM.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Inizializza l'estimatore con la chiave API e il modello.
        
        Args:
            api_key: Chiave API per il servizio LLM (se None, cerca in OPENAI_API_KEY env var)
            model: Nome del modello da utilizzare
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            print("ATTENZIONE: Nessuna chiave API fornita. Imposta la variabile d'ambiente OPENAI_API_KEY o passa la chiave come parametro.")
        
        self.model = model
        
        # Carica i fattori di emissione di riferimento
        self.material_factors = {
            'plastic': 3.5,
            'silicone': 5.2,
            'aluminum': 8.24,
            'glass': 1.44,
            'steel': 2.89,
            'copper': 3.81,
            'lithium-ion battery': 12.5,
            'pcb': 60.0,
            'default': 5.0
        }
        
        self.category_factors = {
            'smartphones': 80.0,
            'laptops': 340.0,
            'tablets': 120.0,
            'desktop computers': 280.0,
            'monitors': 220.0,
            'televisions': 200.0,
            'cameras': 170.0,
            'headphones': 60.0,
            'speakers': 40.0,
            'accessories': 20.0,
            'default': 50.0
        }
    
    def create_prompt(self, product_info: Dict[str, Any]) -> str:
        """
        Crea un prompt per il LLM basato sulle informazioni del prodotto.
        
        Args:
            product_info: Dizionario con le informazioni del prodotto
            
        Returns:
            Prompt formattato per il LLM
        """
        prompt = f"""
Sei un esperto di analisi del ciclo di vita (LCA) e calcolo delle emissioni di CO2 per prodotti elettronici.
Devi stimare le emissioni di CO2e per kg di prodotto (kg CO2e/kg) per il seguente prodotto elettronico.

INFORMAZIONI SUL PRODOTTO:
Nome: {product_info.get('title', 'N/A')}
Categorie: {', '.join(product_info.get('categories', ['N/A']))}
Peso: {product_info.get('weight_kg', 'Non specificato')} kg
Materiale principale: {product_info.get('material', 'Non specificato')}
Dettagli aggiuntivi: {json.dumps(product_info.get('details', {}), indent=2)}

FATTORI DI EMISSIONE DI RIFERIMENTO:
Fattori per materiali (kg CO2e/kg):
{json.dumps(self.material_factors, indent=2)}

Fattori per categorie di prodotti (kg CO2e/kg):
{json.dumps(self.category_factors, indent=2)}

ISTRUZIONI:
1. Analizza le informazioni del prodotto.
2. Considera i materiali principali del prodotto.
3. Stima il fattore di emissione in kg CO2e/kg basandoti sui fattori di riferimento.
4. Fornisci una breve spiegazione del tuo ragionamento.
5. Se mancano informazioni, fai assunzioni ragionevoli basate su prodotti simili.

Rispondi SOLO in formato JSON con i seguenti campi:
{
  "product_name": "Nome del prodotto",
  "category": "Categoria identificata",
  "materials": ["Materiale 1", "Materiale 2"],
  "co2e_per_kg": 123.45,
  "explanation": "Breve spiegazione del calcolo"
}
"""
        return prompt
    
    def call_llm_api(self, prompt: str) -> Dict[str, Any]:
        """
        Chiama l'API del LLM con il prompt fornito.
        
        Args:
            prompt: Prompt da inviare al LLM
            
        Returns:
            Risposta del LLM in formato JSON
        """
        if not self.api_key:
            raise ValueError("Chiave API non fornita. Impossibile chiamare l'API.")
        
        # Esempio di chiamata all'API di OpenAI
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }
        
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()
            
            # Estrai e analizza la risposta JSON
            content = result["choices"][0]["message"]["content"]
            return json.loads(content)
            
        except requests.exceptions.RequestException as e:
            print(f"Errore nella chiamata API: {e}")
            return {"error": str(e)}
        except json.JSONDecodeError:
            print("Errore nel parsing della risposta JSON")
            return {"error": "Errore nel parsing della risposta JSON"}
    
    def estimate_emissions(self, product_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stima le emissioni di CO2 per un prodotto utilizzando il LLM.
        
        Args:
            product_info: Dizionario con le informazioni del prodotto
            
        Returns:
            Dizionario con la stima delle emissioni e la spiegazione
        """
        prompt = self.create_prompt(product_info)
        
        try:
            result = self.call_llm_api(prompt)
            return result
        except Exception as e:
            print(f"Errore nella stima delle emissioni: {e}")
            
            # Fallback: usa un metodo semplificato se l'API fallisce
            return self.fallback_estimation(product_info)
    
    def fallback_estimation(self, product_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Metodo di fallback per stimare le emissioni quando l'API fallisce.
        
        Args:
            product_info: Dizionario con le informazioni del prodotto
            
        Returns:
            Dizionario con la stima delle emissioni e la spiegazione
        """
        # Determina la categoria
        category = "default"
        for cat in product_info.get('categories', []):
            cat_lower = cat.lower()
            if "laptop" in cat_lower:
                category = "laptops"
                break
            elif "phone" in cat_lower or "smartphone" in cat_lower:
                category = "smartphones"
                break
            elif "tablet" in cat_lower:
                category = "tablets"
                break
            elif "monitor" in cat_lower:
                category = "monitors"
                break
            elif "tv" in cat_lower or "television" in cat_lower:
                category = "televisions"
                break
            elif "camera" in cat_lower:
                category = "cameras"
                break
            elif "headphone" in cat_lower or "earphone" in cat_lower or "earbud" in cat_lower:
                category = "headphones"
                break
            elif "speaker" in cat_lower:
                category = "speakers"
                break
            elif "desktop" in cat_lower or "computer" in cat_lower:
                category = "desktop computers"
                break
            elif "accessory" in cat_lower or "accessories" in cat_lower:
                category = "accessories"
                break
        
        # Determina il fattore di emissione
        emission_factor = self.category_factors.get(category, self.category_factors['default'])
        
        return {
            "product_name": product_info.get('title', 'Unknown Product'),
            "category": category,
            "materials": [product_info.get('material', 'unknown')],
            "co2e_per_kg": emission_factor,
            "explanation": f"Stima basata sulla categoria '{category}' utilizzando il metodo di fallback."
        }
    
    def process_batch(self, products: List[Dict[str, Any]], output_file: str) -> None:
        """
        Elabora un batch di prodotti e salva i risultati in un file JSON.
        
        Args:
            products: Lista di dizionari con le informazioni dei prodotti
            output_file: Percorso del file di output
        """
        results = []
        
        for i, product in enumerate(products):
            print(f"Elaborazione prodotto {i+1}/{len(products)}: {product.get('title', 'Unknown')[:50]}...")
            result = self.estimate_emissions(product)
            results.append(result)
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Elaborati {len(results)} prodotti. Risultati salvati in {output_file}")

def load_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """
    Carica un file JSONL e restituisce una lista di dizionari.
    
    Args:
        file_path: Percorso del file JSONL
        
    Returns:
        Lista di dizionari con i dati del file JSONL
    """
    products = []
    with open(file_path, 'r') as f:
        for line in f:
            try:
                data = json.loads(line)
                
                # Estrai le informazioni rilevanti
                product_info = {
                    'asin': data.get('asin', ''),
                    'title': data.get('title', 'Unknown Product'),
                    'categories': data.get('categories', []),
                    'material': data.get('details', {}).get('Material'),
                    'weight_kg': None,
                    'details': data.get('details', {})
                }
                
                # Estrai il peso se disponibile
                if 'details' in data and 'Item Weight' in data['details']:
                    weight_str = data['details']['Item Weight']
                    # Qui dovresti implementare la funzione extract_weight
                    # Per semplicità, la omettiamo in questo esempio
                
                products.append(product_info)
                
            except json.JSONDecodeError:
                print(f"Errore nel parsing JSON")
    
    return products

def main():
    parser = argparse.ArgumentParser(description='Stima le emissioni di CO2 per prodotti elettronici usando un LLM')
    parser.add_argument('--input', type=str, required=True, help='Percorso del file JSONL di input')
    parser.add_argument('--output', type=str, required=True, help='Percorso del file JSON di output')
    parser.add_argument('--api-key', type=str, help='Chiave API per il servizio LLM (opzionale, altrimenti usa OPENAI_API_KEY)')
    parser.add_argument('--model', type=str, default='gpt-4', help='Nome del modello LLM da utilizzare')
    parser.add_argument('--limit', type=int, help='Limite di prodotti da elaborare (opzionale)')
    
    args = parser.parse_args()
    
    # Carica i prodotti dal file JSONL
    products = load_jsonl(args.input)
    
    # Limita il numero di prodotti se specificato
    if args.limit and args.limit > 0:
        products = products[:args.limit]
    
    # Inizializza l'estimatore
    estimator = LLMEmissionsEstimator(api_key=args.api_key, model=args.model)
    
    # Elabora i prodotti
    estimator.process_batch(products, args.output)

if __name__ == "__main__":
    main()
