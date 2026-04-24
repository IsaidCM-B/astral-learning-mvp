from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime
from dataclasses import dataclass

from ..agents.learning_designer import LearningDesignerAgent
from ..agents.tutor_copilot import TutorCopilotAgent
from ..agents.wellness_analyst import WellnessAnalystAgent
from ..agents.mission_engine import MissionEngineAgent
from ..models.orchestration_models import OrchestrationState, AgentResult
import structlog

logger = structlog.get_logger()

@dataclass
class WorkflowConfig:
    """Configuration for orchestration workflow"""
    enable_parallel_execution: bool = True
    timeout_seconds: int = 60
    max_retries: int = 3
    enable_caching: bool = True

class AIOrchestrator:
    """Main orchestration engine for multi-agent AI system"""
    
    def __init__(self, config: WorkflowConfig = None):
        self.config = config or WorkflowConfig()
        self.logger = logger.bind(component="ai_orchestrator")
        
        # Initialize agents
        self.agents = {
            'learning_designer': LearningDesignerAgent(),
            'tutor_copilot': TutorCopilotAgent(),
            'wellness_analyst': WellnessAnalystAgent(),
            'mission_engine': MissionEngineAgent()
        }
        
        # Define workflow graph
        self.workflow_graph = self._create_workflow_graph()
        
    def _create_workflow_graph(self) -> Dict[str, List[str]]:
        """Define the workflow graph with agent dependencies"""
        
        return {
            'entry_point': ['context_analyzer', 'wellness_analyst'],
            'context_analyzer': ['learning_designer'],
            'wellness_analyst': ['mission_engine'],
            'learning_designer': ['mission_engine'],
            'mission_engine': ['tutor_copilot'],
            'tutor_copilot': ['result_synthesizer'],
            'result_synthesizer': []
        }
    
    async def orchestrate(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute multi-agent orchestration workflow"""
        
        start_time = datetime.utcnow()
        orchestration_id = f"orch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            self.logger.info("Starting orchestration", 
                           orchestration_id=orchestration_id,
                           user_id=user_input.get('user_id'))
            
            # Initialize orchestration state
            state = OrchestrationState(
                orchestration_id=orchestration_id,
                user_input=user_input,
                start_time=start_time,
                agent_results={},
                workflow_status="running"
            )
            
            # Execute workflow
            final_state = await self._execute_workflow(state)
            
            # Calculate metrics
            total_time = (datetime.utcnow() - start_time).total_seconds()
            
            response = {
                "orchestration_id": orchestration_id,
                "status": final_state.workflow_status,
                "results": final_state.agent_results,
                "processing_time_seconds": total_time,
                "agents_executed": list(final_state.agent_results.keys()),
                "user_id": user_input.get('user_id')
            }
            
            self.logger.info("Orchestration completed",
                           orchestration_id=orchestration_id,
                           processing_time=total_time,
                           agents_executed=len(response["agents_executed"]))
            
            return response
            
        except Exception as e:
            self.logger.error("Orchestration failed",
                            orchestration_id=orchestration_id,
                            error=str(e))
            
            return {
                "orchestration_id": orchestration_id,
                "status": "failed",
                "error": str(e),
                "processing_time_seconds": (datetime.utcnow() - start_time).total_seconds()
            }
    
    async def _execute_workflow(self, state: OrchestrationState) -> OrchestrationState:
        """Execute the workflow graph"""
        
        # Start with entry point
        current_agents = self.workflow_graph['entry_point']
        completed_agents = set()
        
        while current_agents:
            # Execute agents in parallel if enabled
            if self.config.enable_parallel_execution:
                await self._execute_agents_parallel(current_agents, state)
            else:
                await self._execute_agents_sequential(current_agents, state)
            
            # Mark agents as completed
            completed_agents.update(current_agents)
            
            # Find next agents to execute
            next_agents = []
            for agent in current_agents:
                # Find agents that depend on this agent
                for next_agent, dependencies in self.workflow_graph.items():
                    if agent in dependencies and next_agent not in completed_agents:
                        # Check if all dependencies are satisfied
                        if all(dep in completed_agents for dep in dependencies):
                            next_agents.append(next_agent)
            
            current_agents = list(set(next_agents))
        
        # Final result synthesis
        state = await self._synthesize_results(state)
        state.workflow_status = "completed"
        
        return state
    
    async def _execute_agents_parallel(self, agents: List[str], state: OrchestrationState):
        """Execute multiple agents in parallel"""
        
        tasks = []
        for agent_name in agents:
            task = self._execute_single_agent(agent_name, state)
            tasks.append(task)
        
        # Wait for all agents to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            agent_name = agents[i]
            if isinstance(result, Exception):
                self.logger.error(f"Agent {agent_name} failed", error=str(result))
                state.agent_results[agent_name] = AgentResult(
                    agent_name=agent_name,
                    status="failed",
                    error=str(result),
                    execution_time=0
                )
            else:
                state.agent_results[agent_name] = result
    
    async def _execute_agents_sequential(self, agents: List[str], state: OrchestrationState):
        """Execute agents sequentially"""
        
        for agent_name in agents:
            result = await self._execute_single_agent(agent_name, state)
            state.agent_results[agent_name] = result
    
    async def _execute_single_agent(self, agent_name: str, state: OrchestrationState) -> AgentResult:
        """Execute a single agent"""
        
        start_time = datetime.utcnow()
        
        try:
            agent = self.agents[agent_name]
            
            # Prepare input for agent
            agent_input = self._prepare_agent_input(agent_name, state)
            
            # Execute agent with timeout
            result = await asyncio.wait_for(
                agent.process(agent_input),
                timeout=self.config.timeout_seconds
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return AgentResult(
                agent_name=agent_name,
                status="success",
                result=result,
                execution_time=execution_time,
                timestamp=datetime.utcnow()
            )
            
        except asyncio.TimeoutError:
            self.logger.error(f"Agent {agent_name} timed out")
            return AgentResult(
                agent_name=agent_name,
                status="timeout",
                error=f"Agent timed out after {self.config.timeout_seconds} seconds",
                execution_time=self.config.timeout_seconds
            )
        except Exception as e:
            self.logger.error(f"Agent {agent_name} failed", error=str(e))
            return AgentResult(
                agent_name=agent_name,
                status="failed",
                error=str(e),
                execution_time=(datetime.utcnow() - start_time).total_seconds()
            )
    
    def _prepare_agent_input(self, agent_name: str, state: OrchestrationState) -> Dict[str, Any]:
        """Prepare input data for specific agent"""
        
        base_input = state.user_input.copy()
        
        # Add context from previous agents
        agent_input = {
            **base_input,
            "orchestration_id": state.orchestration_id,
            "previous_results": state.agent_results
        }
        
        # Agent-specific input preparation
        if agent_name == 'learning_designer':
            agent_input.update({
                "context_analysis": state.agent_results.get('context_analyzer', {}).get('result', {}),
                "similar_profiles": self._get_similar_profiles(base_input.get('user_id'))
            })
        elif agent_name == 'tutor_copilot':
            agent_input.update({
                "learning_path": state.agent_results.get('learning_designer', {}).get('result', {}),
                "mission_data": state.agent_results.get('mission_engine', {}).get('result', {}),
                "wellness_state": state.agent_results.get('wellness_analyst', {}).get('result', {})
            })
        elif agent_name == 'mission_engine':
            agent_input.update({
                "learning_path": state.agent_results.get('learning_designer', {}).get('result', {}),
                "wellness_recommendations": state.agent_results.get('wellness_analyst', {}).get('result', {})
            })
        elif agent_name == 'wellness_analyst':
            agent_input.update({
                "behavioral_data": base_input.get('behavioral_data', {}),
                "time_patterns": base_input.get('time_patterns', {}),
                "recent_activity": base_input.get('recent_activity', [])
            })
        
        return agent_input
    
    def _get_similar_profiles(self, user_id: str) -> List[Dict[str, Any]]:
        """Get similar user profiles (placeholder for vector store integration)"""
        # This would integrate with the vector store to find similar profiles
        return []
    
    async def _synthesize_results(self, state: OrchestrationState) -> OrchestrationState:
        """Synthesize results from all agents into final response"""
        
        try:
            # Create synthesis prompt
            synthesis_prompt = self._create_synthesis_prompt(state)
            
            # Use learning designer agent for synthesis (or create dedicated synthesizer)
            synthesizer = self.agents['learning_designer']
            
            synthesis_input = {
                "type": "result_synthesis",
                "agent_results": state.agent_results,
                "original_request": state.user_input,
                "synthesis_prompt": synthesis_prompt
            }
            
            synthesis_result = await synthesizer.process(synthesis_input)
            
            # Add synthesis to results
            state.agent_results['result_synthesizer'] = AgentResult(
                agent_name='result_synthesizer',
                status='success',
                result=synthesis_result,
                execution_time=0,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error("Result synthesis failed", error=str(e))
            # Add failed synthesis result
            state.agent_results['result_synthesizer'] = AgentResult(
                agent_name='result_synthesizer',
                status='failed',
                error=str(e),
                execution_time=0
            )
        
        return state
    
    def _create_synthesis_prompt(self, state: OrchestrationState) -> str:
        """Create prompt for result synthesis"""
        
        agent_results = state.agent_results
        
        prompt = f"""
        Synthesize the results from multiple AI agents into a cohesive response for the user.
        
        ORIGINAL REQUEST: {state.user_input.get('request_type', 'unknown')}
        USER ID: {state.user_input.get('user_id', 'unknown')}
        
        AGENT RESULTS:
        """
        
        for agent_name, result in agent_results.items():
            if result.status == 'success' and agent_name != 'result_synthesizer':
                prompt += f"\n{agent_name.upper()}:\n{result.get('result', {})}\n"
        
        prompt += """
        
        SYNTHESIS INSTRUCTIONS:
        1. Combine insights from all successful agents
        2. Resolve any conflicts between agent recommendations
        3. Prioritize recommendations based on user context
        4. Create a cohesive, actionable response
        5. Include specific next steps for the user
        6. Highlight the most important insights
        
        Format the response as a comprehensive learning recommendation that integrates
        all AI agent insights into a unified plan.
        """
        
        return prompt
    
    async def get_orchestration_status(self, orchestration_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific orchestration (placeholder for persistence)"""
        # This would integrate with a database or cache to track orchestration status
        return None
    
    async def cancel_orchestration(self, orchestration_id: str) -> bool:
        """Cancel an ongoing orchestration (placeholder)"""
        # This would implement cancellation logic
        return True
