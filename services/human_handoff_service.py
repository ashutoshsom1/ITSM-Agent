import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import asyncio

@dataclass
class HandoffRequest:
    """Represents a human handoff request"""
    id: str
    user_id: str
    conversation_id: str
    reason: str
    priority: str
    status: str
    created_at: datetime
    assigned_agent: Optional[str] = None
    context: Optional[Dict] = None
    estimated_wait_time: Optional[int] = None

class HumanHandoffService:
    """
    Manages human agent handoff functionality including queue management,
    agent matching, and context transfer
    """
    
    def __init__(self):
        # In production, this would connect to a real queue system
        self.active_handoffs = {}
        self.agent_pool = self._initialize_agent_pool()
        self.queue_metrics = {
            "total_requests": 0,
            "average_wait_time": 0,
            "active_handoffs": 0
        }
    
    def _initialize_agent_pool(self) -> List[Dict]:
        """Initialize available human agents"""
        return [
            {
                "id": "agent_001",
                "name": "Sarah Johnson",
                "specializations": ["technical_support", "troubleshooting"],
                "status": "available",
                "current_load": 0,
                "max_concurrent": 3,
                "rating": 4.8,
                "languages": ["en", "es"]
            },
            {
                "id": "agent_002", 
                "name": "Mike Chen",
                "specializations": ["software_issues", "development"],
                "status": "available",
                "current_load": 1,
                "max_concurrent": 4,
                "rating": 4.9,
                "languages": ["en", "zh"]
            },
            {
                "id": "agent_003",
                "name": "Emma Williams",
                "specializations": ["customer_support", "general_help"],
                "status": "available", 
                "current_load": 2,
                "max_concurrent": 5,
                "rating": 4.7,
                "languages": ["en", "fr"]
            },
            {
                "id": "agent_004",
                "name": "David Rodriguez",
                "specializations": ["escalation", "complex_issues"],
                "status": "available",
                "current_load": 0,
                "max_concurrent": 2,
                "rating": 4.9,
                "languages": ["en", "es"]
            }
        ]
    
    async def initiate_handoff(
        self,
        user_id: str,
        conversation_id: str,
        reason: str,
        context: Dict = None
    ) -> Dict[str, Any]:
        """Initiate a handoff to a human agent"""
        
        try:
            # Create handoff request
            handoff_id = str(uuid.uuid4())
            priority = self._determine_priority(reason, context)
            
            # Find best available agent
            best_agent = await self._find_best_agent(reason, context, priority)
            
            handoff_request = HandoffRequest(
                id=handoff_id,
                user_id=user_id,
                conversation_id=conversation_id,
                reason=reason,
                priority=priority,
                status="queued" if not best_agent else "assigned",
                created_at=datetime.now(),
                assigned_agent=best_agent["id"] if best_agent else None,
                context=context
            )
            
            # Calculate estimated wait time
            estimated_wait = await self._calculate_wait_time(priority, best_agent)
            handoff_request.estimated_wait_time = estimated_wait
            
            # Store handoff request
            self.active_handoffs[handoff_id] = handoff_request
            
            # Update metrics
            self.queue_metrics["total_requests"] += 1
            self.queue_metrics["active_handoffs"] += 1
            
            # Assign agent if available
            if best_agent:
                await self._assign_agent(handoff_request, best_agent)
                
                return {
                    "handoff_id": handoff_id,
                    "status": "assigned",
                    "message": f"I'm connecting you with {best_agent['name']}, who specializes in {', '.join(best_agent['specializations'])}. They'll be with you shortly!",
                    "agent_info": {
                        "name": best_agent["name"],
                        "specializations": best_agent["specializations"],
                        "rating": best_agent["rating"],
                        "estimated_response_time": "1-2 minutes"
                    },
                    "estimated_wait_time": estimated_wait,
                    "handoff_type": "immediate"
                }
            else:
                return {
                    "handoff_id": handoff_id,
                    "status": "queued",
                    "message": f"I understand you need human assistance. You're currently #{self._get_queue_position(handoff_request)} in our {priority} priority queue. Our team will be with you as soon as possible!",
                    "estimated_wait_time": estimated_wait,
                    "queue_position": self._get_queue_position(handoff_request),
                    "handoff_type": "queued",
                    "priority": priority
                }
                
        except Exception as e:
            return {
                "error": f"Failed to initiate handoff: {e}",
                "fallback_message": "I'm having trouble connecting you with a human agent right now, but I'll continue to help you as best I can. Please let me know how I can assist you further."
            }
    
    async def get_handoff_status(self, handoff_id: str) -> Dict[str, Any]:
        """Get current status of a handoff request"""
        
        if handoff_id not in self.active_handoffs:
            return {"error": "Handoff request not found"}
        
        handoff = self.active_handoffs[handoff_id]
        
        status_info = {
            "handoff_id": handoff_id,
            "status": handoff.status,
            "created_at": handoff.created_at.isoformat(),
            "priority": handoff.priority,
            "estimated_wait_time": handoff.estimated_wait_time
        }
        
        if handoff.assigned_agent:
            agent = self._get_agent_by_id(handoff.assigned_agent)
            if agent:
                status_info["agent_info"] = {
                    "name": agent["name"],
                    "specializations": agent["specializations"],
                    "status": "connected"
                }
        else:
            status_info["queue_position"] = self._get_queue_position(handoff)
        
        return status_info
    
    async def complete_handoff(self, handoff_id: str, resolution: str = None) -> Dict[str, Any]:
        """Mark a handoff as completed"""
        
        if handoff_id not in self.active_handoffs:
            return {"error": "Handoff request not found"}
        
        handoff = self.active_handoffs[handoff_id]
        handoff.status = "completed"
        
        # Free up the agent
        if handoff.assigned_agent:
            agent = self._get_agent_by_id(handoff.assigned_agent)
            if agent:
                agent["current_load"] = max(0, agent["current_load"] - 1)
        
        # Update metrics
        self.queue_metrics["active_handoffs"] = max(0, self.queue_metrics["active_handoffs"] - 1)
        
        # Calculate actual wait time for metrics
        actual_wait_time = (datetime.now() - handoff.created_at).total_seconds() / 60
        self._update_wait_time_metrics(actual_wait_time)
        
        # Remove from active handoffs (or move to completed)
        completed_handoff = self.active_handoffs.pop(handoff_id)
        
        return {
            "handoff_id": handoff_id,
            "status": "completed",
            "resolution": resolution,
            "duration_minutes": actual_wait_time,
            "message": "Thank you for using our support! Feel free to reach out again if you need any help."
        }
    
    def _determine_priority(self, reason: str, context: Dict = None) -> str:
        """Determine priority level for handoff request"""
        
        reason_lower = reason.lower()
        
        # High priority triggers
        high_priority_keywords = [
            "urgent", "emergency", "critical", "down", "outage",
            "security", "breach", "hack", "fraud", "payment"
        ]
        
        if any(keyword in reason_lower for keyword in high_priority_keywords):
            return "high"
        
        # Medium priority triggers
        medium_priority_keywords = [
            "error", "problem", "issue", "bug", "broken",
            "frustrated", "angry", "complaint"
        ]
        
        if any(keyword in reason_lower for keyword in medium_priority_keywords):
            return "medium"
        
        # Check context for priority indicators
        if context:
            sentiment_score = context.get("sentiment", {}).get("score", 0)
            if sentiment_score < -0.7:  # Very negative sentiment
                return "medium"
            
            complexity = context.get("complexity", 0)
            if complexity > 0.8:  # High complexity
                return "medium"
        
        return "normal"
    
    async def _find_best_agent(
        self, 
        reason: str, 
        context: Dict = None, 
        priority: str = "normal"
    ) -> Optional[Dict]:
        """Find the best available agent for the handoff"""
        
        available_agents = [
            agent for agent in self.agent_pool 
            if agent["status"] == "available" and agent["current_load"] < agent["max_concurrent"]
        ]
        
        if not available_agents:
            return None
        
        # Score agents based on specialization match
        scored_agents = []
        
        for agent in available_agents:
            score = 0
            
            # Specialization matching
            reason_lower = reason.lower()
            for specialization in agent["specializations"]:
                if any(keyword in reason_lower for keyword in specialization.split("_")):
                    score += 10
            
            # Load balancing (prefer agents with lower current load)
            load_factor = (agent["max_concurrent"] - agent["current_load"]) / agent["max_concurrent"]
            score += load_factor * 5
            
            # Agent rating
            score += agent["rating"]
            
            # Priority handling (some agents better for high priority)
            if priority == "high" and "escalation" in agent["specializations"]:
                score += 15
            
            scored_agents.append((agent, score))
        
        # Sort by score and return best agent
        scored_agents.sort(key=lambda x: x[1], reverse=True)
        return scored_agents[0][0] if scored_agents else None
    
    async def _assign_agent(self, handoff_request: HandoffRequest, agent: Dict):
        """Assign an agent to a handoff request"""
        
        handoff_request.assigned_agent = agent["id"]
        handoff_request.status = "assigned"
        
        # Update agent load
        agent["current_load"] += 1
        
        # In a real system, this would notify the agent
        print(f"Agent {agent['name']} assigned to handoff {handoff_request.id}")
    
    async def _calculate_wait_time(self, priority: str, assigned_agent: Dict = None) -> int:
        """Calculate estimated wait time in minutes"""
        
        if assigned_agent:
            return 2  # Immediate assignment
        
        # Base wait times by priority
        base_wait_times = {
            "high": 5,
            "medium": 15,
            "normal": 30
        }
        
        base_wait = base_wait_times.get(priority, 30)
        
        # Adjust based on queue length
        queue_length = len([h for h in self.active_handoffs.values() if h.status == "queued"])
        queue_adjustment = queue_length * 5
        
        # Adjust based on agent availability
        available_agents = len([a for a in self.agent_pool if a["current_load"] < a["max_concurrent"]])
        if available_agents == 0:
            queue_adjustment += 15
        
        return base_wait + queue_adjustment
    
    def _get_queue_position(self, handoff_request: HandoffRequest) -> int:
        """Get position in queue for a handoff request"""
        
        queued_requests = [
            h for h in self.active_handoffs.values() 
            if h.status == "queued" and h.created_at <= handoff_request.created_at
        ]
        
        # Sort by priority and creation time
        priority_order = {"high": 0, "medium": 1, "normal": 2}
        queued_requests.sort(
            key=lambda x: (priority_order.get(x.priority, 3), x.created_at)
        )
        
        try:
            return queued_requests.index(handoff_request) + 1
        except ValueError:
            return len(queued_requests) + 1
    
    def _get_agent_by_id(self, agent_id: str) -> Optional[Dict]:
        """Get agent information by ID"""
        return next((agent for agent in self.agent_pool if agent["id"] == agent_id), None)
    
    def _update_wait_time_metrics(self, actual_wait_time: float):
        """Update average wait time metrics"""
        current_avg = self.queue_metrics["average_wait_time"]
        total_requests = self.queue_metrics["total_requests"]
        
        # Calculate new average
        new_avg = ((current_avg * (total_requests - 1)) + actual_wait_time) / total_requests
        self.queue_metrics["average_wait_time"] = round(new_avg, 2)
    
    async def get_queue_metrics(self) -> Dict[str, Any]:
        """Get current queue metrics and agent status"""
        
        available_agents = len([a for a in self.agent_pool if a["current_load"] < a["max_concurrent"]])
        busy_agents = len(self.agent_pool) - available_agents
        
        return {
            "queue_metrics": self.queue_metrics,
            "agent_status": {
                "total_agents": len(self.agent_pool),
                "available_agents": available_agents,
                "busy_agents": busy_agents,
                "agents": [
                    {
                        "name": agent["name"],
                        "status": "available" if agent["current_load"] < agent["max_concurrent"] else "busy",
                        "current_load": agent["current_load"],
                        "max_concurrent": agent["max_concurrent"],
                        "specializations": agent["specializations"]
                    }
                    for agent in self.agent_pool
                ]
            },
            "current_queue": [
                {
                    "handoff_id": h.id,
                    "priority": h.priority,
                    "wait_time_minutes": (datetime.now() - h.created_at).total_seconds() / 60,
                    "status": h.status
                }
                for h in self.active_handoffs.values()
                if h.status in ["queued", "assigned"]
            ]
        }
    
    async def notify_queue_update(self, handoff_id: str) -> Dict[str, Any]:
        """Send queue position update to user"""
        
        if handoff_id not in self.active_handoffs:
            return {"error": "Handoff not found"}
        
        handoff = self.active_handoffs[handoff_id]
        
        if handoff.status != "queued":
            return {"message": "No queue update needed"}
        
        position = self._get_queue_position(handoff)
        estimated_wait = await self._calculate_wait_time(handoff.priority)
        
        return {
            "handoff_id": handoff_id,
            "queue_position": position,
            "estimated_wait_time": estimated_wait,
            "message": f"Update: You're now #{position} in the queue. Estimated wait time: {estimated_wait} minutes.",
            "priority": handoff.priority
        }
