import re
import asyncio
from typing import Dict, Any, List, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ContentRedactor:
    def __init__(self):
        self.redaction_patterns = self._init_redaction_patterns()
    
    def _init_redaction_patterns(self) -> Dict[str, List[str]]:
        """Initialize regex patterns for redaction"""
        return {
            "government_agencies": [
                r'\b(VA|GSA|DOD|DHS|USACE|NAVY|ARMY|AIR FORCE|MARINES)\b',
                r'\b(Department of [A-Za-z\s]+)\b',
                r'\b(U\.S\. [A-Za-z\s]+ Administration)\b',
                r'\b([A-Z]{2,5} Command)\b'
            ],
            "contact_info": [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
                r'\bhttps?://[^\s]+\b',
                r'\bwww\.[^\s]+\b'
            ],
            "federal_codes": [
                r'\bDUNS\s*:?\s*\d+\b',
                r'\bUEI\s*:?\s*[A-Z0-9]+\b',
                r'\bSAM\s*:?\s*[A-Z0-9]+\b',
                r'\bCAGE\s*:?\s*[A-Z0-9]+\b',
                r'\bSolicitation\s*:?\s*[A-Z0-9\-]+\b',
                r'\bContract\s*:?\s*[A-Z0-9\-]+\b'
            ],
            "specific_locations": [
                r'\b\d+\s+[A-Za-z\s]+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Boulevard|Blvd)\b',
                r'\b[A-Za-z\s]+\s+Building\s+\d+\b',
                r'\b[A-Za-z\s]+\s+(Base|AFB|Naval|Fort)\b'
            ]
        }
    
    async def redact_content(self, content: Dict[str, Any], options: Dict[str, str] = {}) -> Tuple[Dict[str, Any], List[str]]:
        """Redact sensitive information from extracted content"""
        try:
            redacted_content = content.copy()
            redaction_summary = []
            
            for section_key, section_content in redacted_content.items():
                if isinstance(section_content, str):
                    redacted_text, section_redactions = self._redact_text(section_content)
                    redacted_content[section_key] = redacted_text
                    redaction_summary.extend([f"{section_key}: {r}" for r in section_redactions])
            
            redacted_content["redaction_applied"] = True
            redacted_content["redaction_timestamp"] = datetime.utcnow().isoformat()
            
            logger.info(f"Content redaction completed. {len(redaction_summary)} items redacted")
            return redacted_content, redaction_summary
            
        except Exception as e:
            logger.error(f"Content redaction failed: {str(e)}")
            raise Exception(f"Content redaction failed: {str(e)}")
    
    def _redact_text(self, text: str) -> Tuple[str, List[str]]:
        """Redact sensitive information from text"""
        redacted_text = text
        redactions = []
        
        for category, patterns in self.redaction_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, redacted_text, re.IGNORECASE)
                if matches:
                    redacted_text = re.sub(pattern, "[REDACTED]", redacted_text, flags=re.IGNORECASE)
                    redactions.extend([f"Removed {category}: {match}" for match in matches])
        
        return redacted_text, redactions
