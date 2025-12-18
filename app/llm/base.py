from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseLLM(ABC):
    """Abstract Base Class for LLM Providers"""

    @abstractmethod
    async def generate_response(
        self, 
        prompt: str, 
        history: List[Dict[str, str]] = [], 
        context: str = "",
        system_instruction: Optional[str] = None
    ) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The user's current message.
            history: List of previous messages [{'role': 'user', 'content': '...'}, ...].
            context: Retrieved knowledge/business context.
            system_instruction: Optional override for system prompt.
        
        Returns:
            The text response.
        """
        pass
