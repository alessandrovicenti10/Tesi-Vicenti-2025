import asyncio
from typing import List, Dict, Any
from .base_agent import LCAAgent
from .epd_agent import EPDSearchAgent
from .validation_agent import ValidationAgent
import asyncio

class LCACoordinator:
    """Coordinatore del sistema multi-agente"""
    
    def __init__(self):
        self.agents: List[LCAAgent] = [
            EPDSearchAgent(),
            ValidationAgent()
        ]
    
    async def process_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa un prodotto utilizzando tutti gli agenti disponibili"""
        tasks = [agent.process(product_data) for agent in self.agents]
        results = await asyncio.gather(*tasks)
        
        # Combina i risultati degli agenti
        epd_result = results[0]  # Risultato dell'EPDSearchAgent
        validation_result = results[1]  # Risultato del ValidationAgent
        
        # Se troviamo un EPD, usiamo quel valore
        if epd_result.get("found_epd", False):
            return {
                "co2e_kg": epd_result.get("co2e_kg"),
                "explanation": f"Valore trovato da EPD ufficiale. Fonte: {epd_result.get('source')}"
            }
        
        # Altrimenti, restituiamo un risultato stimato con la validazione
        return {
            "co2e_kg": epd_result.get("co2e_kg"),
            "explanation": (
                f"Stima basata su analisi LCA. "
                f"Confidenza: {validation_result.get('confidence', 0.0)*100}%. "
                f"Validazione: {validation_result.get('valid', False)}"
            )
        }