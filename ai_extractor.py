import openai
import asyncio
import json
import re
import os
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AIExtractor:
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    def health_check(self) -> bool:
        """Check if AI service is available"""
        try:
            return bool(os.getenv("OPENAI_API_KEY"))
        except:
            return False
    
    async def extract_rfq_content(self, document_content: str, options: Dict[str, Any] = {}) -> Dict[str, Any]:
        """Extract structured content from RFQ document using AI"""
        try:
            prompt = self._build_extraction_prompt(document_content, options)
            
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing government RFQ documents and extracting key information."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            extracted_text = response.choices[0].message.content
            extracted_content = self._parse_extraction_response(extracted_text)
            
            logger.info("AI extraction completed successfully")
            return extracted_content
            
        except Exception as e:
            logger.error(f"AI extraction failed: {str(e)}")
            raise Exception(f"AI extraction failed: {str(e)}")
    
    def _build_extraction_prompt(self, content: str, options: Dict[str, Any]) -> str:
        """Build the prompt for AI extraction"""
        return f"""
Analyze this government RFQ document and extract the following information in JSON format:

DOCUMENT CONTENT:
{content}

Please extract and structure the following sections:

1. PROJECT_OVERVIEW: Main description and purpose
2. SCOPE_OF_WORK: Detailed work requirements  
3. DELIVERABLES: Expected outputs and products
4. TIMELINE: Important dates, deadlines, and duration
5. LOCATION: Where work will be performed (extract only general region/state)
6. SUBMISSION_REQUIREMENTS: How vendors should respond
7. TECHNICAL_REQUIREMENTS: Specifications and standards
8. QUALIFICATIONS: Required vendor capabilities
9. EVALUATION_CRITERIA: How proposals will be judged

IMPORTANT RULES:
- Ignore cover pages, legal boilerplate, and federal acquisition regulations
- Focus on actionable business requirements
- Extract actual requirements, not procedural language
- If a section is not clearly present, mark it as "Not specified"
- Provide clean, business-focused content suitable for vendor consumption

Return the response in this JSON format:
{{
    "project_overview": "...",
    "scope_of_work": "...",
    "deliverables": "...",
    "timeline": "...",
    "location": "...",
    "submission_requirements": "...",
    "technical_requirements": "...",
    "qualifications": "...",
    "evaluation_criteria": "...",
    "extracted_sections": ["list of sections found"],
    "confidence_score": 0.95
}}
"""
    
    def _parse_extraction_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI response into structured data"""
        try:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                return self._manual_parse_response(response_text)
                
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON response, using fallback")
            return self._manual_parse_response(response_text)
    
    def _manual_parse_response(self, response_text: str) -> Dict[str, Any]:
        """Fallback manual parsing"""
        return {
            "project_overview": "AI extraction completed but formatting failed",
            "scope_of_work": response_text[:500] + "...",
            "deliverables": "Not specified",
            "timeline": "Not specified", 
            "location": "Not specified",
            "submission_requirements": "Not specified",
            "technical_requirements": "Not specified",
            "qualifications": "Not specified",
            "evaluation_criteria": "Not specified",
            "extracted_sections": ["raw_content"],
            "confidence_score": 0.5
        }
