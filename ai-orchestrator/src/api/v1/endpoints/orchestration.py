from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
import structlog

from ...orchestration.workflow import AIOrchestrator, WorkflowConfig
from ...models.request_models import OrchestrationRequest, OrchestrationResponse
from ...core.auth import validate_token
from ...core.rate_limit import rate_limit

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/orchestration", tags=["AI Orchestration"])
security = HTTPBearer()

# Global orchestrator instance
orchestrator = AIOrchestrator(WorkflowConfig(
    enable_parallel_execution=True,
    timeout_seconds=60,
    max_retries=3,
    enable_caching=True
))

@router.post("/orchestrate", response_model=OrchestrationResponse)
@rate_limit(max_requests=10, window_seconds=60)
async def orchestrate_ai(
    request: OrchestrationRequest,
    background_tasks: BackgroundTasks,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Execute AI orchestration workflow with multiple agents
    
    This endpoint triggers the multi-agent AI system to:
    1. Analyze user context and requirements
    2. Generate personalized learning paths
    3. Provide wellness recommendations
    4. Create gamified missions
    5. Offer tutoring support
    6. Synthesize all results into cohesive response
    """
    
    try:
        # Validate authentication token
        user_data = await validate_token(credentials.credentials)
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        # Validate request
        if not request.user_id or not request.request_type:
            raise HTTPException(status_code=400, detail="Missing required fields: user_id, request_type")
        
        # Prepare orchestration input
        orchestration_input = {
            "user_id": request.user_id,
            "request_type": request.request_type,
            "user_profile": request.user_profile or {},
            "learning_goals": request.learning_goals or [],
            "subject_area": request.subject_area,
            "difficulty_level": request.difficulty_level or "intermediate",
            "behavioral_data": request.behavioral_data or {},
            "time_patterns": request.time_patterns or {},
            "recent_activity": request.recent_activity or [],
            "context": request.context or {}
        }
        
        # Execute orchestration
        logger.info("Starting AI orchestration", 
                   user_id=request.user_id, 
                   request_type=request.request_type)
        
        result = await orchestrator.orchestrate(orchestration_input)
        
        # Log completion
        logger.info("AI orchestration completed",
                   orchestration_id=result.get("orchestration_id"),
                   status=result.get("status"),
                   processing_time=result.get("processing_time_seconds"))
        
        # Add background task for analytics (optional)
        background_tasks.add_task(
            log_orchestration_analytics,
            orchestration_id=result.get("orchestration_id"),
            user_id=request.user_id,
            request_type=request.request_type,
            processing_time=result.get("processing_time_seconds"),
            agents_executed=result.get("agents_executed", [])
        )
        
        return OrchestrationResponse(
            orchestration_id=result.get("orchestration_id"),
            status=result.get("status"),
            results=result.get("results", {}),
            processing_time_seconds=result.get("processing_time_seconds"),
            agents_executed=result.get("agents_executed", []),
            user_id=request.user_id,
            timestamp=result.get("timestamp")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Orchestration failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal orchestration error")

@router.get("/status/{orchestration_id}")
async def get_orchestration_status(
    orchestration_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get status of a specific orchestration"""
    
    try:
        # Validate authentication
        user_data = await validate_token(credentials.credentials)
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        # Get orchestration status
        status = await orchestrator.get_orchestration_status(orchestration_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Orchestration not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get orchestration status", error=str(e))
        raise HTTPException(status_code=500, detail="Internal error")

@router.post("/cancel/{orchestration_id}")
async def cancel_orchestration(
    orchestration_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Cancel an ongoing orchestration"""
    
    try:
        # Validate authentication
        user_data = await validate_token(credentials.credentials)
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        # Cancel orchestration
        success = await orchestrator.cancel_orchestration(orchestration_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Could not cancel orchestration")
        
        return {"message": "Orchestration cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cancel orchestration", error=str(e))
        raise HTTPException(status_code=500, detail="Internal error")

@router.get("/agents")
async def get_agent_info(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get information about available AI agents"""
    
    try:
        # Validate authentication
        user_data = await validate_token(credentials.credentials)
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        agents_info = {
            "learning_designer": {
                "name": "Learning Designer Agent",
                "description": "Creates personalized learning paths and content recommendations",
                "capabilities": [
                    "Learning style analysis",
                    "Curriculum design",
                    "Content sequencing",
                    "Difficulty adaptation"
                ],
                "model": "GPT-4 Turbo"
            },
            "tutor_copilot": {
                "name": "Tutor Copilot Agent",
                "description": "Provides real-time tutoring assistance and explanations",
                "capabilities": [
                    "Step-by-step problem solving",
                    "Concept explanations",
                    "Hint generation",
                    "Scaffolding support"
                ],
                "model": "Claude-3 Sonnet"
            },
            "wellness_analyst": {
                "name": "Wellness Analyst Agent",
                "description": "Monitors student well-being and provides wellness recommendations",
                "capabilities": [
                    "Stress level detection",
                    "Engagement analysis",
                    "Break recommendations",
                    "Motivation assessment"
                ],
                "model": "GPT-4 Turbo"
            },
            "mission_engine": {
                "name": "Mission Engine Agent",
                "description": "Creates gamified missions and challenges",
                "capabilities": [
                    "Mission generation",
                    "Difficulty calibration",
                    "Progress tracking",
                    "Achievement design"
                ],
                "model": "Gemini Pro"
            }
        }
        
        return {
            "agents": agents_info,
            "workflow_graph": orchestrator.workflow_graph,
            "configuration": {
                "parallel_execution": True,
                "timeout_seconds": 60,
                "max_retries": 3
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get agent info", error=str(e))
        raise HTTPException(status_code=500, detail="Internal error")

async def log_orchestration_analytics(
    orchestration_id: str,
    user_id: str,
    request_type: str,
    processing_time: float,
    agents_executed: list
):
    """Background task to log orchestration analytics"""
    
    try:
        # This would integrate with your analytics system
        logger.info("Orchestration analytics",
                   orchestration_id=orchestration_id,
                   user_id=user_id,
                   request_type=request_type,
                   processing_time=processing_time,
                   agents_executed=agents_executed)
        
        # Store in database or analytics service
        # await analytics_service.log_orchestration_metrics(...)
        
    except Exception as e:
        logger.error("Failed to log orchestration analytics", error=str(e))
