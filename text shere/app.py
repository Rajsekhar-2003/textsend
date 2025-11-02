import os
import secrets
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string, redirect, url_for
import sqlite3
import hashlib

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SecureText Share - Share Text Securely</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/crypto-js.min.js"></script>
    <style>
        :root {
            --primary: #4361ee;
            --secondary: #3a0ca3;
            --success: #4cc9f0;
            --danger: #f72585;
            --warning: #f8961e;
            --light: #f8f9fa;
            --dark: #212529;
            --gray: #6c757d;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: var(--primary);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        
        .header p {
            opacity: 0.9;
            font-size: 1.1rem;
        }
        
        .content {
            padding: 30px;
        }
        
        .tabs {
            display: flex;
            margin-bottom: 20px;
            background: var(--light);
            border-radius: 10px;
            padding: 5px;
        }
        
        .tab {
            flex: 1;
            padding: 15px;
            text-align: center;
            cursor: pointer;
            border-radius: 8px;
            transition: all 0.3s ease;
            font-weight: 600;
        }
        
        .tab.active {
            background: var(--primary);
            color: white;
        }
        
        .panel {
            display: none;
        }
        
        .panel.active {
            display: block;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: var(--dark);
        }
        
        textarea, input, select {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }
        
        textarea {
            min-height: 200px;
            resize: vertical;
            font-family: monospace;
        }
        
        textarea:focus, input:focus, select:focus {
            outline: none;
            border-color: var(--primary);
        }
        
        .options-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .option-group {
            background: var(--light);
            padding: 15px;
            border-radius: 8px;
        }
        
        .btn {
            background: var(--primary);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: all 0.3s ease;
            width: 100%;
        }
        
        .btn:hover {
            background: var(--secondary);
            transform: translateY(-2px);
        }
        
        .btn-secondary {
            background: var(--gray);
        }
        
        .btn-success {
            background: var(--success);
        }
        
        .btn-danger {
            background: var(--danger);
        }
        
        .result {
            margin-top: 20px;
            padding: 20px;
            background: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 8px;
            display: none;
        }
        
        .result.error {
            background: #f8d7da;
            border-color: #f5c6cb;
        }
        
        .url-display {
            background: white;
            padding: 15px;
            border-radius: 8px;
            border: 2px dashed #dee2e6;
            margin: 10px 0;
            word-break: break-all;
        }
        
        .copy-btn {
            background: var(--success);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            margin-top: 10px;
        }
        
        .text-display {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid var(--primary);
            margin: 20px 0;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        
        .stats {
            display: flex;
            justify-content: space-between;
            margin-top: 20px;
            padding: 15px;
            background: var(--light);
            border-radius: 8px;
            font-size: 14px;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-value {
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--primary);
        }
        
        .password-prompt {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        
        @media (max-width: 768px) {
            .container {
                margin: 10px;
            }
            
            .header {
                padding: 20px;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .content {
                padding: 20px;
            }
            
            .options-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 SecureText Share</h1>
            <p>Share text securely with expiration and password protection</p>
        </div>
        
        <div class="content">
            <div class="tabs">
                <div class="tab active" onclick="switchTab('create')">Create Share</div>
                <div class="tab" onclick="switchTab('view')">View Text</div>
            </div>
            
            <!-- Create Panel -->
            <div id="create-panel" class="panel active">
                <div class="form-group">
                    <label for="content">Your Text Content:</label>
                    <textarea id="content" placeholder="Enter the text you want to share securely..."></textarea>
                </div>
                
                <div class="options-grid">
                    <div class="option-group">
                        <label for="password">Password (optional):</label>
                        <input type="password" id="password" placeholder="Set access password">
                    </div>
                    
                    <div class="option-group">
                        <label for="expiration">Expiration:</label>
                        <select id="expiration">
                            <option value="never">Never</option>
                            <option value="1h">1 Hour</option>
                            <option value="24h">24 Hours</option>
                            <option value="7d">7 Days</option>
                            <option value="30d">30 Days</option>
                        </select>
                    </div>
                    
                    <div class="option-group">
                        <label for="max-views">Max Views (0 = unlimited):</label>
                        <input type="number" id="max-views" min="0" value="0">
                    </div>
                </div>
                
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="encrypt"> 
                        Enable client-side encryption (experimental)
                    </label>
                </div>
                
                <button class="btn" onclick="createShare()">Create Secure Share</button>
                
                <div id="create-result" class="result"></div>
            </div>
            
            <!-- View Panel -->
            <div id="view-panel" class="panel">
                <div class="form-group">
                    <label for="share-url">Share URL:</label>
                    <input type="text" id="share-url" placeholder="Paste the share URL here">
                </div>
                
                <div id="password-prompt" class="password-prompt" style="display: none;">
                    <label for="view-password">Password Required:</label>
                    <input type="password" id="view-password" placeholder="Enter password">
                    <button class="btn btn-success" onclick="verifyPassword()" style="margin-top: 10px;">Access Text</button>
                </div>
                
                <button class="btn" onclick="loadText()">Load Text</button>
                
                <div id="text-display" style="display: none;">
                    <div class="text-display" id="content-display"></div>
                    <div class="stats" id="stats-display"></div>
                    <button class="btn btn-secondary" onclick="copyText()">Copy Text</button>
                </div>
                
                <div id="view-result" class="result"></div>
            </div>
        </div>
    </div>

    <script>
        let currentTextId = null;
        
        function switchTab(tabName) {
            // Hide all panels
            document.querySelectorAll('.panel').forEach(panel => {
                panel.classList.remove('active');
            });
            
            // Remove active class from all tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected panel and activate tab
            document.getElementById(tabName + '-panel').classList.add('active');
            event.target.classList.add('active');
        }
        
        function showResult(elementId, message, isError = false) {
            const result = document.getElementById(elementId);
            result.textContent = message;
            result.className = isError ? 'result error' : 'result';
            result.style.display = 'block';
        }
        
        function hideResult(elementId) {
            document.getElementById(elementId).style.display = 'none';
        }
        
        async function createShare() {
            const content = document.getElementById('content').value.trim();
            const password = document.getElementById('password').value;
            const expiration = document.getElementById('expiration').value;
            const maxViews = parseInt(document.getElementById('max-views').value) || 0;
            const encrypt = document.getElementById('encrypt').checked;
            
            if (!content) {
                showResult('create-result', 'Please enter some text content.', true);
                return;
            }
            
            try {
                const response = await fetch('/api/create', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        content: content,
                        password: password,
                        expiration: expiration,
                        max_views: maxViews,
                        encrypt: encrypt
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    const fullUrl = window.location.origin + data.url;
                    const resultHtml = `
                        <h3>✅ Text shared successfully!</h3>
                        <p>Share this URL:</p>
                        <div class="url-display">${fullUrl}</div>
                        <button class="copy-btn" onclick="copyToClipboard('${fullUrl}')">Copy URL</button>
                        <p style="margin-top: 10px; font-size: 14px; color: #666;">
                            📊 Max views: ${maxViews || 'Unlimited'} | 
                            ⏰ Expires: ${expiration === 'never' ? 'Never' : expiration}
                        </p>
                    `;
                    document.getElementById('create-result').innerHTML = resultHtml;
                    document.getElementById('create-result').style.display = 'block';
                    
                    // Clear form
                    document.getElementById('content').value = '';
                    document.getElementById('password').value = '';
                } else {
                    showResult('create-result', 'Error: ' + data.error, true);
                }
            } catch (error) {
                showResult('create-result', 'Network error: ' + error.message, true);
            }
        }
        
        async function loadText() {
            const url = document.getElementById('share-url').value.trim();
            const urlParts = url.split('/');
            const textId = urlParts[urlParts.length - 1];
            
            if (!textId) {
                showResult('view-result', 'Please enter a valid share URL.', true);
                return;
            }
            
            try {
                const response = await fetch('/api/text/' + textId);
                const data = await response.json();
                
                if (response.ok) {
                    currentTextId = textId;
                    
                    if (data.has_password) {
                        document.getElementById('password-prompt').style.display = 'block';
                        document.getElementById('text-display').style.display = 'none';
                        hideResult('view-result');
                    } else {
                        await displayText(data);
                    }
                } else {
                    showResult('view-result', 'Error: ' + data.error, true);
                }
            } catch (error) {
                showResult('view-result', 'Network error: ' + error.message, true);
            }
        }
        
        async function verifyPassword() {
            const password = document.getElementById('view-password').value;
            
            if (!password) {
                showResult('view-result', 'Please enter the password.', true);
                return;
            }
            
            try {
                const response = await fetch('/api/verify', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        id: currentTextId,
                        password: password
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    document.getElementById('password-prompt').style.display = 'none';
                    // Reload text data now that password is verified
                    const textResponse = await fetch('/api/text/' + currentTextId);
                    const textData = await textResponse.json();
                    await displayText(textData);
                } else {
                    showResult('view-result', 'Error: ' + data.error, true);
                }
            } catch (error) {
                showResult('view-result', 'Network error: ' + error.message, true);
            }
        }
        
        async function displayText(data) {
            document.getElementById('content-display').textContent = data.content;
            
            const statsHtml = `
                <div class="stat-item">
                    <div class="stat-value">${data.view_count + 1}</div>
                    <div>Views</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${data.max_views || '∞'}</div>
                    <div>Max Views</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${new Date(data.created_at).toLocaleDateString()}</div>
                    <div>Created</div>
                </div>
            `;
            document.getElementById('stats-display').innerHTML = statsHtml;
            document.getElementById('text-display').style.display = 'block';
            hideResult('view-result');
            
            // Increment view count
            await fetch('/api/view', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    id: currentTextId
                })
            });
        }
        
        function copyText() {
            const text = document.getElementById('content-display').textContent;
            copyToClipboard(text);
            alert('Text copied to clipboard!');
        }
        
        function copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(() => {
                // Optional: Show copied notification
            });
        }
        
        // Handle URL parameters for direct viewing
        window.addEventListener('load', function() {
            const path = window.location.pathname;
            if (path.startsWith('/view/')) {
                const textId = path.split('/view/')[1];
                if (textId) {
                    switchTab('view');
                    document.getElementById('share-url').value = window.location.href;
                    setTimeout(() => loadText(), 500);
                }
            }
        });
    </script>
</body>
</html>
'''

# Database setup
def init_db():
    conn = sqlite3.connect('text_share.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS texts (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            password_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            view_count INTEGER DEFAULT 0,
            max_views INTEGER DEFAULT 0,
            is_encrypted BOOLEAN DEFAULT FALSE
        )
    ''')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('text_share.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

def generate_id():
    return secrets.token_urlsafe(8)

def hash_password(password):
    if not password:
        return None
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/api/create', methods=['POST'])
def create_text():
    try:
        data = request.get_json()
        content = data.get('content', '').strip()
        password = data.get('password', '')
        expiration = data.get('expiration', 'never')
        max_views = data.get('max_views', 0)
        encrypt = data.get('encrypt', False)

        if not content:
            return jsonify({'error': 'Content cannot be empty'}), 400

        # Generate unique ID
        text_id = generate_id()
        
        # Calculate expiration
        expires_at = None
        if expiration != 'never':
            if expiration == '1h':
                expires_at = datetime.utcnow() + timedelta(hours=1)
            elif expiration == '24h':
                expires_at = datetime.utcnow() + timedelta(hours=24)
            elif expiration == '7d':
                expires_at = datetime.utcnow() + timedelta(days=7)
            elif expiration == '30d':
                expires_at = datetime.utcnow() + timedelta(days=30)

        # Store in database
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO texts (id, content, password_hash, expires_at, max_views, is_encrypted)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (text_id, content, hash_password(password), expires_at, max_views, encrypt))
        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'id': text_id,
            'url': f"/view/{text_id}"
        })

    except Exception as e:
        return jsonify({'error': 'Failed to create text share'}), 500

@app.route('/api/text/<text_id>')
def get_text(text_id):
    try:
        conn = get_db_connection()
        text = conn.execute(
            'SELECT * FROM texts WHERE id = ?', (text_id,)
        ).fetchone()
        conn.close()

        if not text:
            return jsonify({'error': 'Text not found'}), 404

        # Check expiration
        if text['expires_at'] and datetime.utcnow() > datetime.fromisoformat(text['expires_at']):
            return jsonify({'error': 'This text has expired'}), 410

        # Check view limit
        if text['max_views'] > 0 and text['view_count'] >= text['max_views']:
            return jsonify({'error': 'Maximum views reached for this text'}), 410

        return jsonify({
            'content': text['content'],
            'has_password': bool(text['password_hash']),
            'view_count': text['view_count'],
            'max_views': text['max_views'],
            'created_at': text['created_at'],
            'is_encrypted': bool(text['is_encrypted'])
        })

    except Exception as e:
        return jsonify({'error': 'Failed to retrieve text'}), 500

@app.route('/api/verify', methods=['POST'])
def verify_password():
    try:
        data = request.get_json()
        text_id = data.get('id')
        password = data.get('password')

        conn = get_db_connection()
        text = conn.execute(
            'SELECT password_hash FROM texts WHERE id = ?', (text_id,)
        ).fetchone()
        conn.close()

        if not text:
            return jsonify({'error': 'Text not found'}), 404

        if not text['password_hash']:
            return jsonify({'success': True})

        if hash_password(password) == text['password_hash']:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Invalid password'}), 401

    except Exception as e:
        return jsonify({'error': 'Verification failed'}), 500

@app.route('/api/view', methods=['POST'])
def increment_view():
    try:
        data = request.get_json()
        text_id = data.get('id')

        conn = get_db_connection()
        conn.execute(
            'UPDATE texts SET view_count = view_count + 1 WHERE id = ?', (text_id,)
        )
        conn.commit()
        conn.close()

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': 'Failed to update view count'}), 500

@app.route('/view/<text_id>')
def view_text(text_id):
    return render_template_string(HTML_TEMPLATE)

# Cleanup expired texts
def cleanup_expired():
    try:
        conn = get_db_connection()
        conn.execute(
            'DELETE FROM texts WHERE expires_at < ?', (datetime.utcnow(),)
        )
        conn.commit()
        conn.close()
    except:
        pass

# Initialize database
init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)