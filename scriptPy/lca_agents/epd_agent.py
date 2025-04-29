from .base_agent import LCAAgent
from typing import Dict, Any
import json

class EPDSearchAgent(LCAAgent):
    def __init__(self):
        super().__init__("EPD Search Agent")
        # Database semplificato di valori EPD noti
        self.known_epds = {
            "iphone": {"co2e_kg": 70.0, "source": "Apple Environmental Report 2024"},
            "macbook": {"co2e_kg": 185.0, "source": "Apple Environmental Report 2024"},
            "ipad": {"co2e_kg": 95.0, "source": "Apple Environmental Report 2024"}
        }
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        product_name = data.get("title", "").lower()
        
        # Cerca corrispondenze nel database EPD
        for key, value in self.known_epds.items():
            if key in product_name:
                return {
                    "found_epd": True,
                    "co2e_kg": value["co2e_kg"],
                    "source": value["source"],
                    "confidence": 0.9
                }
        
        # Stima basata su categoria
        if "smartphone" in product_name:
            return {"found_epd": False, "co2e_kg": 65.0, "confidence": 0.7}
        elif "laptop" in product_name or "notebook" in product_name:
            return {"found_epd": False, "co2e_kg": 175.0, "confidence": 0.7}
        
        return {"found_epd": False, "co2e_kg": None, "confidence": 0.0}