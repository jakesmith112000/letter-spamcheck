import os
import re
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# ----------------------------------------------------------------------
# Spam Check Proxy (public)
# ----------------------------------------------------------------------
@app.route('/api/spamcheck', methods=['POST'])
def spamcheck():
    data = request.json
    html_content = data.get('html', '')
    if not html_content:
        return jsonify({'error': 'No HTML content'}), 400

    email_raw = f"""From: sender@example.com
To: recipient@example.com
Subject: Spam Check Test
MIME-Version: 1.0
Content-Type: text/html; charset="UTF-8"

{html_content}
"""
    try:
        resp = requests.post(
            'https://spamcheck.postmarkapp.com/filter',
            headers={'Content-Type': 'application/json'},
            json={'email': email_raw, 'options': 'long'},
            timeout=30
        )
        if resp.headers.get('content-type', '').startswith('application/json'):
            result = resp.json()
            return jsonify(result), resp.status_code
        else:
            return jsonify({'success': False, 'error': f'SpamCheck API returned {resp.status_code}: {resp.text[:200]}'}), resp.status_code
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ----------------------------------------------------------------------
# Health check endpoint
# ----------------------------------------------------------------------
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'spam-checker'}), 200

if __name__ == '__main__':
    print("🔍 Spam Check Server running at http://localhost:5000")
    print("   POST to /api/spamcheck with JSON: { 'html': '<html>...</html>' }")
    app.run(debug=True, port=5000)
