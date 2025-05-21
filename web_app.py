"""
Web interface for the Tool Calling System.
"""

import os

from flask import Flask, jsonify, render_template, request # Added render_template

from config import DEFAULT_MODEL
from toolCalling import ChatManager

app = Flask(__name__)
chat_manager = ChatManager(DEFAULT_MODEL)

@app.route('/')
def index():
    """Render the main page."""
    # Pass only the necessary tool information (name and description)
    # The tools attribute in ChatManager.tools is a dict: Dict[str, BaseTool]
    # BaseTool has name and description attributes.
    display_tools = {
        name: {'name': tool.name, 'description': tool.description} 
        for name, tool in chat_manager.tools.tools.items()
    }
    return render_template('index.html', tools=display_tools)

@app.route('/api/chat', methods=['POST'])
def chat():
    """API endpoint for chat interactions."""
    data = request.json
    
    if data is None:
        return jsonify({'error': 'Request must be JSON'}), 400
        
    prompt = data.get('prompt', '')
    
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    
    try:
        # Get the response which now includes both the text and tool usage info
        result = chat_manager.chat(prompt)
        
        response_text = 'Error: No result from chat manager'
        tools_used_list = []

        if result is not None:
            response_text = result.get('response', 'No response received or error in processing')
            tools_used_list = result.get('tools_used', [])
        
        # Return the complete result
        return jsonify({
            'response': response_text,
            'tools_used': tools_used_list
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 12000))
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=True)
