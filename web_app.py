"""
Web interface for the Tool Calling System.
"""

import os
from flask import Flask, request, jsonify, render_template_string
from toolCalling import ChatManager
from config import DEFAULT_MODEL

app = Flask(__name__)
chat_manager = ChatManager(DEFAULT_MODEL)

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tool Calling System</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .container {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 20px;
            margin-top: 20px;
        }
        .input-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input[type="text"] {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
        .response {
            margin-top: 20px;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 4px;
            min-height: 100px;
        }
        .tools-list {
            margin-top: 30px;
        }
        .tool {
            margin-bottom: 10px;
            padding: 10px;
            background-color: #f0f0f0;
            border-radius: 4px;
        }
        .tool-name {
            font-weight: bold;
        }
    </style>
</head>
<body>
    <h1>Tool Calling System</h1>
    
    <div class="container">
        <div class="input-group">
            <label for="prompt">Enter your prompt:</label>
            <input type="text" id="prompt" placeholder="e.g., What is 25 * 16?" autofocus>
        </div>
        <button id="submit-btn">Submit</button>
        
        <div class="response" id="response">
            <p>Response will appear here...</p>
        </div>
    </div>
    
    <div class="tools-list">
        <h2>Available Tools</h2>
        {% for tool_name, tool in tools.items() %}
        <div class="tool">
            <div class="tool-name">{{ tool_name }}</div>
            <div class="tool-desc">{{ tool.description }}</div>
        </div>
        {% endfor %}
    </div>
    
    <script>
        document.getElementById('submit-btn').addEventListener('click', async () => {
            const prompt = document.getElementById('prompt').value;
            if (!prompt) return;
            
            document.getElementById('response').innerHTML = '<p>Processing...</p>';
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ prompt }),
                });
                
                const data = await response.json();
                document.getElementById('response').innerHTML = `<p>${data.response}</p>`;
            } catch (error) {
                document.getElementById('response').innerHTML = `<p>Error: ${error.message}</p>`;
            }
        });
        
        // Allow pressing Enter to submit
        document.getElementById('prompt').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                document.getElementById('submit-btn').click();
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Render the main page."""
    return render_template_string(
        HTML_TEMPLATE, 
        tools=chat_manager.tools.tools
    )

@app.route('/api/chat', methods=['POST'])
def chat():
    """API endpoint for chat interactions."""
    data = request.json
    prompt = data.get('prompt', '')
    
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    
    try:
        response = chat_manager.chat(prompt)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 12000))
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=True)