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
        h1, h2, h3 {
            color: #333;
        }
        h1 {
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
            min-height: 50px;
        }
        .tools-used {
            margin-top: 20px;
            padding: 15px;
            background-color: #f0f8ff;
            border-radius: 4px;
            display: none;
        }
        .tool-usage {
            margin-bottom: 15px;
            padding: 10px;
            background-color: #e6f2ff;
            border-radius: 4px;
            border-left: 4px solid #0066cc;
        }
        .tool-usage h3 {
            margin-top: 0;
            color: #0066cc;
        }
        .tool-args, .tool-result {
            margin-top: 5px;
            font-family: monospace;
            background-color: #f5f5f5;
            padding: 8px;
            border-radius: 3px;
            overflow-x: auto;
        }
        .available-tools {
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
        .collapsible {
            cursor: pointer;
            padding: 10px;
            width: 100%;
            border: none;
            text-align: left;
            outline: none;
            background-color: #f1f1f1;
            margin-top: 20px;
            font-weight: bold;
            border-radius: 4px;
        }
        .active, .collapsible:hover {
            background-color: #e0e0e0;
        }
        .content {
            padding: 0 18px;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.2s ease-out;
            background-color: #f9f9f9;
            border-radius: 0 0 4px 4px;
        }
    </style>
</head>
<body>
    <h1>Tool Calling System</h1>
    
    <div class="container">
        <div class="input-group">
            <label for="prompt">Enter your prompt:</label>
            <input type="text" id="prompt" placeholder="e.g., What is 25 * 16? or What date will it be 45 days from today?" autofocus>
        </div>
        <button id="submit-btn">Submit</button>
        
        <div class="response" id="response">
            <p>Response will appear here...</p>
        </div>
        
        <div class="tools-used" id="tools-used">
            <h2>Tools Used</h2>
            <div id="tool-usage-container"></div>
        </div>
    </div>
    
    <button class="collapsible">Available Tools</button>
    <div class="content">
        <div class="available-tools">
            {% for tool_name, tool in tools.items() %}
            <div class="tool">
                <div class="tool-name">{{ tool_name }}</div>
                <div class="tool-desc">{{ tool.description }}</div>
            </div>
            {% endfor %}
        </div>
    </div>
    
    <script>
        // Handle collapsible sections
        const coll = document.getElementsByClassName("collapsible");
        for (let i = 0; i < coll.length; i++) {
            coll[i].addEventListener("click", function() {
                this.classList.toggle("active");
                const content = this.nextElementSibling;
                if (content.style.maxHeight) {
                    content.style.maxHeight = null;
                } else {
                    content.style.maxHeight = content.scrollHeight + "px";
                }
            });
        }
        
        // Handle form submission
        document.getElementById('submit-btn').addEventListener('click', async () => {
            const prompt = document.getElementById('prompt').value;
            if (!prompt) return;
            
            document.getElementById('response').innerHTML = '<p>Processing...</p>';
            document.getElementById('tools-used').style.display = 'none';
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ prompt }),
                });
                
                const data = await response.json();
                
                // Display the response
                document.getElementById('response').innerHTML = `<p>${data.response}</p>`;
                
                // Display tools used if any
                const toolsUsedContainer = document.getElementById('tool-usage-container');
                toolsUsedContainer.innerHTML = '';
                
                if (data.tools_used && data.tools_used.length > 0) {
                    document.getElementById('tools-used').style.display = 'block';
                    
                    data.tools_used.forEach((tool, index) => {
                        const toolDiv = document.createElement('div');
                        toolDiv.className = 'tool-usage';
                        
                        const toolName = document.createElement('h3');
                        toolName.textContent = tool.name;
                        toolDiv.appendChild(toolName);
                        
                        const toolDesc = document.createElement('p');
                        toolDesc.textContent = tool.description;
                        toolDiv.appendChild(toolDesc);
                        
                        const argsTitle = document.createElement('strong');
                        argsTitle.textContent = 'Arguments:';
                        toolDiv.appendChild(argsTitle);
                        
                        const argsDiv = document.createElement('div');
                        argsDiv.className = 'tool-args';
                        argsDiv.textContent = JSON.stringify(tool.arguments, null, 2);
                        toolDiv.appendChild(argsDiv);
                        
                        const resultTitle = document.createElement('strong');
                        resultTitle.textContent = 'Result:';
                        toolDiv.appendChild(resultTitle);
                        
                        const resultDiv = document.createElement('div');
                        resultDiv.className = 'tool-result';
                        resultDiv.textContent = JSON.stringify(tool.result, null, 2);
                        toolDiv.appendChild(resultDiv);
                        
                        toolsUsedContainer.appendChild(toolDiv);
                    });
                }
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
        # Get the response which now includes both the text and tool usage info
        result = chat_manager.chat(prompt)
        
        # Return the complete result
        return jsonify({
            'response': result.get('response', 'No response received'),
            'tools_used': result.get('tools_used', [])
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 12000))
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=True)