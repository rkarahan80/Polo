class AIAssistant {
    constructor() {
        this.isActive = false;
        this.conversationHistory = [];
        this.suggestions = [];
        this.currentContext = null;
        
        this.init();
    }

    init() {
        this.createAssistantInterface();
        this.setupEventListeners();
        this.loadPersonality();
    }

    createAssistantInterface() {
        const assistantHTML = `
            <div class="ai-assistant" id="ai-assistant">
                <div class="assistant-header">
                    <div class="assistant-avatar">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="assistant-info">
                        <h4>AI Creative Assistant</h4>
                        <span class="assistant-status">Ready to help</span>
                    </div>
                    <button class="assistant-toggle" id="assistant-toggle">
                        <i class="fas fa-chevron-down"></i>
                    </button>
                </div>
                
                <div class="assistant-content" id="assistant-content">
                    <div class="conversation-area" id="conversation-area">
                        <div class="welcome-message">
                            <p>👋 Hi! I'm your AI creative assistant. I can help you:</p>
                            <ul>
                                <li>🎨 Generate creative prompts</li>
                                <li>🎬 Suggest video concepts</li>
                                <li>⚡ Optimize generation settings</li>
                                <li>🔧 Troubleshoot issues</li>
                                <li>💡 Provide creative inspiration</li>
                            </ul>
                            <p>What would you like to create today?</p>
                        </div>
                    </div>
                    
                    <div class="quick-actions">
                        <button class="quick-action-btn" data-action="suggest-prompt">
                            <i class="fas fa-lightbulb"></i> Suggest Prompt
                        </button>
                        <button class="quick-action-btn" data-action="optimize-settings">
                            <i class="fas fa-cog"></i> Optimize Settings
                        </button>
                        <button class="quick-action-btn" data-action="creative-ideas">
                            <i class="fas fa-palette"></i> Creative Ideas
                        </button>
                        <button class="quick-action-btn" data-action="troubleshoot">
                            <i class="fas fa-wrench"></i> Troubleshoot
                        </button>
                    </div>
                    
                    <div class="input-area">
                        <input type="text" id="assistant-input" placeholder="Ask me anything about video creation...">
                        <button id="send-message-btn">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    </div>
                    
                    <div class="smart-suggestions" id="smart-suggestions">
                        <!-- Dynamic suggestions will appear here -->
                    </div>
                </div>
            </div>
        `;
        
        return assistantHTML;
    }

    setupEventListeners() {
        document.getElementById('assistant-toggle')?.addEventListener('click', () => this.toggleAssistant());
        document.getElementById('send-message-btn')?.addEventListener('click', () => this.sendMessage());
        document.getElementById('assistant-input')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
        
        document.querySelectorAll('.quick-action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleQuickAction(e.target.dataset.action));
        });
        
        // Context-aware suggestions
        this.setupContextListeners();
    }

    setupContextListeners() {
        // Listen for prompt input changes
        const promptInput = document.getElementById('prompt-input');
        if (promptInput) {
            promptInput.addEventListener('input', (e) => {
                this.analyzePromptContext(e.target.value);
            });
        }
        
        // Listen for model changes
        const modelSelect = document.getElementById('model-select');
        if (modelSelect) {
            modelSelect.addEventListener('change', (e) => {
                this.updateModelSuggestions(e.target.value);
            });
        }
    }

    toggleAssistant() {
        this.isActive = !this.isActive;
        const content = document.getElementById('assistant-content');
        const toggle = document.getElementById('assistant-toggle');
        
        if (this.isActive) {
            content.style.display = 'block';
            toggle.innerHTML = '<i class="fas fa-chevron-up"></i>';
        } else {
            content.style.display = 'none';
            toggle.innerHTML = '<i class="fas fa-chevron-down"></i>';
        }
    }

    async sendMessage() {
        const input = document.getElementById('assistant-input');
        const message = input.value.trim();
        
        if (!message) return;
        
        this.addMessageToConversation('user', message);
        input.value = '';
        
        // Show typing indicator
        this.showTypingIndicator();
        
        // Process the message
        const response = await this.processMessage(message);
        this.hideTypingIndicator();
        this.addMessageToConversation('assistant', response);
    }

    addMessageToConversation(sender, message) {
        const conversationArea = document.getElementById('conversation-area');
        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender}-message`;
        
        if (sender === 'user') {
            messageElement.innerHTML = `
                <div class="message-content">${message}</div>
                <div class="message-time">${new Date().toLocaleTimeString()}</div>
            `;
        } else {
            messageElement.innerHTML = `
                <div class="assistant-avatar-small">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="message-content">${message}</div>
                <div class="message-time">${new Date().toLocaleTimeString()}</div>
            `;
        }
        
        conversationArea.appendChild(messageElement);
        conversationArea.scrollTop = conversationArea.scrollHeight;
        
        // Store in conversation history
        this.conversationHistory.push({ sender, message, timestamp: Date.now() });
    }

    showTypingIndicator() {
        const conversationArea = document.getElementById('conversation-area');
        const typingElement = document.createElement('div');
        typingElement.className = 'typing-indicator';
        typingElement.id = 'typing-indicator';
        typingElement.innerHTML = `
            <div class="assistant-avatar-small">
                <i class="fas fa-robot"></i>
            </div>
            <div class="typing-dots">
                <span></span><span></span><span></span>
            </div>
        `;
        conversationArea.appendChild(typingElement);
        conversationArea.scrollTop = conversationArea.scrollHeight;
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    async processMessage(message) {
        // Simulate AI processing with intelligent responses
        await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));
        
        const lowerMessage = message.toLowerCase();
        
        // Intent recognition and response generation
        if (lowerMessage.includes('prompt') || lowerMessage.includes('idea')) {
            return this.generatePromptSuggestion();
        } else if (lowerMessage.includes('setting') || lowerMessage.includes('parameter')) {
            return this.generateSettingsSuggestion();
        } else if (lowerMessage.includes('error') || lowerMessage.includes('problem')) {
            return this.generateTroubleshootingResponse();
        } else if (lowerMessage.includes('creative') || lowerMessage.includes('inspiration')) {
            return this.generateCreativeIdeas();
        } else {
            return this.generateGeneralResponse(message);
        }
    }

    generatePromptSuggestion() {
        const suggestions = [
            "🎬 How about: 'A majestic dragon soaring through clouds at golden hour, cinematic lighting, 4K quality'?",
            "🌟 Try this: 'Futuristic city with flying cars, neon reflections on wet streets, cyberpunk aesthetic'",
            "🌊 Consider: 'Ocean waves crashing against cliffs during a storm, dramatic lighting, slow motion'",
            "🦋 What about: 'Butterfly emerging from cocoon in time-lapse, macro photography, nature documentary style'",
            "🏰 How about: 'Medieval castle on a hilltop during sunrise, misty atmosphere, epic fantasy style'"
        ];
        
        const suggestion = suggestions[Math.floor(Math.random() * suggestions.length)];
        return `${suggestion}\n\nWould you like me to suggest variations or help optimize the settings for this prompt?`;
    }

    generateSettingsSuggestion() {
        const currentModel = document.getElementById('model-select')?.value || 'RunwayML';
        
        return `⚙️ For ${currentModel}, I recommend:\n\n` +
               `• **Duration**: Start with 5-10 seconds for better quality\n` +
               `• **Resolution**: 1280x720 for balanced quality/speed\n` +
               `• **Seed**: Use a fixed seed (like 42) for consistent results\n\n` +
               `💡 **Pro tip**: Shorter videos with detailed prompts often produce better results than longer, vague ones!`;
    }

    generateTroubleshootingResponse() {
        return `🔧 **Common issues and solutions:**\n\n` +
               `• **Blurry output**: Try reducing duration or increasing detail in prompt\n` +
               `• **Slow generation**: Check your internet connection and API limits\n` +
               `• **Unexpected results**: Be more specific in your prompt description\n` +
               `• **API errors**: Verify your API key and account credits\n\n` +
               `Need help with a specific error? Share the details and I'll help you fix it! 🚀`;
    }

    generateCreativeIdeas() {
        const themes = [
            "🌌 **Space & Sci-Fi**: Explore alien worlds, space stations, or futuristic technology",
            "🏞️ **Nature & Wildlife**: Capture the beauty of landscapes, animals in their habitat",
            "🎭 **Fantasy & Magic**: Create mystical creatures, enchanted forests, magical spells",
            "🏙️ **Urban & Architecture**: Modern cityscapes, architectural marvels, street life",
            "🎨 **Abstract & Artistic**: Flowing colors, geometric patterns, surreal compositions"
        ];
        
        const randomTheme = themes[Math.floor(Math.random() * themes.length)];
        
        return `✨ **Creative inspiration for you:**\n\n${randomTheme}\n\n` +
               `🎯 **Quick challenge**: Try combining two different themes for unique results!\n\n` +
               `Want more specific ideas for any of these themes? Just ask! 🎬`;
    }

    generateGeneralResponse(message) {
        const responses = [
            "That's an interesting question! Let me help you explore that idea further. What specific aspect would you like to focus on?",
            "I'd love to help you with that! Could you provide a bit more context about what you're trying to achieve?",
            "Great question! Based on your input, I think we can create something amazing together. What's your vision?",
            "I'm here to help make your creative vision come to life! Tell me more about what you have in mind.",
            "Excellent! Let's brainstorm some ideas. What style or mood are you going for?"
        ];
        
        return responses[Math.floor(Math.random() * responses.length)];
    }

    handleQuickAction(action) {
        switch (action) {
            case 'suggest-prompt':
                this.addMessageToConversation('assistant', this.generatePromptSuggestion());
                break;
            case 'optimize-settings':
                this.addMessageToConversation('assistant', this.generateSettingsSuggestion());
                break;
            case 'creative-ideas':
                this.addMessageToConversation('assistant', this.generateCreativeIdeas());
                break;
            case 'troubleshoot':
                this.addMessageToConversation('assistant', this.generateTroubleshootingResponse());
                break;
        }
    }

    analyzePromptContext(prompt) {
        if (!prompt || prompt.length < 10) return;
        
        const suggestions = this.generateContextualSuggestions(prompt);
        this.displaySmartSuggestions(suggestions);
    }

    generateContextualSuggestions(prompt) {
        const suggestions = [];
        const lowerPrompt = prompt.toLowerCase();
        
        // Analyze prompt content and suggest improvements
        if (!lowerPrompt.includes('lighting')) {
            suggestions.push({
                type: 'enhancement',
                text: 'Add lighting description',
                suggestion: 'Consider adding "cinematic lighting" or "golden hour" to enhance the mood'
            });
        }
        
        if (!lowerPrompt.includes('camera') && !lowerPrompt.includes('shot')) {
            suggestions.push({
                type: 'enhancement',
                text: 'Add camera movement',
                suggestion: 'Try adding "slow zoom in" or "pan left" for dynamic movement'
            });
        }
        
        if (prompt.length < 20) {
            suggestions.push({
                type: 'improvement',
                text: 'Add more detail',
                suggestion: 'More descriptive prompts typically produce better results'
            });
        }
        
        return suggestions;
    }

    displaySmartSuggestions(suggestions) {
        const suggestionsContainer = document.getElementById('smart-suggestions');
        
        if (suggestions.length === 0) {
            suggestionsContainer.innerHTML = '';
            return;
        }
        
        suggestionsContainer.innerHTML = `
            <div class="suggestions-header">💡 Smart Suggestions</div>
            ${suggestions.map(suggestion => `
                <div class="suggestion-item" data-suggestion="${suggestion.suggestion}">
                    <span class="suggestion-type">${suggestion.type}</span>
                    <span class="suggestion-text">${suggestion.text}</span>
                    <button class="apply-suggestion-btn">Apply</button>
                </div>
            `).join('')}
        `;
        
        // Add click handlers for applying suggestions
        suggestionsContainer.querySelectorAll('.apply-suggestion-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const suggestionItem = e.target.closest('.suggestion-item');
                const suggestion = suggestionItem.dataset.suggestion;
                this.applySuggestion(suggestion);
            });
        });
    }

    applySuggestion(suggestion) {
        const promptInput = document.getElementById('prompt-input');
        if (promptInput) {
            const currentPrompt = promptInput.value;
            promptInput.value = currentPrompt + (currentPrompt ? ', ' : '') + suggestion;
            this.showNotification('Suggestion applied to prompt!', 'success');
        }
    }

    updateModelSuggestions(model) {
        let suggestion = '';
        
        switch (model) {
            case 'RunwayML':
                suggestion = '🚀 RunwayML works great with detailed, cinematic prompts. Try adding camera movements and lighting descriptions!';
                break;
            case 'damo-vilab/text-to-video-ms-1.7b':
                suggestion = '🔬 ModelScope T2V excels with clear, simple descriptions. Keep prompts concise but descriptive!';
                break;
            default:
                suggestion = '✨ This model works best with well-structured prompts. Be specific about what you want to see!';
        }
        
        this.addMessageToConversation('assistant', suggestion);
    }

    loadPersonality() {
        // Load assistant personality and preferences
        this.personality = {
            tone: 'helpful and creative',
            expertise: ['video generation', 'creative writing', 'technical optimization'],
            style: 'encouraging and informative'
        };
    }

    showNotification(message, type) {
        if (window.app && window.app.showNotification) {
            window.app.showNotification(message, type);
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AIAssistant;
} else {
    window.AIAssistant = AIAssistant;
}