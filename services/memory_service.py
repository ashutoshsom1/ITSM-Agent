import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError
import asyncio
import hashlib

class MemoryService:
    """
    Handles all memory operations including user profiles, conversation history,
    and contextual information storage using Azure Cosmos DB
    """
    
    def __init__(self):
        self.cosmos_endpoint = os.getenv("COSMOS_ENDPOINT")
        self.cosmos_key = os.getenv("COSMOS_KEY")
        self.database_name = "ai_agent_db"
        self.users_container = "users"
        self.conversations_container = "conversations"
        self.preferences_container = "preferences"
        
        if self.cosmos_endpoint and self.cosmos_key:
            self.client = CosmosClient(self.cosmos_endpoint, self.cosmos_key)
            self._initialize_database()
        else:
            # For local development, use in-memory storage
            self.local_storage = {
                "users": {},
                "conversations": {},
                "preferences": {}
            }
            self.client = None
    
    def _initialize_database(self):
        """Initialize Cosmos DB database and containers"""
        try:
            # Create database
            self.database = self.client.create_database_if_not_exists(id=self.database_name)
            
            # Create containers
            self.users_container_client = self.database.create_container_if_not_exists(
                id=self.users_container,
                partition_key=PartitionKey(path="/user_id"),
                offer_throughput=400
            )
            
            self.conversations_container_client = self.database.create_container_if_not_exists(
                id=self.conversations_container,
                partition_key=PartitionKey(path="/user_id"),
                offer_throughput=400
            )
            
            self.preferences_container_client = self.database.create_container_if_not_exists(
                id=self.preferences_container,
                partition_key=PartitionKey(path="/user_id"),
                offer_throughput=400
            )
            
        except Exception as e:
            print(f"Error initializing Cosmos DB: {e}")
            self.client = None
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Retrieve user profile"""
        if self.client:
            try:
                response = self.users_container_client.read_item(
                    item=user_id,
                    partition_key=user_id
                )
                return response
            except CosmosResourceNotFoundError:
                return None
        else:
            return self.local_storage["users"].get(user_id)
    
    async def create_user_profile(self, user_id: str, user_name: str = None) -> Dict:
        """Create new user profile"""
        profile = {
            "id": user_id,
            "user_id": user_id,
            "user_name": user_name or f"User_{user_id[:8]}",
            "created_at": datetime.now().isoformat(),
            "last_interaction": datetime.now().isoformat(),
            "interaction_count": 0,
            "preferences": {
                "communication_style": "friendly",
                "response_length": "medium",
                "technical_level": "intermediate"
            },
            "common_topics": [],
            "conversation_patterns": {},
            "sentiment_history": []
        }
        
        if self.client:
            self.users_container_client.create_item(body=profile)
        else:
            self.local_storage["users"][user_id] = profile
        
        return profile
    
    async def update_user_profile(self, user_id: str, update_data: Dict) -> Dict:
        """Update user profile"""
        profile = await self.get_user_profile(user_id)
        if not profile:
            raise ValueError("User profile not found")
        
        # Update fields
        for key, value in update_data.items():
            if key in profile:
                profile[key] = value
        
        profile["last_interaction"] = datetime.now().isoformat()
        
        if self.client:
            self.users_container_client.replace_item(
                item=user_id,
                body=profile
            )
        else:
            self.local_storage["users"][user_id] = profile
        
        return profile
    
    async def store_conversation(
        self, 
        user_id: str, 
        message: str, 
        role: str,
        conversation_id: str = None
    ) -> str:
        """Store conversation message"""
        conversation_id = conversation_id or "default"
        message_id = hashlib.md5(f"{user_id}_{conversation_id}_{datetime.now()}".encode()).hexdigest()
        
        conversation_entry = {
            "id": message_id,
            "user_id": user_id,
            "conversation_id": conversation_id,
            "message": message,
            "role": role,  # 'user' or 'assistant'
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "message_length": len(message),
                "processed": True
            }
        }
        
        if self.client:
            self.conversations_container_client.create_item(body=conversation_entry)
        else:
            if user_id not in self.local_storage["conversations"]:
                self.local_storage["conversations"][user_id] = []
            self.local_storage["conversations"][user_id].append(conversation_entry)
        
        # Update user interaction count
        await self._update_interaction_count(user_id)
        
        return message_id
    
    async def get_conversation_history(
        self, 
        user_id: str, 
        conversation_id: str = None,
        limit: int = 50
    ) -> List[Dict]:
        """Retrieve conversation history"""
        if self.client:
            query = "SELECT * FROM c WHERE c.user_id = @user_id"
            parameters = [{"name": "@user_id", "value": user_id}]
            
            if conversation_id:
                query += " AND c.conversation_id = @conversation_id"
                parameters.append({"name": "@conversation_id", "value": conversation_id})
            
            query += " ORDER BY c.timestamp DESC OFFSET 0 LIMIT @limit"
            parameters.append({"name": "@limit", "value": limit})
            
            items = list(self.conversations_container_client.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            return sorted(items, key=lambda x: x["timestamp"])
        else:
            conversations = self.local_storage["conversations"].get(user_id, [])
            if conversation_id:
                conversations = [c for c in conversations if c["conversation_id"] == conversation_id]
            
            return sorted(conversations, key=lambda x: x["timestamp"])[-limit:]
    
    async def get_user_conversations(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Get unique conversations for a user"""
        if self.client:
            query = """
            SELECT DISTINCT c.conversation_id, 
                   MAX(c.timestamp) as last_message_time,
                   COUNT(1) as message_count
            FROM c 
            WHERE c.user_id = @user_id 
            GROUP BY c.conversation_id 
            ORDER BY MAX(c.timestamp) DESC 
            OFFSET 0 LIMIT @limit
            """
            parameters = [
                {"name": "@user_id", "value": user_id},
                {"name": "@limit", "value": limit}
            ]
            
            items = list(self.conversations_container_client.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            return items
        else:
            conversations = self.local_storage["conversations"].get(user_id, [])
            conversation_groups = {}
            
            for conv in conversations:
                conv_id = conv["conversation_id"]
                if conv_id not in conversation_groups:
                    conversation_groups[conv_id] = {
                        "conversation_id": conv_id,
                        "last_message_time": conv["timestamp"],
                        "message_count": 0
                    }
                conversation_groups[conv_id]["message_count"] += 1
                if conv["timestamp"] > conversation_groups[conv_id]["last_message_time"]:
                    conversation_groups[conv_id]["last_message_time"] = conv["timestamp"]
            
            return sorted(
                list(conversation_groups.values()),
                key=lambda x: x["last_message_time"],
                reverse=True
            )[:limit]
    
    async def update_user_preferences(
        self, 
        user_id: str, 
        message: str, 
        context_analysis: Dict
    ):
        """Update user preferences based on interaction patterns"""
        profile = await self.get_user_profile(user_id)
        if not profile:
            return
        
        # Analyze message for preferences
        message_length = len(message.split())
        
        # Update communication style preference
        if any(word in message.lower() for word in ["please", "thanks", "appreciate"]):
            profile["preferences"]["communication_style"] = "polite"
        elif any(word in message.lower() for word in ["quick", "fast", "hurry"]):
            profile["preferences"]["communication_style"] = "direct"
        
        # Update technical level based on terminology used
        technical_terms = ["api", "database", "server", "code", "function", "algorithm"]
        if any(term in message.lower() for term in technical_terms):
            profile["preferences"]["technical_level"] = "advanced"
        
        # Update response length preference
        if message_length > 50:
            profile["preferences"]["response_length"] = "detailed"
        elif message_length < 10:
            profile["preferences"]["response_length"] = "brief"
        
        # Track common topics
        sentiment = context_analysis.get("sentiment", {})
        if sentiment.get("score", 0) > 0.5:  # Positive sentiment
            topics = context_analysis.get("topics", [])
            for topic in topics:
                if topic not in profile["common_topics"]:
                    profile["common_topics"].append(topic)
                    if len(profile["common_topics"]) > 10:
                        profile["common_topics"] = profile["common_topics"][-10:]
        
        # Store sentiment history
        if sentiment:
            profile["sentiment_history"].append({
                "timestamp": datetime.now().isoformat(),
                "score": sentiment.get("score", 0),
                "confidence": sentiment.get("confidence", 0)
            })
            
            # Keep only last 20 sentiment records
            profile["sentiment_history"] = profile["sentiment_history"][-20:]
        
        await self.update_user_profile(user_id, profile)
    
    async def _update_interaction_count(self, user_id: str):
        """Update user interaction count"""
        profile = await self.get_user_profile(user_id)
        if profile:
            profile["interaction_count"] = profile.get("interaction_count", 0) + 1
            profile["last_interaction"] = datetime.now().isoformat()
            await self.update_user_profile(user_id, profile)
    
    async def get_user_analytics(self, user_id: str) -> Dict:
        """Get analytics data for a user"""
        profile = await self.get_user_profile(user_id)
        conversations = await self.get_conversation_history(user_id, limit=100)
        
        if not profile or not conversations:
            return {}
        
        # Calculate metrics
        total_messages = len(conversations)
        user_messages = [c for c in conversations if c["role"] == "user"]
        assistant_messages = [c for c in conversations if c["role"] == "assistant"]
        
        avg_message_length = sum(len(c["message"]) for c in user_messages) / len(user_messages) if user_messages else 0
        
        # Recent activity
        recent_conversations = [
            c for c in conversations 
            if datetime.fromisoformat(c["timestamp"]) > datetime.now() - timedelta(days=7)
        ]
        
        return {
            "total_interactions": profile.get("interaction_count", 0),
            "total_messages": total_messages,
            "avg_message_length": round(avg_message_length, 2),
            "recent_activity": len(recent_conversations),
            "common_topics": profile.get("common_topics", []),
            "preferences": profile.get("preferences", {}),
            "sentiment_trend": profile.get("sentiment_history", [])[-5:],  # Last 5 sentiment scores
            "last_interaction": profile.get("last_interaction"),
            "account_age_days": (
                datetime.now() - datetime.fromisoformat(profile.get("created_at", datetime.now().isoformat()))
            ).days
        }
