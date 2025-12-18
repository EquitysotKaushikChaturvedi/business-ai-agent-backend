from app.llm.base import BaseLLM
from app.core.config import settings
from typing import List, Dict, Optional
import logging
import asyncio
from openai import AsyncOpenAI
import traceback

logger = logging.getLogger(__name__)

class OpenAILLM(BaseLLM):
    """
    Production-ready OpenAI Provider.
    """
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY is missing. AI will fail.")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            # Configurable model, default to high-performance/cost-effective mix if needed
            self.model_name = "gpt-4o" 

    async def generate_response(
        self, 
        prompt: str, 
        history: List[Dict[str, str]] = [], 
        context: str = "",
        system_instruction: Optional[str] = None
    ) -> str:
        
        if not self.client:
            return "Error: OPENAI_API_KEY is missing in environment variables."

        # Construct System Prompt (Same strict behavior as Gemini)
        default_system = (
            f"Role: You are an intelligent business assistant. \n"
            f"Context: Use the following business knowledge to answer: \n{context}\n"
            f"Instructions:\n"
            f"1. Understand the user's question first.\n"
            f"2. If the answer is not in the context or chat history, ask for clarification.\n"
            f"3. Do NOT hallucinate. Stick to facts.\n"
            f"4. Be professional but human-like. Vary your greetings.\n"
            f"5. IMPORTANT: If unclear, ask a question back.\n" 
        )

        if system_instruction:
            # If custom instruction provided, overlay it
            full_system_prompt = system_instruction
        else:
            full_system_prompt = default_system

        # Prepare messages
        messages = [{"role": "system", "content": full_system_prompt}]
        
        # Add history
        # Ensure strict role compliance (user, assistant)
        for msg in history:
            role = msg.get('role', 'user')
            content = msg.get('content', '').strip()
            if not content:
                continue
            if role not in ['user', 'assistant', 'system']:
                role = 'user' # Fallback
            messages.append({"role": role, "content": content})

        # Add current prompt
        messages.append({"role": "user", "content": prompt})

        # Retry Logic for Rate Limits / Transient Errors
        retries = 3
        
        for attempt in range(retries):
            try:
                logger.info(f"Sending to OpenAI ({self.model_name}). Attempt {attempt+1}")
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000
                )
                return response.choices[0].message.content
            except Exception as e:
                error_str = str(e)
                logger.error(f"OpenAI Error (Attempt {attempt+1}): {error_str}")
                
                # Check for rate limits or server errors
                if "429" in error_str or "500" in error_str or "503" in error_str:
                    if attempt < retries - 1:
                        wait = 2 * (attempt + 1)
                        logger.warning(f"Retrying in {wait}s...")
                        await asyncio.sleep(wait)
                        continue
                
                # Fatal or max retries reached
                return "I apologize, but I am currently experiencing connection issues. Please try again later."
