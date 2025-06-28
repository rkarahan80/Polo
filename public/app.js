class VideoGenerationApp {
    constructor() {
        this.currentTab = 'generate';
        this.projects = [];
        this.history = [];
        this.templates = [];
        this.ws = null;
        this.currentGeneration = null;
        
        this.init();
    }

    init() {
        this.setupWebSocket();
        this.setupEventListeners();
        this.loadData();
        this.setupDefaultTemplates();
    }

    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            this.updateConnectionStatus(true);
        };
        
        this.ws.onclose = () => {
            this.updateConnectionStatus(false);
            // Attempt to reconnect after 3 seconds
            setTimeout(() => this.setupWebSocket(), 3000);
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
    }

    updateConnectionStatus(connected) {
        const statusDot = document.getElementById('connection-status');
        const statusText = document.getElementById('status-text');
        
        if (connected) {
            statusDot.style.backgroundColor = 'var(--success-color)';
            statusText.textContent = 'Connected';
        } else {
            statusDot.style.backgroundColor = 'var(--error-color)';
            statusText.textContent = 'Disconnected';
        }
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'generation_progress':
                this.updateGenerationProgress(data.progress, data.message);
                break;
            case 'generation_complete':
                this.handleGenerationComplete(data.result);
                break;
            case 'generation_error':
                this.handleGenerationError(data.error);
                break;
            case 'project_created':
            case 'project_updated':
                this.loadProjects();
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const tab = e.currentTarget.dataset.tab;
                this.switchTab(tab);
            });
        });

        // Generation form
        document.getElementById('generation-type').addEventListener('change', this.handleGenerationTypeChange.bind(this));
        document.getElementById('generate-btn').addEventListener('click', this.handleGenerate.bind(this));
        document.getElementById('duration-slider').addEventListener('input', this.updateDurationValue.bind(this));
        
        // File upload
        document.getElementById('upload-area').addEventListener('click', () => {
            document.getElementById('image-upload').click();
        });
        document.getElementById('image-upload').addEventListener('change', this.handleFileUpload.bind(this));
        
        // Drag and drop
        const uploadArea = document.getElementById('upload-area');
        uploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
        uploadArea.addEventListener('drop', this.handleDrop.bind(this));

        // Prompt suggestions
        document.querySelectorAll('.suggestion-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.getElementById('prompt-input').value = e.target.dataset.prompt;
            });
        });

        // Project management
        document.getElementById('new-project-btn').addEventListener('click', this.showProjectModal.bind(this));
        document.getElementById('create-project-btn').addEventListener('click', this.showProjectModal.bind(this));
        document.getElementById('save-project-btn').addEventListener('click', this.saveProject.bind(this));
        document.getElementById('cancel-project-btn').addEventListener('click', this.hideProjectModal.bind(this));

        // Template management
        document.getElementById('save-template-btn').addEventListener('click', this.showTemplateModal.bind(this));
        document.getElementById('create-template-btn').addEventListener('click', this.showTemplateModal.bind(this));
        document.getElementById('save-template-btn-modal').addEventListener('click', this.saveTemplate.bind(this));
        document.getElementById('cancel-template-btn').addEventListener('click', this.hideTemplateModal.bind(this));

        // Modal close buttons
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.target.closest('.modal').classList.remove('active');
            });
        });

        // Batch processing
        document.getElementById('batch-type').addEventListener('change', this.handleBatchTypeChange.bind(this));
        document.getElementById('start-batch-btn').addEventListener('click', this.startBatchProcessing.bind(this));

        // Settings
        document.getElementById('save-settings-btn').addEventListener('click', this.saveSettings.bind(this));

        // Template categories
        document.querySelectorAll('.category-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.category-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.filterTemplates(e.target.dataset.category);
            });
        });
    }

    switchTab(tabName) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update content
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');

        // Update page title
        const titles = {
            generate: 'Video Generation',
            projects: 'My Projects',
            history: 'Generation History',
            templates: 'Prompt Templates',
            batch: 'Batch Processing',
            analytics: 'Analytics Dashboard',
            settings: 'Settings'
        };
        document.getElementById('page-title').textContent = titles[tabName];

        this.currentTab = tabName;

        // Load tab-specific data
        switch (tabName) {
            case 'projects':
                this.loadProjects();
                break;
            case 'history':
                this.loadHistory();
                break;
            case 'templates':
                this.loadTemplates();
                break;
            case 'analytics':
                this.loadAnalytics();
                break;
        }
    }

    handleGenerationTypeChange(e) {
        const type = e.target.value;
        const imageUploadGroup = document.getElementById('image-upload-group');
        
        if (type === 'text-to-video') {
            imageUploadGroup.style.display = 'none';
        } else {
            imageUploadGroup.style.display = 'block';
        }
    }

    updateDurationValue() {
        const slider = document.getElementById('duration-slider');
        const valueSpan = document.getElementById('duration-value');
        valueSpan.textContent = `${slider.value}s`;
    }

    handleFileUpload(e) {
        const file = e.target.files[0];
        if (file) {
            this.uploadFile(file);
        }
    }

    handleDragOver(e) {
        e.preventDefault();
        e.currentTarget.classList.add('drag-over');
    }

    handleDrop(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.uploadFile(files[0]);
        }
    }

    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                this.showUploadPreview(result);
                this.showNotification('File uploaded successfully', 'success');
            } else {
                throw new Error('Upload failed');
            }
        } catch (error) {
            this.showNotification('Upload failed: ' + error.message, 'error');
        }
    }

    showUploadPreview(fileInfo) {
        const preview = document.getElementById('upload-preview');
        const isVideo = fileInfo.originalName.match(/\.(mp4|mov|avi|webm)$/i);
        
        preview.innerHTML = `
            <div class="upload-preview-item">
                ${isVideo ? 
                    `<video src="${fileInfo.path}" controls style="max-width: 200px; max-height: 150px;"></video>` :
                    `<img src="${fileInfo.path}" alt="Preview" style="max-width: 200px; max-height: 150px; object-fit: cover;">`
                }
                <p>${fileInfo.originalName}</p>
                <button class="btn btn-secondary btn-sm" onclick="this.parentElement.remove()">Remove</button>
            </div>
        `;
    }

    async handleGenerate() {
        const generationType = document.getElementById('generation-type').value;
        const model = document.getElementById('model-select').value;
        const prompt = document.getElementById('prompt-input').value.trim();
        const duration = parseInt(document.getElementById('duration-slider').value);
        const resolution = document.getElementById('resolution-select').value;
        const seed = document.getElementById('seed-input').value;
        const projectId = document.getElementById('project-select').value;

        if (!prompt) {
            this.showNotification('Please enter a text prompt', 'error');
            return;
        }

        // Show progress
        this.showGenerationProgress();
        
        // Simulate generation process
        this.simulateGeneration({
            type: generationType,
            model,
            prompt,
            duration,
            resolution,
            seed,
            projectId
        });
    }

    showGenerationProgress() {
        document.getElementById('generation-progress').style.display = 'block';
        document.getElementById('preview-actions').style.display = 'none';
        document.getElementById('generate-btn').disabled = true;
    }

    hideGenerationProgress() {
        document.getElementById('generation-progress').style.display = 'none';
        document.getElementById('generate-btn').disabled = false;
    }

    updateGenerationProgress(progress, message) {
        document.getElementById('progress-fill').style.width = `${progress}%`;
        document.getElementById('progress-text').textContent = message;
    }

    simulateGeneration(params) {
        let progress = 0;
        const steps = [
            { progress: 10, message: 'Initializing generation...' },
            { progress: 30, message: 'Processing prompt...' },
            { progress: 50, message: 'Generating frames...' },
            { progress: 80, message: 'Rendering video...' },
            { progress: 100, message: 'Complete!' }
        ];

        const interval = setInterval(() => {
            if (progress < steps.length) {
                const step = steps[progress];
                this.updateGenerationProgress(step.progress, step.message);
                progress++;
            } else {
                clearInterval(interval);
                setTimeout(() => {
                    this.handleGenerationComplete({
                        videoUrl: 'https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4',
                        params
                    });
                }, 1000);
            }
        }, 1500);
    }

    handleGenerationComplete(result) {
        this.hideGenerationProgress();
        
        // Show video preview
        const preview = document.getElementById('video-preview');
        preview.innerHTML = `
            <video controls style="width: 100%; height: 100%; object-fit: cover;">
                <source src="${result.videoUrl}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
        `;
        
        document.getElementById('preview-actions').style.display = 'flex';
        
        // Add to history
        this.addToHistory(result);
        
        this.showNotification('Video generated successfully!', 'success');
    }

    handleGenerationError(error) {
        this.hideGenerationProgress();
        this.showNotification('Generation failed: ' + error, 'error');
    }

    addToHistory(result) {
        const historyItem = {
            id: Date.now().toString(),
            prompt: result.params.prompt,
            model: result.params.model,
            type: result.params.type,
            videoUrl: result.videoUrl,
            createdAt: new Date().toISOString(),
            ...result.params
        };

        fetch('/api/history', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(historyItem)
        });
    }

    showProjectModal() {
        document.getElementById('project-modal').classList.add('active');
        document.getElementById('project-form').reset();
    }

    hideProjectModal() {
        document.getElementById('project-modal').classList.remove('active');
    }

    async saveProject() {
        const name = document.getElementById('project-name').value.trim();
        const description = document.getElementById('project-description').value.trim();

        if (!name) {
            this.showNotification('Please enter a project name', 'error');
            return;
        }

        try {
            const response = await fetch('/api/projects', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, description })
            });

            if (response.ok) {
                const project = await response.json();
                this.hideProjectModal();
                this.showNotification('Project created successfully', 'success');
                this.loadProjects();
                this.updateProjectSelect();
            } else {
                throw new Error('Failed to create project');
            }
        } catch (error) {
            this.showNotification('Failed to create project: ' + error.message, 'error');
        }
    }

    async loadProjects() {
        try {
            const response = await fetch('/api/projects');
            if (response.ok) {
                this.projects = await response.json();
                this.renderProjects();
                this.updateProjectSelect();
            }
        } catch (error) {
            console.error('Failed to load projects:', error);
        }
    }

    renderProjects() {
        const grid = document.getElementById('projects-grid');
        
        if (this.projects.length === 0) {
            grid.innerHTML = `
                <div class="text-center" style="grid-column: 1 / -1;">
                    <i class="fas fa-folder-open" style="font-size: 3rem; color: var(--text-secondary); margin-bottom: 1rem;"></i>
                    <p>No projects yet. Create your first project to get started!</p>
                </div>
            `;
            return;
        }

        grid.innerHTML = this.projects.map(project => `
            <div class="project-card" data-project-id="${project.id}">
                <h4>${project.name}</h4>
                <p>${project.description || 'No description'}</p>
                <div class="project-meta">
                    <span>${project.videos?.length || 0} videos</span>
                    <span>${new Date(project.createdAt).toLocaleDateString()}</span>
                </div>
            </div>
        `).join('');
    }

    updateProjectSelect() {
        const select = document.getElementById('project-select');
        select.innerHTML = '<option value="">No Project</option>' +
            this.projects.map(project => 
                `<option value="${project.id}">${project.name}</option>`
            ).join('');
    }

    showTemplateModal() {
        const prompt = document.getElementById('prompt-input').value.trim();
        if (!prompt) {
            this.showNotification('Please enter a prompt first', 'error');
            return;
        }
        
        document.getElementById('template-modal').classList.add('active');
        document.getElementById('template-form').reset();
    }

    hideTemplateModal() {
        document.getElementById('template-modal').classList.remove('active');
    }

    async saveTemplate() {
        const name = document.getElementById('template-name').value.trim();
        const description = document.getElementById('template-description').value.trim();
        const category = document.getElementById('template-category').value;
        const isPublic = document.getElementById('template-public').checked;
        const prompt = document.getElementById('prompt-input').value.trim();

        if (!name || !prompt) {
            this.showNotification('Please enter a name and ensure you have a prompt', 'error');
            return;
        }

        const settings = {
            model: document.getElementById('model-select').value,
            duration: parseInt(document.getElementById('duration-slider').value),
            resolution: document.getElementById('resolution-select').value
        };

        try {
            const response = await fetch('/api/templates', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, description, prompt, category, isPublic, settings })
            });

            if (response.ok) {
                this.hideTemplateModal();
                this.showNotification('Template saved successfully', 'success');
                this.loadTemplates();
            } else {
                throw new Error('Failed to save template');
            }
        } catch (error) {
            this.showNotification('Failed to save template: ' + error.message, 'error');
        }
    }

    async loadTemplates() {
        try {
            const response = await fetch('/api/templates');
            if (response.ok) {
                this.templates = await response.json();
                this.renderTemplates();
            }
        } catch (error) {
            console.error('Failed to load templates:', error);
        }
    }

    renderTemplates(category = 'all') {
        const grid = document.getElementById('templates-grid');
        const filteredTemplates = category === 'all' ? 
            this.templates : 
            this.templates.filter(t => t.category === category);

        if (filteredTemplates.length === 0) {
            grid.innerHTML = `
                <div class="text-center" style="grid-column: 1 / -1;">
                    <i class="fas fa-bookmark" style="font-size: 3rem; color: var(--text-secondary); margin-bottom: 1rem;"></i>
                    <p>No templates in this category yet.</p>
                </div>
            `;
            return;
        }

        grid.innerHTML = filteredTemplates.map(template => `
            <div class="template-card" data-template-id="${template.id}">
                <h4>${template.name}</h4>
                <p>${template.description || 'No description'}</p>
                <div class="template-prompt">
                    <strong>Prompt:</strong> ${template.prompt.substring(0, 100)}${template.prompt.length > 100 ? '...' : ''}
                </div>
                <div class="template-actions" style="margin-top: 1rem;">
                    <button class="btn btn-primary btn-sm" onclick="app.useTemplate('${template.id}')">
                        <i class="fas fa-play"></i> Use Template
                    </button>
                    <button class="btn btn-secondary btn-sm" onclick="app.deleteTemplate('${template.id}')">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </div>
            </div>
        `).join('');
    }

    filterTemplates(category) {
        this.renderTemplates(category);
    }

    useTemplate(templateId) {
        const template = this.templates.find(t => t.id === templateId);
        if (template) {
            // Switch to generate tab
            this.switchTab('generate');
            
            // Fill form with template data
            document.getElementById('prompt-input').value = template.prompt;
            if (template.settings) {
                if (template.settings.model) {
                    document.getElementById('model-select').value = template.settings.model;
                }
                if (template.settings.duration) {
                    document.getElementById('duration-slider').value = template.settings.duration;
                    this.updateDurationValue();
                }
                if (template.settings.resolution) {
                    document.getElementById('resolution-select').value = template.settings.resolution;
                }
            }
            
            this.showNotification('Template loaded successfully', 'success');
        }
    }

    async deleteTemplate(templateId) {
        if (!confirm('Are you sure you want to delete this template?')) {
            return;
        }

        try {
            const response = await fetch(`/api/templates/${templateId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showNotification('Template deleted successfully', 'success');
                this.loadTemplates();
            } else {
                throw new Error('Failed to delete template');
            }
        } catch (error) {
            this.showNotification('Failed to delete template: ' + error.message, 'error');
        }
    }

    async loadHistory(page = 1) {
        try {
            const response = await fetch(`/api/history?page=${page}&limit=20`);
            if (response.ok) {
                const data = await response.json();
                this.renderHistory(data.history);
                this.renderHistoryPagination(data);
            }
        } catch (error) {
            console.error('Failed to load history:', error);
        }
    }

    renderHistory(history) {
        const list = document.getElementById('history-list');
        
        if (history.length === 0) {
            list.innerHTML = `
                <div class="text-center">
                    <i class="fas fa-history" style="font-size: 3rem; color: var(--text-secondary); margin-bottom: 1rem;"></i>
                    <p>No generation history yet. Start creating videos to see them here!</p>
                </div>
            `;
            return;
        }

        list.innerHTML = history.map(item => `
            <div class="history-item">
                <div class="history-thumbnail">
                    ${item.videoUrl ? 
                        `<video src="${item.videoUrl}" style="width: 100%; height: 100%; object-fit: cover;"></video>` :
                        '<div style="display: flex; align-items: center; justify-content: center; height: 100%; background: var(--background-color);"><i class="fas fa-video"></i></div>'
                    }
                </div>
                <div class="history-content">
                    <h4>${item.prompt.substring(0, 50)}${item.prompt.length > 50 ? '...' : ''}</h4>
                    <p><strong>Model:</strong> ${item.model} | <strong>Type:</strong> ${item.type}</p>
                    <div class="history-meta">
                        <span>${new Date(item.createdAt).toLocaleString()}</span>
                        <span>${item.duration}s | ${item.resolution}</span>
                    </div>
                </div>
            </div>
        `).join('');
    }

    renderHistoryPagination(data) {
        const pagination = document.getElementById('history-pagination');
        const { page, totalPages } = data;
        
        if (totalPages <= 1) {
            pagination.innerHTML = '';
            return;
        }

        let buttons = [];
        
        // Previous button
        if (page > 1) {
            buttons.push(`<button onclick="app.loadHistory(${page - 1})">Previous</button>`);
        }
        
        // Page numbers
        for (let i = Math.max(1, page - 2); i <= Math.min(totalPages, page + 2); i++) {
            buttons.push(`<button class="${i === page ? 'active' : ''}" onclick="app.loadHistory(${i})">${i}</button>`);
        }
        
        // Next button
        if (page < totalPages) {
            buttons.push(`<button onclick="app.loadHistory(${page + 1})">Next</button>`);
        }
        
        pagination.innerHTML = buttons.join('');
    }

    handleBatchTypeChange(e) {
        const type = e.target.value;
        const promptsGroup = document.getElementById('batch-prompts-group');
        const filesGroup = document.getElementById('batch-files-group');
        
        if (type === 'prompts') {
            promptsGroup.style.display = 'block';
            filesGroup.style.display = 'none';
        } else {
            promptsGroup.style.display = 'none';
            filesGroup.style.display = 'block';
        }
    }

    startBatchProcessing() {
        const type = document.getElementById('batch-type').value;
        
        if (type === 'prompts') {
            const prompts = document.getElementById('batch-prompts').value
                .split('\n')
                .map(p => p.trim())
                .filter(p => p.length > 0);
            
            if (prompts.length === 0) {
                this.showNotification('Please enter at least one prompt', 'error');
                return;
            }
            
            this.processBatchPrompts(prompts);
        } else {
            const files = document.getElementById('batch-files').files;
            
            if (files.length === 0) {
                this.showNotification('Please select at least one file', 'error');
                return;
            }
            
            this.processBatchFiles(files);
        }
    }

    processBatchPrompts(prompts) {
        const status = document.getElementById('batch-status');
        const queue = document.getElementById('batch-queue');
        
        status.innerHTML = `<p>Processing ${prompts.length} prompts...</p>`;
        
        queue.innerHTML = prompts.map((prompt, index) => `
            <div class="batch-item" id="batch-item-${index}">
                <span>${prompt.substring(0, 50)}${prompt.length > 50 ? '...' : ''}</span>
                <span class="batch-item-status">Queued</span>
            </div>
        `).join('');
        
        // Simulate batch processing
        this.simulateBatchProcessing(prompts);
    }

    simulateBatchProcessing(items) {
        let currentIndex = 0;
        
        const processNext = () => {
            if (currentIndex >= items.length) {
                document.getElementById('batch-status').innerHTML = '<p>Batch processing complete!</p>';
                return;
            }
            
            const itemElement = document.getElementById(`batch-item-${currentIndex}`);
            itemElement.querySelector('.batch-item-status').textContent = 'Processing...';
            
            // Simulate processing time
            setTimeout(() => {
                itemElement.querySelector('.batch-item-status').textContent = 'Complete';
                itemElement.style.backgroundColor = 'var(--success-color)';
                itemElement.style.color = 'white';
                
                currentIndex++;
                processNext();
            }, 2000 + Math.random() * 3000);
        };
        
        processNext();
    }

    async loadAnalytics() {
        try {
            const response = await fetch('/api/analytics');
            if (response.ok) {
                const data = await response.json();
                this.renderAnalytics(data);
            }
        } catch (error) {
            console.error('Failed to load analytics:', error);
        }
    }

    renderAnalytics(data) {
        document.getElementById('total-generations').textContent = data.totalGenerations;
        document.getElementById('total-projects').textContent = data.totalProjects;
        document.getElementById('total-templates').textContent = data.totalTemplates;
        
        // Render recent activity
        const recentActivity = document.getElementById('recent-activity');
        recentActivity.innerHTML = data.recentActivity.map(item => `
            <div style="padding: 0.5rem; border-bottom: 1px solid var(--border-color);">
                <strong>${item.prompt.substring(0, 30)}...</strong><br>
                <small>${new Date(item.createdAt).toLocaleString()}</small>
            </div>
        `).join('');
    }

    saveSettings() {
        const settings = {
            runwayApiKey: document.getElementById('runway-api-key').value,
            openaiApiKey: document.getElementById('openai-api-key').value,
            defaultModel: document.getElementById('default-model').value,
            defaultDuration: document.getElementById('default-duration').value,
            autoCleanup: document.getElementById('auto-cleanup').checked,
            enableGpu: document.getElementById('enable-gpu').checked
        };
        
        localStorage.setItem('videoGenSettings', JSON.stringify(settings));
        this.showNotification('Settings saved successfully', 'success');
    }

    loadSettings() {
        const settings = JSON.parse(localStorage.getItem('videoGenSettings') || '{}');
        
        if (settings.runwayApiKey) {
            document.getElementById('runway-api-key').value = settings.runwayApiKey;
        }
        if (settings.openaiApiKey) {
            document.getElementById('openai-api-key').value = settings.openaiApiKey;
        }
        if (settings.defaultModel) {
            document.getElementById('default-model').value = settings.defaultModel;
            document.getElementById('model-select').value = settings.defaultModel;
        }
        if (settings.defaultDuration) {
            document.getElementById('default-duration').value = settings.defaultDuration;
            document.getElementById('duration-slider').value = settings.defaultDuration;
            this.updateDurationValue();
        }
        if (settings.autoCleanup !== undefined) {
            document.getElementById('auto-cleanup').checked = settings.autoCleanup;
        }
        if (settings.enableGpu !== undefined) {
            document.getElementById('enable-gpu').checked = settings.enableGpu;
        }
    }

    setupDefaultTemplates() {
        const defaultTemplates = [
            {
                name: 'Serene Nature',
                description: 'Peaceful natural scenes',
                prompt: 'A serene lake at sunset with gentle ripples and mountains in the background',
                category: 'nature'
            },
            {
                name: 'Urban Cityscape',
                description: 'Modern city environments',
                prompt: 'A bustling city street at night with neon lights and traffic',
                category: 'urban'
            },
            {
                name: 'Abstract Motion',
                description: 'Creative abstract visuals',
                prompt: 'Colorful abstract shapes flowing and morphing in space',
                category: 'abstract'
            }
        ];

        // Only add if no templates exist
        if (this.templates.length === 0) {
            defaultTemplates.forEach(template => {
                fetch('/api/templates', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(template)
                });
            });
        }
    }

    async loadData() {
        await Promise.all([
            this.loadProjects(),
            this.loadTemplates(),
            this.loadHistory()
        ]);
        
        this.loadSettings();
        this.updateDurationValue();
    }

    showNotification(message, type = 'info') {
        const container = document.getElementById('notification-container');
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: inherit; cursor: pointer;">&times;</button>
            </div>
        `;
        
        container.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
}

// Initialize the app when the page loads
const app = new VideoGenerationApp();

// Make app globally available for onclick handlers
window.app = app;