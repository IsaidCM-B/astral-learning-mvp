from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime

from .base_agent import BaseAgent
from ..llm.llm_client import LLMClient
from ..vector_store.vector_client import VectorStoreClient
from ..models.learning_models import LearningPath, LearningObjective, ContentRecommendation

class LearningDesignerAgent(BaseAgent):
    """Agent responsible for designing personalized learning paths and content"""
    
    def __init__(self, model_provider: str = "openai", model_name: str = "gpt-4-turbo"):
        super().__init__("learning_designer", model_provider)
        self.llm_client = LLMClient(provider=model_provider, model=model_name)
        self.vector_store = VectorStoreClient()
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process user data and generate personalized learning path"""
        start_time = datetime.utcnow()
        
        try:
            # Validate input
            if not await self.validate_input(input_data):
                raise ValueError("Invalid input data for learning designer")
            
            user_profile = input_data.get("user_profile", {})
            learning_goals = input_data.get("learning_goals", [])
            subject_area = input_data.get("subject_area", "")
            difficulty_level = input_data.get("difficulty_level", "intermediate")
            
            # Gather context from vector store
            similar_profiles = await self.vector_store.find_similar_profiles(
                user_profile, limit=5
            )
            
            # Generate learning path
            learning_path = await self._generate_learning_path(
                user_profile=user_profile,
                learning_goals=learning_goals,
                subject_area=subject_area,
                difficulty_level=difficulty_level,
                similar_profiles=similar_profiles
            )
            
            # Generate content recommendations
            content_recommendations = await self._generate_content_recommendations(
                learning_path=learning_path,
                user_profile=user_profile
            )
            
            response = {
                "type": "learning_design",
                "learning_path": learning_path.dict(),
                "content_recommendations": [rec.dict() for rec in content_recommendations],
                "personalization_factors": self._extract_personalization_factors(user_profile),
                "estimated_completion_time": self._estimate_completion_time(learning_path)
            }
            
            # Log interaction
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            await self.log_interaction(input_data, response, processing_time)
            
            return response
            
        except Exception as e:
            self.logger.error("Learning designer processing failed", error=str(e))
            return {
                "type": "error",
                "error": "Failed to generate learning design",
                "details": str(e)
            }
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for learning designer agent"""
        required_fields = ["user_profile", "learning_goals"]
        
        for field in required_fields:
            if field not in input_data:
                self.logger.error(f"Missing required field: {field}")
                return False
        
        user_profile = input_data.get("user_profile", {})
        if not user_profile.get("learning_style") or not user_profile.get("grade_level"):
            self.logger.error("User profile missing required information")
            return False
        
        learning_goals = input_data.get("learning_goals", [])
        if not isinstance(learning_goals, list) or len(learning_goals) == 0:
            self.logger.error("Learning goals must be a non-empty list")
            return False
        
        return True
    
    async def _generate_learning_path(self, user_profile: Dict[str, Any], 
                                    learning_goals: List[str],
                                    subject_area: str,
                                    difficulty_level: str,
                                    similar_profiles: List[Dict]) -> LearningPath:
        """Generate personalized learning path using LLM"""
        
        # Create context for LLM
        context_prompt = self._build_learning_path_prompt(
            user_profile=user_profile,
            learning_goals=learning_goals,
            subject_area=subject_area,
            difficulty_level=difficulty_level,
            similar_profiles=similar_profiles
        )
        
        # Generate learning path with LLM
        llm_response = await self.llm_client.generate_response(
            prompt=context_prompt,
            max_tokens=2000,
            temperature=0.7
        )
        
        # Parse and structure the response
        learning_path = self._parse_learning_path_response(llm_response, user_profile)
        
        return learning_path
    
    def _build_learning_path_prompt(self, user_profile: Dict[str, Any],
                                  learning_goals: List[str],
                                  subject_area: str,
                                  difficulty_level: str,
                                  similar_profiles: List[Dict]) -> str:
        """Build comprehensive prompt for learning path generation"""
        
        prompt = f"""
        You are an expert learning designer creating a personalized learning path for a student.

        STUDENT PROFILE:
        - Learning Style: {user_profile.get('learning_style', 'unknown')}
        - Grade Level: {user_profile.get('grade_level', 'unknown')}
        - Cognitive Traits: {user_profile.get('cognitive_traits', {})}
        - Attention Span: {user_profile.get('attention_span', 'unknown')}
        - Preferred Subjects: {user_profile.get('preferred_subjects', [])}

        LEARNING GOALS:
        {chr(10).join(f"- {goal}" for goal in learning_goals)}

        SUBJECT AREA: {subject_area}
        DIFFICULTY LEVEL: {difficulty_level}

        SIMILAR STUDENT PROFILES:
        {self._format_similar_profiles(similar_profiles)}

        INSTRUCTIONS:
        Create a structured learning path that:
        1. Aligns with the student's learning style and cognitive traits
        2. Addresses all learning goals progressively
        3. Includes appropriate difficulty progression
        4. Incorporates engagement strategies based on similar profiles
        5. Provides clear learning objectives for each stage
        6. Includes assessment points to track progress

        RESPONSE FORMAT (JSON):
        {{
            "title": "Learning Path Title",
            "description": "Brief description of the learning journey",
            "estimated_duration_weeks": 8,
            "learning_stages": [
                {{
                    "stage_id": "stage_1",
                    "title": "Stage Title",
                    "description": "Stage description",
                    "learning_objectives": ["objective 1", "objective 2"],
                    "estimated_duration_days": 7,
                    "difficulty_level": "beginner",
                    "prerequisites": [],
                    "activities": [
                        {{
                            "activity_id": "activity_1",
                            "title": "Activity Title",
                            "type": "reading|video|practice|project",
                            "estimated_duration_minutes": 30,
                            "description": "Activity description"
                        }}
                    ],
                    "assessment": {{
                        "type": "quiz|project|presentation",
                        "description": "Assessment description",
                        "passing_criteria": "80% score"
                    }}
                }}
            ]
        }}

        Generate a comprehensive, personalized learning path following the exact JSON format above.
        """
        
        return prompt
    
    def _format_similar_profiles(self, similar_profiles: List[Dict]) -> str:
        """Format similar profiles for prompt context"""
        if not similar_profiles:
            return "No similar profiles found."
        
        formatted = []
        for i, profile in enumerate(similar_profiles[:3], 1):
            formatted.append(f"""
            Profile {i}:
            - Learning Style: {profile.get('learning_style', 'unknown')}
            - Successful Activities: {profile.get('successful_activities', [])}
            - Engagement Patterns: {profile.get('engagement_patterns', {})}
            """)
        
        return "\n".join(formatted)
    
    def _parse_learning_path_response(self, llm_response: str, 
                                    user_profile: Dict[str, Any]) -> LearningPath:
        """Parse LLM response into structured LearningPath object"""
        
        try:
            # Extract JSON from response
            import json
            import re
            
            # Find JSON block in response
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in LLM response")
            
            path_data = json.loads(json_match.group())
            
            # Create LearningPath object
            learning_path = LearningPath(
                title=path_data["title"],
                description=path_data["description"],
                estimated_duration_weeks=path_data["estimated_duration_weeks"],
                user_id=user_profile.get("id"),
                created_at=datetime.utcnow(),
                stages=[
                    LearningObjective(**stage) 
                    for stage in path_data["learning_stages"]
                ]
            )
            
            return learning_path
            
        except Exception as e:
            self.logger.error("Failed to parse learning path response", error=str(e))
            # Return default learning path
            return self._create_default_learning_path(user_profile)
    
    def _create_default_learning_path(self, user_profile: Dict[str, Any]) -> LearningPath:
        """Create a default learning path if parsing fails"""
        
        default_stage = LearningObjective(
            stage_id="default_stage",
            title="Introduction to Learning",
            description="Getting started with personalized learning",
            learning_objectives=["Understand learning platform", "Complete first activity"],
            estimated_duration_days=7,
            difficulty_level="beginner",
            prerequisites=[],
            activities=[],
            assessment=None
        )
        
        return LearningPath(
            title="Default Learning Path",
            description="Basic learning path to get started",
            estimated_duration_weeks=4,
            user_id=user_profile.get("id"),
            created_at=datetime.utcnow(),
            stages=[default_stage]
        )
    
    async def _generate_content_recommendations(self, learning_path: LearningPath,
                                             user_profile: Dict[str, Any]) -> List[ContentRecommendation]:
        """Generate content recommendations based on learning path"""
        
        recommendations = []
        
        for stage in learning_path.stages:
            for activity in stage.activities:
                # Generate content recommendation for each activity
                recommendation = await self._generate_single_recommendation(
                    activity=activity,
                    user_profile=user_profile,
                    stage_context=stage
                )
                
                if recommendation:
                    recommendations.append(recommendation)
        
        return recommendations
    
    async def _generate_single_recommendation(self, activity: Dict,
                                           user_profile: Dict[str, Any],
                                           stage_context: LearningObjective) -> Optional[ContentRecommendation]:
        """Generate single content recommendation"""
        
        try:
            prompt = f"""
            Recommend specific learning content for this activity:
            
            ACTIVITY: {activity.get('title', 'Unknown')}
            TYPE: {activity.get('type', 'unknown')}
            DURATION: {activity.get('estimated_duration_minutes', 30)} minutes
            
            STUDENT PROFILE:
            - Learning Style: {user_profile.get('learning_style', 'unknown')}
            - Grade Level: {user_profile.get('grade_level', 'unknown')}
            - Interests: {user_profile.get('interests', [])}
            
            STAGE CONTEXT: {stage_context.title}
            
            Recommend 1-3 specific resources (videos, articles, exercises, etc.) that match:
            1. The activity type and duration
            2. Student's learning style
            3. Appropriate difficulty level
            
            Return as JSON list of recommendations with title, type, url, and description.
            """
            
            response = await self.llm_client.generate_response(
                prompt=prompt,
                max_tokens=500,
                temperature=0.5
            )
            
            # Parse recommendations (simplified for this example)
            return ContentRecommendation(
                activity_id=activity.get("activity_id", "unknown"),
                title="Recommended Resource",
                type="video",
                url="https://example.com/resource",
                description="Description of recommended resource",
                estimated_duration_minutes=activity.get("estimated_duration_minutes", 30),
                difficulty_level=stage_context.difficulty_level
            )
            
        except Exception as e:
            self.logger.error("Failed to generate content recommendation", error=str(e))
            return None
    
    def _extract_personalization_factors(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key personalization factors from user profile"""
        
        return {
            "learning_style": user_profile.get("learning_style"),
            "cognitive_traits": user_profile.get("cognitive_traits", {}),
            "attention_span": user_profile.get("attention_span"),
            "preferred_difficulty": user_profile.get("preferred_difficulty", "adaptive"),
            "engagement_triggers": user_profile.get("engagement_triggers", [])
        }
    
    def _estimate_completion_time(self, learning_path: LearningPath) -> Dict[str, Any]:
        """Estimate completion time for learning path"""
        
        total_days = sum(stage.estimated_duration_days for stage in learning_path.stages)
        total_hours = total_days * 1.5  # Assuming 1.5 hours per day average
        
        return {
            "estimated_total_days": total_days,
            "estimated_total_hours": total_hours,
            "recommended_pace": f"{total_hours / 7:.1f} hours per week",
            "completion_probability": 0.85  # Based on similar profiles
        }
