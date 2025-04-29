import asyncio
from pathlib import Path
import json
from lca_agents.coordinator import LCACoordinator
from typing import Dict, Any

async def estimate_co2_for_product(product_data: Dict[str, Any], coordinator: LCACoordinator) -> Dict[str, Any]:
    """Stima la carbon footprint usando il sistema multi-agente"""
    
    try:
        result = await coordinator.process_product(product_data)
        return result
    except Exception as exc:
        return {
            "co2e_kg": None,
            "explanation": f"Error: {exc}"
        }

async def main(num_rows: int = 26):
    coordinator = LCACoordinator()
    products = []
    
    # Carica i prodotti
    with open("../dataset/Multi_products.jsonl", "r", encoding="utf-8") as fp:
        for i, line in enumerate(fp):
            if i >= num_rows:
                break
            products.append(json.loads(line))
    
    # Processa i prodotti
    results = []
    for product in products:
        result = await estimate_co2_for_product(product, coordinator)
        results.append({
            "product_name": product.get("title", "Unknown"),
            **result
        })
    
    # Salva i risultati
    out_path = Path("MultiAgent_results.json")
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Salvati {len(results)} risultati in {out_path.resolve()}")

if __name__ == "__main__":
    asyncio.run(main())