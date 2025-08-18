# How to Create Visual Analysis Topic in Microsoft Copilot Studio

## Step-by-Step Implementation Guide

### Prerequisites
- Custom connector created and working
- Access to Microsoft Copilot Studio
- Your ITSM AI Assistant bot created

---

## Step 1: Create the Visual Analysis Topic

1. **Open your bot in Copilot Studio**
2. Go to **Topics** tab
3. Click **+ New topic**
4. Choose **From blank**

### Basic Topic Setup
```
Topic Name: Screenshot Analysis
Display Name: Visual Troubleshooting
Description: Analyze screenshots and images for IT support
```

---

## Step 2: Configure Trigger Phrases

In the **Trigger** section, add these phrases:

```
Trigger phrases:
- screenshot
- image
- show you
- visual problem
- screen capture
- upload image
- share screenshot
- picture of error
- I have an image
- can you see this
```

---

## Step 3: Build the Conversation Flow

### Node 1: Welcome Message
**Action Type**: Message
```
Message: I can analyze screenshots and images to help troubleshoot your issue. Please upload a screenshot or image of the problem you're experiencing.
```

### Node 2: Request File Upload
**Action Type**: Ask with attachment
```
Configuration:
- Question: "Please upload your screenshot or image"
- Variable name: UserImage
- File types allowed: Images only
- Max file size: 10MB
- Required: Yes

Settings:
✅ Images (.jpg, .jpeg, .png, .gif, .bmp)
❌ Documents
❌ Other file types
```

### Node 3: Get User Information
**Action Type**: Set variable
```
Variable assignments:
- UserID = System.User.Id
- ConversationID = System.Conversation.Id
- UserName = System.User.DisplayName
```

### Node 4: Call AnalyzeImage API
**Action Type**: Call an action (Custom Connector)

```
Connector: ITSM-AI-Assistant
Action: AnalyzeImage

Input Parameters:
- file: UserImage (the uploaded file object)
- user_id: UserID (optional - can be null)
- conversation_id: ConversationID (optional - can be null)
- context: "User shared screenshot for IT support"

Output Variables:
- Save response as: ImageAnalysisResult

Expected Response Structure:
{
  "analysis": { ... },           // Raw analysis data
  "ai_response": "string",       // AI-generated response text
  "suggestions": ["string"],     // Array of suggestion strings
  "detected_issues": ["string"] // Array of detected issue strings
}
```

### Node 5: Check for Errors
**Action Type**: Condition
```
Condition: ImageAnalysisResult.succeeded = true

If True: Continue to analysis results
If False: Go to error handling
```

### Node 6: Display Analysis Results
**Action Type**: Message with adaptive card
```
Message Text: Here's what I found in your image:

Adaptive Card Configuration:
{
  "type": "AdaptiveCard",
  "version": "1.4",
  "body": [
    {
      "type": "TextBlock",
      "text": "🔍 **Image Analysis Results**",
      "size": "Large",
      "weight": "Bolder"
    },
    {
      "type": "TextBlock", 
      "text": "${ImageAnalysisResult.ai_response}",
      "wrap": true,
      "spacing": "Medium"
    },
    {
      "type": "TextBlock",
      "text": "**Detected Issues:**",
      "weight": "Bolder",
      "spacing": "Medium"
    },
    {
      "type": "Container",
      "items": [
        {
          "type": "TextBlock",
          "text": "${join(ImageAnalysisResult.detected_issues, '\n• ')}",
          "wrap": true
        }
      ]
    },
    {
      "type": "TextBlock",
      "text": "**Suggested Solutions:**",
      "weight": "Bolder",
      "spacing": "Medium"
    },
    {
      "type": "Container",
      "items": [
        {
          "type": "TextBlock",
          "text": "${join(ImageAnalysisResult.suggestions, '\n• ')}",
          "wrap": true
        }
      ]
    }
  ],
  "actions": [
    {
      "type": "Action.Submit",
      "title": "✅ Try These Solutions",
      "data": {
        "action": "try_solutions"
      }
    },
    {
      "type": "Action.Submit", 
      "title": "🤝 Need Human Assistance",
      "data": {
        "action": "human_help"
      }
    },
    {
      "type": "Action.Submit",
      "title": "📷 Upload Another Image", 
      "data": {
        "action": "upload_another"
      }
    }
  ]
}

Alternative Simple Message Format:
If adaptive cards are complex, use this simpler format:

Message: 
"🔍 **Analysis Complete!**

${ImageAnalysisResult.ai_response}

**Issues Found:**
${foreach(ImageAnalysisResult.detected_issues, item, '• ' + item)}

**Recommendations:**
${foreach(ImageAnalysisResult.suggestions, item, '• ' + item)}"

Quick Replies:
- "Try solutions"
- "Need human help" 
- "Upload another image"
```

### Node 7: Handle User Actions
**Action Type**: Condition on submitted data
```
Check: System.Activity.Value.action

Cases:
1. "try_solutions" → Go to Solutions Node
2. "human_help" → Go to Human Handoff Topic  
3. "upload_another" → Go back to Node 2
```

### Node 8: Show Solutions
**Action Type**: Message with suggestions
```
Message: Based on the analysis, here are the recommended solutions:

Dynamic Content: ${ImageAnalysisResult.suggestions}

Quick Replies:
- "Solution worked!"
- "Need more help"
- "Try different approach"
- "Talk to human agent"
```

---

## Step 4: Error Handling Flow

### Error Node 1: API Call Failed
**Action Type**: Message
```
Message: I'm having trouble analyzing your image right now. This could be due to:

• Image format not supported
• File size too large
• Temporary service issue

Would you like to:
- Try uploading a different image
- Describe the issue in text instead  
- Connect with a human agent
```

### Error Node 2: Invalid File Type
**Action Type**: Message
```
Message: Please upload an image file (JPG, PNG, GIF, or BMP). Other file types cannot be analyzed.

Quick Replies:
- "Upload image"
- "Describe issue instead"
```

---

## Step 5: Advanced Configurations

### Add Context Variables
In your topic, create these variables to maintain context:

```
Topic Variables:
- AnalysisCount (Number) - Track how many images analyzed
- IssueCategory (Text) - Store detected issue type  
- PreviousAnalysis (Object) - Store previous results
- UserPreferences (Object) - User's preferred solution types
```

### Enhanced Flow Logic
```yaml
Advanced Logic:
1. If AnalysisCount > 1:
   - Compare with previous analysis
   - Show pattern recognition
   - Suggest root cause analysis

2. If IssueCategory = "Hardware":
   - Route to hardware specialist
   - Provide hardware-specific solutions
   
3. If IssueCategory = "Software": 
   - Check for software updates
   - Provide software troubleshooting
```

---

## Step 6: Testing the Topic

### Test Scenarios

1. **Valid Image Upload**
   - Upload a screenshot with visible error
   - Verify API call succeeds
   - Check analysis results display correctly

2. **Invalid File Type**
   - Try uploading a PDF or Word document
   - Verify error message appears
   - Check user can retry with correct file

3. **Large File**
   - Upload image larger than 10MB
   - Verify size limit error
   - Test retry functionality

4. **API Failure**
   - Simulate API unavailability
   - Verify graceful error handling
   - Check fallback options work

### Test Data
```
Good test images:
- Screenshot with Windows error dialog
- Image of network connectivity issue
- Photo of hardware problem
- Screenshot of software interface

Bad test files:
- PDF document
- Large video file
- Corrupted image file
- Empty file
```

---

## Step 7: Integration with Other Topics

### Link to Human Handoff
```yaml
When user clicks "Need Human Assistance":
1. Transfer context variables
2. Include image analysis results
3. Set priority based on detected issues
4. Route to Human Handoff topic
```

### Link to Solution Topics
```yaml
When specific issues detected:
1. Hardware issues → Hardware Support topic
2. Software issues → Software Support topic  
3. Network issues → Network Troubleshooting topic
4. Security issues → Security Response topic
```

---

## Step 8: Analytics and Improvement

### Track Performance
```yaml
Analytics to Monitor:
- Image upload success rate
- Analysis accuracy feedback
- Solution effectiveness  
- Escalation rate from visual analysis
- Most common detected issues
```

### Continuous Improvement
```yaml
Optimization Areas:
- Refine trigger phrases based on usage
- Improve error messages based on feedback
- Add more file format support
- Enhance analysis result presentation
- Update solution suggestions based on success rates
```

---

## Sample Copilot Studio Node Configuration

### Complete Node Setup Example:

```yaml
Node: "Process Image Analysis"
Type: "Call an action"

Connector: "ITSM-AI-Assistant"
Operation: "AnalyzeImage"

Inputs:
  file: Topic.UserImage.file
  user_id: System.User.Id  
  conversation_id: System.Conversation.Id
  context: "User shared screenshot for IT support"

Outputs:
  analysis_result: Topic.ImageAnalysisResult
  ai_response: Topic.AIResponse
  detected_issues: Topic.DetectedIssues
  suggestions: Topic.SolutionSuggestions

Error Handling:
  On Success: Continue to "Display Results"
  On Failure: Go to "Error Message"
  Timeout: 30 seconds
```

---

## Pro Tips for Implementation

### 1. File Handling Best Practices
- Set reasonable file size limits (10MB max)
- Support common image formats only
- Provide clear error messages for unsupported files
- Show upload progress for large files

### 2. User Experience
- Use loading messages during API calls
- Provide preview of uploaded image
- Allow users to replace uploaded images
- Show analysis confidence levels

### 3. Performance Optimization  
- Cache analysis results
- Implement retry logic for failed API calls
- Use progressive disclosure for detailed results
- Optimize image display for mobile devices

This implementation gives you a fully functional visual analysis topic that integrates seamlessly with your FastAPI backend! 🚀

The key is using the **"Ask with attachment"** action type and properly configuring the custom connector call with the uploaded file.
