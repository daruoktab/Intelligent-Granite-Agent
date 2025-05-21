document.addEventListener('DOMContentLoaded', () => {
    const darkModeToggle = document.getElementById('darkModeToggle');
    const body = document.body;

    // Function to apply the saved theme or default to light
    const applyTheme = () => {
        const currentTheme = localStorage.getItem('theme');
        if (currentTheme === 'dark') {
            body.classList.add('dark-mode');
            darkModeToggle.textContent = 'Light Mode';
        } else {
            body.classList.remove('dark-mode');
            darkModeToggle.textContent = 'Dark Mode';
        }
    };

    // Apply theme on initial load
    applyTheme();

    // Toggle dark mode
    darkModeToggle.addEventListener('click', () => {
        body.classList.toggle('dark-mode');
        if (body.classList.contains('dark-mode')) {
            localStorage.setItem('theme', 'dark');
            darkModeToggle.textContent = 'Light Mode';
        } else {
            localStorage.setItem('theme', 'light');
            darkModeToggle.textContent = 'Dark Mode';
        }
    });

    // Handle collapsible sections
    const collapsibles = document.getElementsByClassName("collapsible");
    for (let i = 0; i < collapsibles.length; i++) {
        collapsibles[i].addEventListener("click", function() {
            this.classList.toggle("active");
            const content = this.nextElementSibling;
            if (content.style.maxHeight) {
                content.style.maxHeight = null;
                content.classList.remove("open");
            } else {
                content.style.maxHeight = content.scrollHeight + "px";
                content.classList.add("open");
            }
        });
    }

    const submitButton = document.getElementById('submit-btn');
    const promptInput = document.getElementById('prompt');
    const responseDiv = document.getElementById('response');
    const toolsUsedDiv = document.getElementById('tools-used');
    const toolUsageContainer = document.getElementById('tool-usage-container');

    // Handle form submission
    submitButton.addEventListener('click', async () => {
        const prompt = promptInput.value.trim();
        if (!prompt) {
            responseDiv.innerHTML = '<p style="color: red;">Please enter a prompt.</p>';
            return;
        }

        responseDiv.innerHTML = '<p>Processing...</p>';
        toolsUsedDiv.style.display = 'none';
        toolUsageContainer.innerHTML = ''; // Clear previous tool usage

        try {
            const apiResponse = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ prompt }),
            });

            if (!apiResponse.ok) {
                const errorData = await apiResponse.json().catch(() => ({ error: 'Failed to parse error response' }));
                throw new Error(errorData.error || `HTTP error! status: ${apiResponse.status}`);
            }
            
            const data = await apiResponse.json();
            
            // Display the response
            responseDiv.innerHTML = `<p>${data.response || 'No response content received.'}</p>`;
            
            // Display tools used if any
            if (data.tools_used && data.tools_used.length > 0) {
                toolsUsedDiv.style.display = 'block';
                
                data.tools_used.forEach((tool) => {
                    const toolDiv = document.createElement('div');
                    toolDiv.className = 'tool-usage';
                    
                    const toolName = document.createElement('h3');
                    toolName.textContent = tool.name || 'Unnamed Tool';
                    toolDiv.appendChild(toolName);
                    
                    if (tool.description) {
                        const toolDesc = document.createElement('p');
                        toolDesc.textContent = tool.description;
                        toolDiv.appendChild(toolDesc);
                    }
                    
                    const argsTitle = document.createElement('strong');
                    argsTitle.textContent = 'Arguments:';
                    toolDiv.appendChild(argsTitle);
                    
                    const argsDiv = document.createElement('div');
                    argsDiv.className = 'tool-args';
                    argsDiv.textContent = JSON.stringify(tool.arguments, null, 2) || '{}';
                    toolDiv.appendChild(argsDiv);
                    
                    const resultTitle = document.createElement('strong');
                    resultTitle.textContent = 'Result:';
                    toolDiv.appendChild(resultTitle);
                    
                    const resultDiv = document.createElement('div');
                    resultDiv.className = 'tool-result';
                    resultDiv.textContent = JSON.stringify(tool.result, null, 2) || 'No result';
                    toolDiv.appendChild(resultDiv);
                    
                    toolUsageContainer.appendChild(toolDiv);
                });
            }
        } catch (error) {
            console.error('Error during API call:', error);
            responseDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
        }
    });

    // Allow pressing Enter to submit
    promptInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            submitButton.click();
        }
    });
});
