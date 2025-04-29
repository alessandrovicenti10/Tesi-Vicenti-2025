from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class LCAAgent(ABC):
    """Classe base per tutti gli agenti LCA"""
    
    def __init__(self, name: str):
        self.name = name
        
    @abstractmethod
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Metodo principale che ogni agente deve implementare"""
        pass