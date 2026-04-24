from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import structlog

logger = structlog.get_logger()

class BaseAgent(ABC):
    """Base class for all AI agents in the orchestration system"""
    
    def __init__(self, name: str, model_provider: str = "openai"):
        self.name = name
        self.model_provider = model_provider
        self.logger = logger.bind(agent=name)
        
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data and return response"""
        pass
    
    @abstractmethod
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for the agent"""
        pass
    
    async def log_interaction(self, input_data: Dict[str, Any], 
                            response: Dict[str, Any], 
                            processing_time: float):
        """Log agent interaction for monitoring"""
        self.logger.info(
            "agent_interaction",
            agent=self.name,
            input_type=input_data.get("type", "unknown"),
            response_type=response.get("type", "unknown"),
            processing_time=processing_time
        )
