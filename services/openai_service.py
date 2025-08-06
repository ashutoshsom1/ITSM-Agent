import os
import json
import asyncio
from typing import List, Dict, Optional, Any
import openai
from datetime import datetime

class OpenAIService:
    """
    Handles all OpenAI GPT interactions for conversation and image analysis
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")  # For Azure OpenAI
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
        
        if self.endpoint:
            # Azure OpenAI configuration
            openai.api_type = "azure"
            openai.api_base = self.endpoint
            openai.api_version = self.api_version
            openai.api_key = self.api_key
        else:
            # Standard OpenAI configuration
            openai.api_key = self.api_key
    
    async def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict],
        user_profile: Dict,
        context_analysis: Dict
    ) -> str:
        """Generate AI response based on context and history"""
        
        # Build system prompt based on user profile and context
        system_prompt = self._build_system_prompt(user_profile, context_analysis)
        
        # Build conversation context
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add relevant conversation history
        for conv in conversation_history[-10:]:  # Last 10 messages for context
            messages.append({
                "role": conv["role"],
                "content": conv["message"]
            })
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        try:
            if self.endpoint:
                # Azure OpenAI
                response = await self._call_azure_openai(messages)
            else:
                # Standard OpenAI
                response = await self._call_openai(messages)
            
            return response
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return self._get_fallback_response(user_message, context_analysis)
    
    async def generate_image_response(
        self,
        image_analysis: Dict,
        context: str,
        conversation_history: List[Dict],
        user_profile: Dict
    ) -> str:
        """Generate response based on image analysis"""
        
        # Build context for image response
        analysis_summary = self._summarize_image_analysis(image_analysis)
        
        system_prompt = f"""
        You are an AI assistant helping a user understand an image they shared.
        
        User Profile: {user_profile.get('preferences', {})}
        
        Image Analysis Results:
        {analysis_summary}
        
        Provide helpful, actionable insights based on the image analysis.
        If issues are detected, offer step-by-step solutions.
        Be encouraging and supportive in your response.
        """
        
        user_prompt = f"""
        I shared an image with you. {context or 'Please help me understand what you see and provide guidance.'}
        
        Based on your analysis, what insights can you provide?
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            if self.endpoint:
                response = await self._call_azure_openai(messages)
            else:
                response = await self._call_openai(messages)
            
            return response
            
        except Exception as e:
            print(f"Error generating image response: {e}")
            return "I can see your image, but I'm having trouble analyzing it right now. Could you describe what you're seeing or what specific help you need?"
    
    def _build_system_prompt(self, user_profile: Dict, context_analysis: Dict) -> str:
        """Build personalized system prompt"""
        preferences = user_profile.get("preferences", {})
        common_topics = user_profile.get("common_topics", [])
        
        prompt = f"""
        You are an advanced AI assistant with the following capabilities:
        
        🧠 CONTEXTUAL MEMORY: You remember previous conversations and learn from user interactions
        👁️ VISUAL ANALYSIS: You can analyze images and screenshots to provide guidance
        🤝 HUMAN HANDOFF: You can connect users with human agents when needed
        ✨ PROACTIVE INTELLIGENCE: You anticipate user needs and provide helpful suggestions
        
        USER PROFILE:
        - Communication Style: {preferences.get('communication_style', 'friendly')}
        - Technical Level: {preferences.get('technical_level', 'intermediate')}
        - Response Length: {preferences.get('response_length', 'medium')}
        - Common Topics: {', '.join(common_topics) if common_topics else 'General'}
        - Interaction Count: {user_profile.get('interaction_count', 0)}
        
        CONTEXT ANALYSIS:
        - Sentiment: {context_analysis.get('sentiment', {}).get('score', 'neutral')}
        - Complexity: {context_analysis.get('complexity', 'normal')}
        - Topics: {', '.join(context_analysis.get('topics', []))}
        
        PERSONALITY GUIDELINES:
        - Be helpful, encouraging, and solution-focused
        - Adapt your communication style to match user preferences
        - Proactively suggest next steps and related resources
        - Celebrate user achievements and progress
        - When you detect frustration, offer human handoff options
        - Remember details from previous conversations to provide personalized help
        
        RESPONSE GUIDELINES:
        - Keep responses {preferences.get('response_length', 'medium')} length
        - Match {preferences.get('communication_style', 'friendly')} communication style
        - Adjust technical depth for {preferences.get('technical_level', 'intermediate')} level
        - Include relevant proactive suggestions when appropriate
        - Offer to analyze images or screenshots if the user mentions visual problems
        
        Current timestamp: {datetime.now().isoformat()}
        """
        
        return prompt
    
    def _summarize_image_analysis(self, analysis: Dict) -> str:
        """Summarize image analysis results for prompt"""
        summary = []
        
        if analysis.get("description"):
            summary.append(f"Description: {analysis['description']}")
        
        if analysis.get("detected_text"):
            summary.append(f"Text Found: {analysis['detected_text']}")
        
        if analysis.get("objects"):
            objects = ", ".join(analysis["objects"])
            summary.append(f"Objects Detected: {objects}")
        
        if analysis.get("detected_issues"):
            issues = ", ".join(analysis["detected_issues"])
            summary.append(f"Potential Issues: {issues}")
        
        if analysis.get("categories"):
            categories = ", ".join(analysis["categories"])
            summary.append(f"Categories: {categories}")
        
        return "\n".join(summary) if summary else "Basic image analysis completed"
    
    async def _call_azure_openai(self, messages: List[Dict]) -> str:
        """Call Azure OpenAI API"""
        try:
            response = openai.ChatCompletion.create(
                engine=self.deployment_name,
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise Exception(f"Azure OpenAI API error: {e}")
    
    async def _call_openai(self, messages: List[Dict]) -> str:
        """Call standard OpenAI API"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise Exception(f"OpenAI API error: {e}")
    
    def _get_fallback_response(self, user_message: str, context_analysis: Dict) -> str:
        """Generate fallback response when AI service is unavailable"""
        sentiment = context_analysis.get("sentiment", {})
        
        if sentiment.get("score", 0) < -0.5:
            return "I understand you're experiencing some frustration. While I'm having technical difficulties right now, I'd be happy to connect you with a human agent who can provide immediate assistance. Would you like me to arrange that?"
        
        if any(word in user_message.lower() for word in ["error", "problem", "issue", "help"]):
            return "I want to help you with that issue, but I'm experiencing some technical difficulties. In the meantime, you can try sharing a screenshot of the problem, or I can connect you with a human agent for immediate assistance."
        
        return "I'm experiencing some technical difficulties right now, but I'm still here to help! You can share screenshots for visual analysis, or I can connect you with a human agent if you need immediate assistance."
    
    async def generate_proactive_suggestions(
        self,
        user_profile: Dict,
        recent_activity: List[Dict],
        context: Dict = None
    ) -> List[Dict]:
        """Generate proactive suggestions based on user patterns"""
        
        # Analyze patterns in recent activity
        common_themes = self._extract_themes(recent_activity)
        user_preferences = user_profile.get("preferences", {})
        
        suggestions = []
        
        # Pattern-based suggestions
        if "troubleshooting" in common_themes:
            suggestions.append({
                "type": "workflow",
                "title": "Create a troubleshooting checklist",
                "description": "Based on your recent issues, I can help you create a personalized troubleshooting workflow",
                "action": "create_checklist",
                "priority": "high"
            })
        
        if "learning" in common_themes:
            suggestions.append({
                "type": "resource",
                "title": "Recommended learning resources",
                "description": "I found some resources that match your learning style and interests",
                "action": "show_resources",
                "priority": "medium"
            })
        
        # Time-based suggestions
        current_hour = datetime.now().hour
        if 9 <= current_hour <= 17:  # Work hours
            suggestions.append({
                "type": "productivity",
                "title": "Daily productivity check",
                "description": "Would you like me to help prioritize your tasks for today?",
                "action": "daily_planning",
                "priority": "low"
            })
        
        return suggestions
    
    def _extract_themes(self, activity: List[Dict]) -> List[str]:
        """Extract common themes from user activity"""
        themes = []
        
        # Simple keyword-based theme extraction
        for item in activity:
            message = item.get("message", "").lower()
            
            if any(word in message for word in ["error", "problem", "fix", "issue"]):
                themes.append("troubleshooting")
            
            if any(word in message for word in ["learn", "how", "tutorial", "guide"]):
                themes.append("learning")
            
            if any(word in message for word in ["schedule", "plan", "organize", "task"]):
                themes.append("planning")
        
        return list(set(themes))
