from .base_agent import LCAAgent
from typing import Dict, Any

class ValidationAgent(LCAAgent):
    def __init__(self):
        super().__init__("Validation Agent")
        self.benchmarks = {
            "smartphone": {"min": 30.0, "max": 100.0},
            "laptop": {"min": 150.0, "max": 300.0},
            "tablet": {"min": 70.0, "max": 150.0}
        }
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        co2e = data.get("co2e_kg")
        product_name = data.get("title", "").lower()
        
        # Determina la categoria
        if any(term in product_name for term in ["iphone", "galaxy", "smartphone"]):
            category = "smartphone"
        elif any(term in product_name for term in ["macbook", "thinkpad", "laptop"]):
            category = "laptop"
        elif "ipad" in product_name:
            category = "tablet"
        else:
            category = "unknown"
            
        if not co2e:
            return {
                "valid": False,
                "confidence": 0.0,
                "message": "Nessun valore CO2e disponibile"
            }
            
        benchmark = self.benchmarks.get(category, {"min": 0, "max": 1000})
        is_valid = benchmark["min"] <= co2e <= benchmark["max"]
        
        return {
            "valid": is_valid,
            "confidence": 0.8 if is_valid else 0.3,
            "message": f"Validazione basata su benchmark {category}"
        }