class CollaborationHub {
    constructor() {
        this.activeCollaborations = new Map();
        this.sharedProjects = [];
        this.comments = [];
        this.realTimeUsers = new Set();
        this.currentUser = this.getCurrentUser();
        
        this.init();
    }

    init() {
        this.createCollaborationInterface();
        this.setupEventListeners();
        this.initializeRealTimeSync();
    }

    createCollaborationInterface() {
        const collaborationHTML = `
            <div class="collaboration-hub">
                <div class="collaboration-header">
                    <h3><i class="fas fa-users"></i> Collaboration Hub</h3>
                    <div class="collaboration-controls">
                        <button class="btn btn-primary" id="share-project-btn">
                            <i class="fas fa-share-alt"></i> Share Project
                        </button>
                        <button class="btn btn-secondary" id="invite-collaborator-btn">
                            <i class="fas fa-user-plus"></i> Invite
                        </button>
                    </div>
                </div>
                
                <div class="collaboration-content">
                    <div class="active-collaborators">
                        <h4>Active Collaborators</h4>
                        <div class="collaborators-list" id="collaborators-list">
                            <!-- Active users will appear here -->
                        </div>
                    </div>
                    
                    <div class="shared-projects">
                        <h4>Shared Projects</h4>
                        <div class="projects-list" id="shared-projects-list">
                            <!-- Shared projects will appear here -->
                        </div>
                    </div>
                    
                    <div class="collaboration-feed">
                        <h4>Activity Feed</h4>
                        <div class="feed-content" id="collaboration-feed">
                            <!-- Real-time activity feed -->
                        </div>
                    </div>
                    
                    <div class="comments-section">
                        <h4>Comments & Feedback</h4>
                        <div class="comments-list" id="comments-list">
                            <!-- Comments will appear here -->
                        </div>
                        <div class="comment-input">
                            <textarea id="comment-text" placeholder="Add a comment or feedback..."></textarea>
                            <button id="post-comment-btn" class="btn btn-primary">
                                <i class="fas fa-comment"></i> Post
                            </button>
                        </div>
                    </div>
                </div>
                
                <!-- Version Control Panel -->
                <div class="version-control">
                    <h4><i class="fas fa-code-branch"></i> Version Control</h4>
                    <div class="version-timeline" id="version-timeline">
                        <!-- Version history will appear here -->
                    </div>
                    <div class="version-actions">
                        <button class="btn btn-secondary" id="create-branch-btn">
                            <i class="fas fa-code-branch"></i> Create Branch
                        </button>
                        <button class="btn btn-warning" id="merge-changes-btn">
                            <i class="fas fa-compress-arrows-alt"></i> Merge Changes
                        </button>
                    </div>
                </div>
                
                <!-- Real-time Chat -->
                <div class="collaboration-chat">
                    <div class="chat-header">
                        <h4><i class="fas fa-comments"></i> Team Chat</h4>
                        <button class="chat-toggle" id="chat-toggle">
                            <i class="fas fa-chevron-up"></i>
                        </button>
                    </div>
                    <div class="chat-content" id="chat-content">
                        <div class="chat-messages" id="chat-messages">
                            <!-- Chat messages will appear here -->
                        </div>
                        <div class="chat-input">
                            <input type="text" id="chat-input" placeholder="Type a message...">
                            <button id="send-chat-btn">
                                <i class="fas fa-paper-plane"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        return collaborationHTML;
    }

    setupEventListeners() {
        // Share project
        document.getElementById('share-project-btn')?.addEventListener('click', () => this.shareProject());
        
        // Invite collaborator
        document.getElementById('invite-collaborator-btn')?.addEventListener('click', () => this.inviteCollaborator());
        
        // Comments
        document.getElementById('post-comment-btn')?.addEventListener('click', () => this.postComment());
        
        // Version control
        document.getElementById('create-branch-btn')?.addEventListener('click', () => this.createBranch());
        document.getElementById('merge-changes-btn')?.addEventListener('click', () => this.mergeChanges());
        
        // Chat
        document.getElementById('send-chat-btn')?.addEventListener('click', () => this.sendChatMessage());
        document.getElementById('chat-input')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendChatMessage();
        });
        document.getElementById('chat-toggle')?.addEventListener('click', () => this.toggleChat());
    }

    initializeRealTimeSync() {
        // Simulate real-time collaboration
        this.syncInterval = setInterval(() => {
            this.syncCollaborationData();
        }, 5000);
        
        // Add current user to active collaborators
        this.addActiveCollaborator(this.currentUser);
    }

    shareProject() {
        const modal = this.createShareModal();
        document.body.appendChild(modal);
    }

    createShareModal() {
        const modal = document.createElement('div');
        modal.className = 'modal active';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Share Project</h3>
                    <button class="modal-close" onclick="this.closest('.modal').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label>Project to Share</label>
                        <select id="project-to-share" class="form-control">
                            <option value="">Select a project...</option>
                            <!-- Projects will be populated here -->
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Share with (email addresses)</label>
                        <textarea id="collaborator-emails" class="form-control" 
                                placeholder="Enter email addresses separated by commas"></textarea>
                    </div>
                    <div class="form-group">
                        <label>Permission Level</label>
                        <select id="permission-level" class="form-control">
                            <option value="view">View Only</option>
                            <option value="comment">Can Comment</option>
                            <option value="edit">Can Edit</option>
                            <option value="admin">Admin</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Share Message</label>
                        <textarea id="share-message" class="form-control" 
                                placeholder="Optional message to collaborators"></textarea>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">Cancel</button>
                    <button class="btn btn-primary" onclick="collaborationHub.processProjectShare()">Share Project</button>
                </div>
            </div>
        `;
        
        return modal;
    }

    processProjectShare() {
        const projectId = document.getElementById('project-to-share')?.value;
        const emails = document.getElementById('collaborator-emails')?.value;
        const permission = document.getElementById('permission-level')?.value;
        const message = document.getElementById('share-message')?.value;
        
        if (!projectId || !emails) {
            this.showNotification('Please select a project and enter email addresses', 'error');
            return;
        }
        
        const sharedProject = {
            id: Date.now().toString(),
            projectId: projectId,
            collaborators: emails.split(',').map(email => email.trim()),
            permission: permission,
            message: message,
            sharedAt: new Date().toISOString(),
            sharedBy: this.currentUser.name
        };
        
        this.sharedProjects.push(sharedProject);
        this.updateSharedProjectsList();
        this.addToActivityFeed(`Project shared with ${sharedProject.collaborators.length} collaborators`);
        
        document.querySelector('.modal').remove();
        this.showNotification('Project shared successfully!', 'success');
    }

    inviteCollaborator() {
        const email = prompt('Enter collaborator email:');
        if (email) {
            this.sendInvitation(email);
        }
    }

    sendInvitation(email) {
        const invitation = {
            id: Date.now().toString(),
            email: email,
            invitedBy: this.currentUser.name,
            invitedAt: new Date().toISOString(),
            status: 'pending'
        };
        
        // Simulate sending invitation
        setTimeout(() => {
            this.addToActivityFeed(`Invitation sent to ${email}`);
            this.showNotification(`Invitation sent to ${email}`, 'success');
        }, 1000);
    }

    postComment() {
        const commentText = document.getElementById('comment-text')?.value;
        if (!commentText.trim()) return;
        
        const comment = {
            id: Date.now().toString(),
            text: commentText,
            author: this.currentUser.name,
            timestamp: new Date().toISOString(),
            replies: []
        };
        
        this.comments.push(comment);
        this.updateCommentsList();
        this.addToActivityFeed(`${this.currentUser.name} added a comment`);
        
        document.getElementById('comment-text').value = '';
    }

    updateCommentsList() {
        const commentsList = document.getElementById('comments-list');
        if (!commentsList) return;
        
        commentsList.innerHTML = this.comments.map(comment => `
            <div class="comment-item">
                <div class="comment-header">
                    <strong>${comment.author}</strong>
                    <span class="comment-time">${new Date(comment.timestamp).toLocaleString()}</span>
                </div>
                <div class="comment-text">${comment.text}</div>
                <div class="comment-actions">
                    <button class="btn btn-sm btn-secondary" onclick="collaborationHub.replyToComment('${comment.id}')">
                        <i class="fas fa-reply"></i> Reply
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="collaborationHub.likeComment('${comment.id}')">
                        <i class="fas fa-thumbs-up"></i> Like
                    </button>
                </div>
            </div>
        `).join('');
    }

    createBranch() {
        const branchName = prompt('Enter branch name:');
        if (!branchName) return;
        
        const branch = {
            id: Date.now().toString(),
            name: branchName,
            createdBy: this.currentUser.name,
            createdAt: new Date().toISOString(),
            commits: []
        };
        
        this.addToVersionTimeline(branch);
        this.addToActivityFeed(`Created branch: ${branchName}`);
        this.showNotification(`Branch "${branchName}" created`, 'success');
    }

    mergeChanges() {
        // Simulate merge process
        this.showNotification('Merging changes...', 'info');
        
        setTimeout(() => {
            this.addToActivityFeed('Changes merged successfully');
            this.showNotification('Changes merged successfully!', 'success');
        }, 2000);
    }

    sendChatMessage() {
        const chatInput = document.getElementById('chat-input');
        const message = chatInput?.value.trim();
        
        if (!message) return;
        
        const chatMessage = {
            id: Date.now().toString(),
            text: message,
            sender: this.currentUser.name,
            timestamp: new Date().toISOString()
        };
        
        this.addChatMessage(chatMessage);
        chatInput.value = '';
        
        // Simulate receiving responses from other collaborators
        setTimeout(() => {
            this.simulateCollaboratorResponse(message);
        }, 2000 + Math.random() * 3000);
    }

    addChatMessage(message) {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) return;
        
        const messageElement = document.createElement('div');
        messageElement.className = `chat-message ${message.sender === this.currentUser.name ? 'own-message' : 'other-message'}`;
        messageElement.innerHTML = `
            <div class="message-sender">${message.sender}</div>
            <div class="message-text">${message.text}</div>
            <div class="message-time">${new Date(message.timestamp).toLocaleTimeString()}</div>
        `;
        
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    simulateCollaboratorResponse(originalMessage) {
        const responses = [
            "Great idea! Let's implement that.",
            "I like the direction this is going.",
            "What do you think about adjusting the lighting?",
            "The latest version looks amazing!",
            "Should we try a different approach?",
            "Perfect! That's exactly what we needed."
        ];
        
        const collaborators = ['Alice', 'Bob', 'Charlie', 'Diana'];
        const randomCollaborator = collaborators[Math.floor(Math.random() * collaborators.length)];
        const randomResponse = responses[Math.floor(Math.random() * responses.length)];
        
        const response = {
            id: Date.now().toString(),
            text: randomResponse,
            sender: randomCollaborator,
            timestamp: new Date().toISOString()
        };
        
        this.addChatMessage(response);
    }

    toggleChat() {
        const chatContent = document.getElementById('chat-content');
        const chatToggle = document.getElementById('chat-toggle');
        
        if (chatContent.style.display === 'none') {
            chatContent.style.display = 'block';
            chatToggle.innerHTML = '<i class="fas fa-chevron-up"></i>';
        } else {
            chatContent.style.display = 'none';
            chatToggle.innerHTML = '<i class="fas fa-chevron-down"></i>';
        }
    }

    addActiveCollaborator(user) {
        this.realTimeUsers.add(user);
        this.updateCollaboratorsList();
    }

    updateCollaboratorsList() {
        const collaboratorsList = document.getElementById('collaborators-list');
        if (!collaboratorsList) return;
        
        const users = Array.from(this.realTimeUsers);
        collaboratorsList.innerHTML = users.map(user => `
            <div class="collaborator-item">
                <div class="collaborator-avatar">
                    <i class="fas fa-user"></i>
                </div>
                <div class="collaborator-info">
                    <div class="collaborator-name">${user.name}</div>
                    <div class="collaborator-status online">Online</div>
                </div>
            </div>
        `).join('');
    }

    addToActivityFeed(activity) {
        const feed = document.getElementById('collaboration-feed');
        if (!feed) return;
        
        const activityElement = document.createElement('div');
        activityElement.className = 'activity-item';
        activityElement.innerHTML = `
            <div class="activity-icon">
                <i class="fas fa-circle"></i>
            </div>
            <div class="activity-content">
                <div class="activity-text">${activity}</div>
                <div class="activity-time">${new Date().toLocaleTimeString()}</div>
            </div>
        `;
        
        feed.insertBefore(activityElement, feed.firstChild);
        
        // Keep only the latest 10 activities
        while (feed.children.length > 10) {
            feed.removeChild(feed.lastChild);
        }
    }

    addToVersionTimeline(branch) {
        const timeline = document.getElementById('version-timeline');
        if (!timeline) return;
        
        const versionElement = document.createElement('div');
        versionElement.className = 'version-item';
        versionElement.innerHTML = `
            <div class="version-marker"></div>
            <div class="version-content">
                <div class="version-title">Branch: ${branch.name}</div>
                <div class="version-author">by ${branch.createdBy}</div>
                <div class="version-time">${new Date(branch.createdAt).toLocaleString()}</div>
            </div>
        `;
        
        timeline.insertBefore(versionElement, timeline.firstChild);
    }

    syncCollaborationData() {
        // Simulate real-time data synchronization
        if (Math.random() < 0.3) {
            const activities = [
                'New video generated',
                'Project settings updated',
                'Template saved',
                'Comment added',
                'File uploaded'
            ];
            
            const randomActivity = activities[Math.floor(Math.random() * activities.length)];
            this.addToActivityFeed(randomActivity);
        }
    }

    getCurrentUser() {
        return {
            id: 'user_' + Date.now(),
            name: 'You',
            email: 'user@example.com',
            role: 'creator'
        };
    }

    showNotification(message, type) {
        if (window.app && window.app.showNotification) {
            window.app.showNotification(message, type);
        }
    }

    destroy() {
        if (this.syncInterval) {
            clearInterval(this.syncInterval);
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CollaborationHub;
} else {
    window.CollaborationHub = CollaborationHub;
}