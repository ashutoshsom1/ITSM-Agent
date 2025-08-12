import os
import json
import asyncio
from typing import List, Dict, Optional, Any
from openai import AsyncAzureOpenAI, AsyncOpenAI
from datetime import datetime

class OpenAIService:
    """
    Handles all OpenAI GPT interactions for conversation and image analysis
    """
    
    def __init__(self):
        self.api_key = os.getenv("AZURE_OPENAI_KEY") or os.getenv("OPENAI_API_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")  # For Azure OpenAI
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-35-turbo-16k")
        
        print(f"OpenAI Service Initialization:")
        print(f"API Key: {'***' + self.api_key[-4:] if self.api_key else 'None'}")
        print(f"Endpoint: {self.endpoint}")
        print(f"API Version: {self.api_version}")
        print(f"Deployment: {self.deployment_name}")
        
        if self.endpoint and self.api_key:
            # Azure OpenAI configuration
            self.client = AsyncAzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.endpoint
            )
            self.is_azure = True
            print("✓ Azure OpenAI client initialized successfully")
        elif self.api_key:
            # Standard OpenAI configuration
            self.client = AsyncOpenAI(api_key=self.api_key)
            self.is_azure = False
            print("✓ Standard OpenAI client initialized successfully")
        else:
            self.client = None
            self.is_azure = False
            print("⚠️ Warning: No OpenAI credentials found. Using fallback responses.")
    
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
            print(f"Generating response - Client available: {self.client is not None}")
            print(f"Is Azure: {self.is_azure}")
            print(f"User message: {user_message[:50]}...")
            
            if self.client is None:
                print("No client available, using fallback")
                return self._get_fallback_response(user_message, context_analysis)
            
            if self.is_azure:
                # Azure OpenAI
                print("Calling Azure OpenAI...")
                response = await self._call_azure_openai(messages)
            else:
                # Standard OpenAI
                print("Calling Standard OpenAI...")
                response = await self._call_openai(messages)
            
            print(f"Response received: {response[:100]}...")
            return response
            
        except Exception as e:
            print(f"Error generating response: {e}")
            print(f"Exception type: {type(e)}")
            import traceback
            traceback.print_exc()
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
        
        IMPORTANT: The user has already uploaded an image and I have analyzed it using Azure Computer Vision. 
        You do NOT need to ask them to upload an image - it has already been processed.
        
        User Profile: {user_profile.get('preferences', {})}
        
        DETAILED IMAGE ANALYSIS RESULTS:
        {analysis_summary}
        
        Based on this comprehensive analysis, provide helpful, actionable insights about what you can see in the image.
        If issues are detected, offer step-by-step solutions.
        Be encouraging and supportive in your response.
        Reference specific details from the analysis above.
        """
        
        user_prompt = f"""
        I just shared an image with you and you've analyzed it. {context or 'Please help me understand what you see and provide guidance based on your analysis.'}
        
        Based on the detailed analysis results above, what insights can you provide about my image?
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            if self.client is None:
                return "I can see you've shared an image, but I'm having trouble connecting to my AI service right now. Could you describe what you're seeing so I can still help you?"
            
            if self.is_azure:
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
        
        # Image basic info
        image_info = analysis.get("image_info", {})
        if image_info:
            summary.append(f"Image Details: {image_info.get('width', 'Unknown')}x{image_info.get('height', 'Unknown')} {image_info.get('format', 'Unknown format')}")
        
        # Main description
        if analysis.get("description"):
            summary.append(f"What I can see: {analysis['description']}")
            
        if analysis.get("confidence"):
            summary.append(f"Analysis confidence: {analysis['confidence']:.1%}")
        
        # Detected text (most important for Excel screenshot)
        if analysis.get("detected_text"):
            text = analysis['detected_text']
            if len(text) > 500:
                text = text[:500] + "... (truncated)"
            summary.append(f"Text content found: {text}")
        
        # Objects and tags
        if analysis.get("tags"):
            tags = analysis["tags"]
            if isinstance(tags, list) and len(tags) > 0:
                tag_names = [tag.get("name", str(tag)) if isinstance(tag, dict) else str(tag) for tag in tags[:10]]
                summary.append(f"Identified elements: {', '.join(tag_names)}")
        
        if analysis.get("objects"):
            objects = analysis["objects"]
            if isinstance(objects, list) and len(objects) > 0:
                obj_names = [obj.get("name", str(obj)) if isinstance(obj, dict) else str(obj) for obj in objects[:5]]
                summary.append(f"Objects detected: {', '.join(obj_names)}")
        
        # Categories
        if analysis.get("categories"):
            categories = ", ".join(analysis["categories"])
            summary.append(f"Content categories: {categories}")
        
        # Issues and suggestions
        if analysis.get("detected_issues"):
            issues = ", ".join(analysis["detected_issues"])
            summary.append(f"Potential issues detected: {issues}")
            
        if analysis.get("suggestions"):
            suggestions = analysis["suggestions"][:3]  # Limit to top 3
            summary.append(f"AI suggestions: {'; '.join(suggestions)}")
        
        # Color information
        color_info = analysis.get("color_info", {})
        if color_info and color_info.get("dominant_colors"):
            summary.append(f"Dominant colors: {', '.join(color_info['dominant_colors'])}")
        
        return "\n".join(summary) if summary else "Basic image analysis completed"
    
    async def _call_azure_openai(self, messages: List[Dict]) -> str:
        """Call Azure OpenAI API"""
        try:
            print(f"Making Azure OpenAI request to deployment: {self.deployment_name}")
            print(f"Message count: {len(messages)}")
            
            response = await self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            result = response.choices[0].message.content.strip()
            print(f"Azure OpenAI response received successfully: {len(result)} characters")
            return result
            
        except Exception as e:
            print(f"Azure OpenAI API detailed error: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Azure OpenAI API error: {e}")
    
    async def _call_openai(self, messages: List[Dict]) -> str:
        """Call standard OpenAI API"""
        try:
            response = await self.client.chat.completions.create(
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
