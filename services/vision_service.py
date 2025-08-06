import os
import base64
import json
from typing import Dict, List, Any, Optional
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
from PIL import Image
import io
import time

class VisionService:
    """
    Handles image analysis using Azure Computer Vision and custom analysis
    """
    
    def __init__(self):
        self.subscription_key = os.getenv("COMPUTER_VISION_SUBSCRIPTION_KEY")
        self.endpoint = os.getenv("COMPUTER_VISION_ENDPOINT")
        
        if self.subscription_key and self.endpoint:
            self.client = ComputerVisionClient(
                self.endpoint,
                CognitiveServicesCredentials(self.subscription_key)
            )
        else:
            self.client = None
            print("Computer Vision credentials not found, using fallback analysis")
    
    async def analyze_image(self, image_data: bytes, context: str = None) -> Dict[str, Any]:
        """
        Comprehensive image analysis including Azure Computer Vision and custom analysis
        """
        try:
            # Basic image info
            image_info = self._get_image_info(image_data)
            
            analysis_result = {
                "image_info": image_info,
                "timestamp": time.time(),
                "context": context
            }
            
            if self.client:
                # Azure Computer Vision analysis
                azure_analysis = await self._azure_computer_vision_analysis(image_data)
                analysis_result.update(azure_analysis)
            else:
                # Fallback analysis
                analysis_result.update(self._fallback_analysis(image_data, context))
            
            # Custom problem detection
            problem_analysis = self._detect_common_problems(analysis_result, context)
            analysis_result["detected_issues"] = problem_analysis["issues"]
            analysis_result["suggestions"] = problem_analysis["suggestions"]
            
            # Generate actionable insights
            insights = self._generate_insights(analysis_result, context)
            analysis_result["insights"] = insights
            
            return analysis_result
            
        except Exception as e:
            print(f"Error in image analysis: {e}")
            return {
                "error": str(e),
                "suggestions": ["Try uploading the image again", "Ensure the image is clear and well-lit"],
                "fallback_analysis": self._fallback_analysis(image_data, context)
            }
    
    def _get_image_info(self, image_data: bytes) -> Dict:
        """Extract basic image information"""
        try:
            image = Image.open(io.BytesIO(image_data))
            return {
                "width": image.width,
                "height": image.height,
                "format": image.format,
                "mode": image.mode,
                "size_bytes": len(image_data)
            }
        except Exception as e:
            return {"error": f"Could not read image info: {e}"}
    
    async def _azure_computer_vision_analysis(self, image_data: bytes) -> Dict[str, Any]:
        """Perform Azure Computer Vision analysis"""
        try:
            # Convert bytes to stream
            image_stream = io.BytesIO(image_data)
            
            # Analyze image
            analysis = self.client.analyze_image_in_stream(
                image_stream,
                visual_features=[
                    "Categories", "Description", "Objects", "Tags", 
                    "ImageType", "Color", "Adult", "Brands", "Faces"
                ]
            )
            
            result = {
                "description": analysis.description.captions[0].text if analysis.description.captions else "",
                "confidence": analysis.description.captions[0].confidence if analysis.description.captions else 0,
                "categories": [cat.name for cat in analysis.categories] if analysis.categories else [],
                "tags": [{"name": tag.name, "confidence": tag.confidence} for tag in analysis.tags] if analysis.tags else [],
                "objects": [{"name": obj.object_property, "confidence": obj.confidence, "rectangle": obj.rectangle} for obj in analysis.objects] if analysis.objects else [],
                "color_info": {
                    "dominant_colors": analysis.color.dominant_colors if analysis.color else [],
                    "accent_color": analysis.color.accent_color if analysis.color else None,
                    "is_bw": analysis.color.is_bw_img if analysis.color else False
                },
                "image_type": {
                    "clip_art_type": analysis.image_type.clip_art_type if analysis.image_type else 0,
                    "line_drawing_type": analysis.image_type.line_drawing_type if analysis.image_type else 0
                }
            }
            
            # OCR Text extraction
            try:
                read_result = self.client.read_in_stream(io.BytesIO(image_data), raw=True)
                operation_id = read_result.headers["Operation-Location"].split("/")[-1]
                
                # Wait for the operation to complete
                while True:
                    read_operation_result = self.client.get_read_result(operation_id)
                    if read_operation_result.status not in ['notStarted', 'running']:
                        break
                    time.sleep(1)
                
                if read_operation_result.status == OperationStatusCodes.succeeded:
                    text_results = []
                    for text_result in read_operation_result.analyze_result.read_results:
                        for line in text_result.lines:
                            text_results.append(line.text)
                    
                    result["detected_text"] = " ".join(text_results)
                    result["text_lines"] = text_results
                
            except Exception as ocr_error:
                result["detected_text"] = ""
                result["text_error"] = str(ocr_error)
            
            return result
            
        except Exception as e:
            print(f"Azure Computer Vision error: {e}")
            return {"azure_vision_error": str(e)}
    
    def _fallback_analysis(self, image_data: bytes, context: str = None) -> Dict[str, Any]:
        """Fallback analysis when Azure services are not available"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Basic analysis
            analysis = {
                "description": "Image uploaded successfully",
                "confidence": 0.5,
                "categories": ["general"],
                "tags": [],
                "objects": [],
                "detected_text": "",
                "analysis_type": "fallback"
            }
            
            # Color analysis
            colors = image.getcolors(maxcolors=256*256*256)
            if colors:
                dominant_color = max(colors, key=lambda item: item[0])
                analysis["color_info"] = {
                    "dominant_colors": [f"Color analysis available"],
                    "is_bw": image.mode in ['L', '1']
                }
            
            # Basic content detection based on context
            if context:
                context_lower = context.lower()
                if any(word in context_lower for word in ["error", "problem", "issue"]):
                    analysis["categories"].append("troubleshooting")
                if any(word in context_lower for word in ["screenshot", "screen", "ui"]):
                    analysis["categories"].append("user_interface")
                if any(word in context_lower for word in ["code", "programming"]):
                    analysis["categories"].append("development")
            
            return analysis
            
        except Exception as e:
            return {
                "error": f"Fallback analysis failed: {e}",
                "description": "Unable to analyze image",
                "categories": ["unknown"]
            }
    
    def _detect_common_problems(self, analysis: Dict, context: str = None) -> Dict[str, List]:
        """Detect common problems based on image analysis"""
        issues = []
        suggestions = []
        
        # Check image quality
        image_info = analysis.get("image_info", {})
        if image_info.get("width", 0) < 400 or image_info.get("height", 0) < 300:
            issues.append("Low resolution image")
            suggestions.append("Try taking a higher resolution screenshot or photo")
        
        # Check for error indicators in text
        detected_text = analysis.get("detected_text", "").lower()
        error_keywords = ["error", "exception", "failed", "not found", "access denied", "timeout"]
        
        for keyword in error_keywords:
            if keyword in detected_text:
                issues.append(f"Detected '{keyword}' in image text")
                suggestions.append(f"I can help troubleshoot this {keyword} issue")
        
        # Check for UI elements that might indicate problems
        tags = analysis.get("tags", [])
        tag_names = [tag["name"] if isinstance(tag, dict) else tag for tag in tags]
        
        if any(tag in ["red", "warning", "alert"] for tag in tag_names):
            issues.append("Warning indicators detected")
            suggestions.append("Share more details about what you were trying to do when this appeared")
        
        # Context-based analysis
        if context:
            context_lower = context.lower()
            if "not working" in context_lower:
                suggestions.append("Let's troubleshoot this step by step - can you describe what you expected to happen?")
            if "slow" in context_lower:
                suggestions.append("I can help identify performance issues - what specific actions are slow?")
            if "crashed" in context_lower:
                issues.append("Application crash detected")
                suggestions.append("Check if there are any error logs or messages we can review")
        
        # Default helpful suggestions
        if not suggestions:
            suggestions.extend([
                "I can see your image clearly",
                "Feel free to describe what specific help you need",
                "I can provide step-by-step guidance if you're troubleshooting an issue"
            ])
        
        return {
            "issues": issues,
            "suggestions": suggestions
        }
    
    def _generate_insights(self, analysis: Dict, context: str = None) -> List[Dict]:
        """Generate actionable insights from image analysis"""
        insights = []
        
        # Text-based insights
        detected_text = analysis.get("detected_text", "")
        if detected_text:
            insights.append({
                "type": "text_analysis",
                "title": "Text Content Found",
                "description": f"I can see text in your image: '{detected_text[:100]}...' if longer",
                "actionable": True,
                "actions": ["Copy text", "Translate text", "Search for solutions"]
            })
        
        # Object detection insights
        objects = analysis.get("objects", [])
        if objects:
            object_names = [obj["name"] if isinstance(obj, dict) else obj for obj in objects]
            insights.append({
                "type": "object_detection",
                "title": "Elements Identified",
                "description": f"I can see: {', '.join(object_names[:5])}",
                "actionable": True,
                "actions": ["Analyze specific elements", "Get usage tips"]
            })
        
        # Problem-solving insights
        issues = analysis.get("detected_issues", [])
        if issues:
            insights.append({
                "type": "problem_solving",
                "title": "Issues Detected",
                "description": f"I identified {len(issues)} potential issues",
                "actionable": True,
                "actions": ["Start guided troubleshooting", "Get detailed analysis", "Connect with human agent"]
            })
        
        # Categories-based insights
        categories = analysis.get("categories", [])
        if "user_interface" in categories or "ui" in str(categories).lower():
            insights.append({
                "type": "ui_analysis",
                "title": "User Interface Analysis",
                "description": "I can help analyze UI/UX elements and workflows",
                "actionable": True,
                "actions": ["Analyze user flow", "Suggest improvements", "Identify usability issues"]
            })
        
        if "troubleshooting" in categories:
            insights.append({
                "type": "troubleshooting",
                "title": "Troubleshooting Mode",
                "description": "I'm ready to help solve this problem step by step",
                "actionable": True,
                "actions": ["Start diagnostic", "Check common solutions", "Create action plan"]
            })
        
        # Default insight if no specific insights generated
        if not insights:
            insights.append({
                "type": "general",
                "title": "Image Analysis Complete",
                "description": "I've analyzed your image and I'm ready to help",
                "actionable": True,
                "actions": ["Ask specific questions", "Get detailed analysis", "Share more context"]
            })
        
        return insights
    
    async def extract_text_from_image(self, image_data: bytes) -> str:
        """Extract text from image using OCR"""
        if not self.client:
            return "OCR service not available"
        
        try:
            image_stream = io.BytesIO(image_data)
            read_result = self.client.read_in_stream(image_stream, raw=True)
            operation_id = read_result.headers["Operation-Location"].split("/")[-1]
            
            # Wait for the operation to complete
            while True:
                read_operation_result = self.client.get_read_result(operation_id)
                if read_operation_result.status not in ['notStarted', 'running']:
                    break
                time.sleep(1)
            
            if read_operation_result.status == OperationStatusCodes.succeeded:
                text_results = []
                for text_result in read_operation_result.analyze_result.read_results:
                    for line in text_result.lines:
                        text_results.append(line.text)
                
                return " ".join(text_results)
            
            return "No text detected"
            
        except Exception as e:
            return f"Error extracting text: {e}"
    
    def validate_image(self, image_data: bytes) -> Dict[str, Any]:
        """Validate image before processing"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            validation = {
                "valid": True,
                "issues": [],
                "recommendations": []
            }
            
            # Size validation
            if len(image_data) > 10 * 1024 * 1024:  # 10MB
                validation["issues"].append("Image file is very large")
                validation["recommendations"].append("Consider compressing the image")
            
            # Resolution validation
            if image.width < 100 or image.height < 100:
                validation["issues"].append("Image resolution is very low")
                validation["recommendations"].append("Use a higher resolution image for better analysis")
            
            # Format validation
            if image.format not in ['JPEG', 'PNG', 'BMP', 'TIFF']:
                validation["issues"].append(f"Unusual image format: {image.format}")
                validation["recommendations"].append("Consider using JPEG or PNG format")
            
            if validation["issues"]:
                validation["valid"] = False
            
            return validation
            
        except Exception as e:
            return {
                "valid": False,
                "issues": [f"Cannot read image: {e}"],
                "recommendations": ["Ensure the file is a valid image format"]
            }
