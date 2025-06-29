class VideoEditor {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.video = null;
        this.timeline = null;
        this.effects = [];
        this.transitions = [];
        this.currentTime = 0;
        this.isPlaying = false;
        this.zoom = 1;
        this.selectedClip = null;
        
        this.init();
    }

    init() {
        this.createEditorInterface();
        this.setupEventListeners();
        this.initializeTimeline();
    }

    createEditorInterface() {
        const editorHTML = `
            <div class="video-editor">
                <div class="editor-header">
                    <h3><i class="fas fa-cut"></i> Video Editor</h3>
                    <div class="editor-controls">
                        <button class="btn btn-primary" id="import-video-btn">
                            <i class="fas fa-upload"></i> Import Video
                        </button>
                        <button class="btn btn-secondary" id="export-video-btn">
                            <i class="fas fa-download"></i> Export
                        </button>
                    </div>
                </div>
                
                <div class="editor-workspace">
                    <div class="preview-panel">
                        <canvas id="video-canvas" width="640" height="360"></canvas>
                        <div class="playback-controls">
                            <button id="play-pause-btn"><i class="fas fa-play"></i></button>
                            <button id="stop-btn"><i class="fas fa-stop"></i></button>
                            <span id="time-display">00:00 / 00:00</span>
                            <input type="range" id="volume-slider" min="0" max="100" value="50">
                        </div>
                    </div>
                    
                    <div class="effects-panel">
                        <h4>Effects & Filters</h4>
                        <div class="effects-grid">
                            <button class="effect-btn" data-effect="blur">Blur</button>
                            <button class="effect-btn" data-effect="sharpen">Sharpen</button>
                            <button class="effect-btn" data-effect="vintage">Vintage</button>
                            <button class="effect-btn" data-effect="sepia">Sepia</button>
                            <button class="effect-btn" data-effect="grayscale">Grayscale</button>
                            <button class="effect-btn" data-effect="brightness">Brightness</button>
                            <button class="effect-btn" data-effect="contrast">Contrast</button>
                            <button class="effect-btn" data-effect="saturation">Saturation</button>
                        </div>
                        
                        <h4>Transitions</h4>
                        <div class="transitions-grid">
                            <button class="transition-btn" data-transition="fade">Fade</button>
                            <button class="transition-btn" data-transition="slide">Slide</button>
                            <button class="transition-btn" data-transition="zoom">Zoom</button>
                            <button class="transition-btn" data-transition="dissolve">Dissolve</button>
                        </div>
                        
                        <h4>Text & Graphics</h4>
                        <div class="text-controls">
                            <input type="text" id="text-input" placeholder="Enter text...">
                            <button id="add-text-btn">Add Text</button>
                            <input type="color" id="text-color" value="#ffffff">
                            <select id="font-family">
                                <option value="Arial">Arial</option>
                                <option value="Helvetica">Helvetica</option>
                                <option value="Times">Times</option>
                                <option value="Courier">Courier</option>
                            </select>
                        </div>
                    </div>
                </div>
                
                <div class="timeline-container">
                    <div class="timeline-header">
                        <h4>Timeline</h4>
                        <div class="timeline-controls">
                            <button id="zoom-in-btn"><i class="fas fa-search-plus"></i></button>
                            <button id="zoom-out-btn"><i class="fas fa-search-minus"></i></button>
                            <button id="split-clip-btn"><i class="fas fa-cut"></i> Split</button>
                            <button id="delete-clip-btn"><i class="fas fa-trash"></i> Delete</button>
                        </div>
                    </div>
                    <div class="timeline" id="timeline">
                        <div class="timeline-ruler"></div>
                        <div class="timeline-tracks">
                            <div class="track video-track" data-track="video">
                                <div class="track-label">Video</div>
                                <div class="track-content"></div>
                            </div>
                            <div class="track audio-track" data-track="audio">
                                <div class="track-label">Audio</div>
                                <div class="track-content"></div>
                            </div>
                            <div class="track effects-track" data-track="effects">
                                <div class="track-label">Effects</div>
                                <div class="track-content"></div>
                            </div>
                        </div>
                        <div class="playhead" id="playhead"></div>
                    </div>
                </div>
            </div>
        `;
        
        return editorHTML;
    }

    setupEventListeners() {
        // Playback controls
        document.getElementById('play-pause-btn')?.addEventListener('click', () => this.togglePlayback());
        document.getElementById('stop-btn')?.addEventListener('click', () => this.stopPlayback());
        
        // Effect buttons
        document.querySelectorAll('.effect-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.applyEffect(e.target.dataset.effect));
        });
        
        // Transition buttons
        document.querySelectorAll('.transition-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.addTransition(e.target.dataset.transition));
        });
        
        // Text controls
        document.getElementById('add-text-btn')?.addEventListener('click', () => this.addTextOverlay());
        
        // Timeline controls
        document.getElementById('zoom-in-btn')?.addEventListener('click', () => this.zoomTimeline(1.2));
        document.getElementById('zoom-out-btn')?.addEventListener('click', () => this.zoomTimeline(0.8));
        document.getElementById('split-clip-btn')?.addEventListener('click', () => this.splitClip());
        document.getElementById('delete-clip-btn')?.addEventListener('click', () => this.deleteClip());
    }

    initializeTimeline() {
        this.timeline = document.getElementById('timeline');
        this.canvas = document.getElementById('video-canvas');
        this.ctx = this.canvas?.getContext('2d');
        
        // Setup timeline interaction
        this.timeline?.addEventListener('click', (e) => this.seekToPosition(e));
        this.timeline?.addEventListener('dragover', (e) => e.preventDefault());
        this.timeline?.addEventListener('drop', (e) => this.handleTimelineDrop(e));
    }

    applyEffect(effectType) {
        if (!this.selectedClip) {
            this.showNotification('Please select a clip first', 'warning');
            return;
        }

        const effect = {
            id: Date.now().toString(),
            type: effectType,
            startTime: this.currentTime,
            duration: 2, // Default 2 seconds
            intensity: 1.0,
            clipId: this.selectedClip.id
        };

        this.effects.push(effect);
        this.renderEffectOnTimeline(effect);
        this.showNotification(`${effectType} effect applied`, 'success');
    }

    addTransition(transitionType) {
        const transition = {
            id: Date.now().toString(),
            type: transitionType,
            duration: 1.0, // Default 1 second
            position: this.currentTime
        };

        this.transitions.push(transition);
        this.renderTransitionOnTimeline(transition);
        this.showNotification(`${transitionType} transition added`, 'success');
    }

    addTextOverlay() {
        const text = document.getElementById('text-input')?.value;
        const color = document.getElementById('text-color')?.value;
        const font = document.getElementById('font-family')?.value;

        if (!text) {
            this.showNotification('Please enter text', 'warning');
            return;
        }

        const textOverlay = {
            id: Date.now().toString(),
            type: 'text',
            content: text,
            color: color,
            font: font,
            size: 24,
            position: { x: 50, y: 50 },
            startTime: this.currentTime,
            duration: 3.0
        };

        this.effects.push(textOverlay);
        this.renderTextOnCanvas(textOverlay);
        this.showNotification('Text overlay added', 'success');
    }

    renderTextOnCanvas(textOverlay) {
        if (!this.ctx) return;

        this.ctx.font = `${textOverlay.size}px ${textOverlay.font}`;
        this.ctx.fillStyle = textOverlay.color;
        this.ctx.fillText(textOverlay.content, textOverlay.position.x, textOverlay.position.y);
    }

    splitClip() {
        if (!this.selectedClip) {
            this.showNotification('Please select a clip to split', 'warning');
            return;
        }

        const splitTime = this.currentTime;
        const originalClip = this.selectedClip;
        
        // Create two new clips
        const firstClip = {
            ...originalClip,
            id: Date.now().toString() + '_1',
            duration: splitTime - originalClip.startTime
        };
        
        const secondClip = {
            ...originalClip,
            id: Date.now().toString() + '_2',
            startTime: splitTime,
            duration: originalClip.duration - (splitTime - originalClip.startTime)
        };

        // Remove original clip and add new ones
        this.removeClip(originalClip.id);
        this.addClipToTimeline(firstClip);
        this.addClipToTimeline(secondClip);
        
        this.showNotification('Clip split successfully', 'success');
    }

    exportVideo() {
        this.showNotification('Exporting video...', 'info');
        
        // Simulate export process
        const exportProgress = document.createElement('div');
        exportProgress.className = 'export-progress';
        exportProgress.innerHTML = `
            <div class="progress-bar">
                <div class="progress-fill" style="width: 0%"></div>
            </div>
            <div class="progress-text">Preparing export...</div>
        `;
        
        document.body.appendChild(exportProgress);
        
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 10;
            if (progress >= 100) {
                progress = 100;
                clearInterval(interval);
                setTimeout(() => {
                    exportProgress.remove();
                    this.showNotification('Video exported successfully!', 'success');
                }, 1000);
            }
            
            const fill = exportProgress.querySelector('.progress-fill');
            const text = exportProgress.querySelector('.progress-text');
            fill.style.width = `${progress}%`;
            text.textContent = `Exporting... ${Math.round(progress)}%`;
        }, 200);
    }

    showNotification(message, type) {
        // Use the existing notification system
        if (window.app && window.app.showNotification) {
            window.app.showNotification(message, type);
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VideoEditor;
} else {
    window.VideoEditor = VideoEditor;
}