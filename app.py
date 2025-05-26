from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import os
import logging
from datetime import datetime

from services.ai_extractor import AIExtractor
from services.redactor import ContentRedactor
from services.rfq_generator import RFQGenerator

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ai_extractor = AIExtractor()
redactor = ContentRedactor()
rfq_generator = RFQGenerator()

@app.route('/')
def home():
    return "<h1>🚀 RFQ Rocket Backend</h1><p>Server is running!</p>"

@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        api_key_ok = ai_extractor.health_check()
        return jsonify({
            'status': 'healthy' if api_key_ok else 'error',
            'services': {'ai_extractor': 'ready' if api_key_ok else 'no_api_key'}
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/process-rfq', methods=['POST'])
def process_rfq():
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({'success': False, 'error': 'No content'}), 400
        
        result = asyncio.run(process_document(data['content'], data.get('company_info', {})))
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

async def process_document(content: str, company_info: dict):
    extracted = await ai_extractor.extract_rfq_content(content)
    redacted, summary = await redactor.redact_content(extracted)
    final_rfq = await rfq_generator.generate_rfq(redacted, company_info)
    
    return {
        'success': True,
        'extracted_content': extracted,
        'redacted_content': redacted,
        'redaction_summary': summary,
        'final_rfq': final_rfq,
        'confidence_score': extracted.get('confidence_score', 0.0)
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
