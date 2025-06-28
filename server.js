const express = require('express');
const multer = require('multer');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const { v4: uuidv4 } = require('uuid');
const WebSocket = require('ws');
const http = require('http');
const cron = require('node-cron');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// Middleware
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.static('public'));
app.use('/outputs', express.static('outputs'));
app.use('/uploads', express.static('uploads'));

// Ensure directories exist
const dirs = ['uploads', 'outputs', 'temp', 'projects'];
dirs.forEach(dir => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
});

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, 'uploads/');
  },
  filename: (req, file, cb) => {
    const uniqueName = `${Date.now()}-${uuidv4()}${path.extname(file.originalname)}`;
    cb(null, uniqueName);
  }
});

const upload = multer({ 
  storage,
  limits: { fileSize: 100 * 1024 * 1024 }, // 100MB limit
  fileFilter: (req, file, cb) => {
    const allowedTypes = /jpeg|jpg|png|gif|mp4|mov|avi|webm/;
    const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());
    const mimetype = allowedTypes.test(file.mimetype);
    
    if (mimetype && extname) {
      return cb(null, true);
    } else {
      cb(new Error('Invalid file type'));
    }
  }
});

// WebSocket connections for real-time updates
const clients = new Set();

wss.on('connection', (ws) => {
  clients.add(ws);
  console.log('Client connected');
  
  ws.on('close', () => {
    clients.delete(ws);
    console.log('Client disconnected');
  });
});

// Broadcast to all connected clients
function broadcast(data) {
  clients.forEach(client => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(JSON.stringify(data));
    }
  });
}

// In-memory storage for projects and generation history
let projects = [];
let generationHistory = [];
let templates = [];

// Load existing data
try {
  if (fs.existsSync('data/projects.json')) {
    projects = JSON.parse(fs.readFileSync('data/projects.json', 'utf8'));
  }
  if (fs.existsSync('data/history.json')) {
    generationHistory = JSON.parse(fs.readFileSync('data/history.json', 'utf8'));
  }
  if (fs.existsSync('data/templates.json')) {
    templates = JSON.parse(fs.readFileSync('data/templates.json', 'utf8'));
  }
} catch (error) {
  console.log('No existing data found, starting fresh');
}

// Save data function
function saveData() {
  if (!fs.existsSync('data')) {
    fs.mkdirSync('data');
  }
  fs.writeFileSync('data/projects.json', JSON.stringify(projects, null, 2));
  fs.writeFileSync('data/history.json', JSON.stringify(generationHistory, null, 2));
  fs.writeFileSync('data/templates.json', JSON.stringify(templates, null, 2));
}

// API Routes

// Upload file endpoint
app.post('/api/upload', upload.single('file'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file uploaded' });
  }
  
  res.json({
    filename: req.file.filename,
    originalName: req.file.originalname,
    size: req.file.size,
    path: `/uploads/${req.file.filename}`
  });
});

// Batch upload endpoint
app.post('/api/upload-batch', upload.array('files', 10), (req, res) => {
  if (!req.files || req.files.length === 0) {
    return res.status(400).json({ error: 'No files uploaded' });
  }
  
  const files = req.files.map(file => ({
    filename: file.filename,
    originalName: file.originalname,
    size: file.size,
    path: `/uploads/${file.filename}`
  }));
  
  res.json({ files });
});

// Project management endpoints
app.get('/api/projects', (req, res) => {
  res.json(projects);
});

app.post('/api/projects', (req, res) => {
  const project = {
    id: uuidv4(),
    name: req.body.name,
    description: req.body.description || '',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    videos: [],
    settings: req.body.settings || {}
  };
  
  projects.push(project);
  saveData();
  
  broadcast({ type: 'project_created', project });
  res.json(project);
});

app.put('/api/projects/:id', (req, res) => {
  const projectIndex = projects.findIndex(p => p.id === req.params.id);
  if (projectIndex === -1) {
    return res.status(404).json({ error: 'Project not found' });
  }
  
  projects[projectIndex] = {
    ...projects[projectIndex],
    ...req.body,
    updatedAt: new Date().toISOString()
  };
  
  saveData();
  broadcast({ type: 'project_updated', project: projects[projectIndex] });
  res.json(projects[projectIndex]);
});

app.delete('/api/projects/:id', (req, res) => {
  const projectIndex = projects.findIndex(p => p.id === req.params.id);
  if (projectIndex === -1) {
    return res.status(404).json({ error: 'Project not found' });
  }
  
  projects.splice(projectIndex, 1);
  saveData();
  
  broadcast({ type: 'project_deleted', projectId: req.params.id });
  res.json({ success: true });
});

// Generation history endpoints
app.get('/api/history', (req, res) => {
  const page = parseInt(req.query.page) || 1;
  const limit = parseInt(req.query.limit) || 20;
  const startIndex = (page - 1) * limit;
  const endIndex = startIndex + limit;
  
  const paginatedHistory = generationHistory
    .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    .slice(startIndex, endIndex);
  
  res.json({
    history: paginatedHistory,
    total: generationHistory.length,
    page,
    totalPages: Math.ceil(generationHistory.length / limit)
  });
});

app.post('/api/history', (req, res) => {
  const historyItem = {
    id: uuidv4(),
    ...req.body,
    createdAt: new Date().toISOString()
  };
  
  generationHistory.push(historyItem);
  saveData();
  
  broadcast({ type: 'history_added', item: historyItem });
  res.json(historyItem);
});

// Template management endpoints
app.get('/api/templates', (req, res) => {
  res.json(templates);
});

app.post('/api/templates', (req, res) => {
  const template = {
    id: uuidv4(),
    name: req.body.name,
    description: req.body.description || '',
    prompt: req.body.prompt,
    settings: req.body.settings || {},
    category: req.body.category || 'custom',
    createdAt: new Date().toISOString(),
    isPublic: req.body.isPublic || false
  };
  
  templates.push(template);
  saveData();
  
  broadcast({ type: 'template_created', template });
  res.json(template);
});

app.delete('/api/templates/:id', (req, res) => {
  const templateIndex = templates.findIndex(t => t.id === req.params.id);
  if (templateIndex === -1) {
    return res.status(404).json({ error: 'Template not found' });
  }
  
  templates.splice(templateIndex, 1);
  saveData();
  
  broadcast({ type: 'template_deleted', templateId: req.params.id });
  res.json({ success: true });
});

// Video processing endpoints
app.post('/api/process-video', upload.single('video'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No video file uploaded' });
  }
  
  // Simulate video processing
  const processedVideo = {
    id: uuidv4(),
    originalPath: req.file.path,
    processedPath: `/outputs/processed_${req.file.filename}`,
    status: 'processing',
    createdAt: new Date().toISOString()
  };
  
  // Simulate processing time
  setTimeout(() => {
    processedVideo.status = 'completed';
    broadcast({ type: 'video_processed', video: processedVideo });
  }, 3000);
  
  res.json(processedVideo);
});

// Analytics endpoint
app.get('/api/analytics', (req, res) => {
  const totalGenerations = generationHistory.length;
  const totalProjects = projects.length;
  const totalTemplates = templates.length;
  
  const generationsByModel = generationHistory.reduce((acc, item) => {
    const model = item.model || 'unknown';
    acc[model] = (acc[model] || 0) + 1;
    return acc;
  }, {});
  
  const recentActivity = generationHistory
    .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    .slice(0, 10);
  
  res.json({
    totalGenerations,
    totalProjects,
    totalTemplates,
    generationsByModel,
    recentActivity
  });
});

// Cleanup old files (runs daily at midnight)
cron.schedule('0 0 * * *', () => {
  console.log('Running cleanup task...');
  
  const tempDir = 'temp';
  const maxAge = 24 * 60 * 60 * 1000; // 24 hours
  
  if (fs.existsSync(tempDir)) {
    const files = fs.readdirSync(tempDir);
    files.forEach(file => {
      const filePath = path.join(tempDir, file);
      const stats = fs.statSync(filePath);
      
      if (Date.now() - stats.mtime.getTime() > maxAge) {
        fs.unlinkSync(filePath);
        console.log(`Deleted old temp file: ${file}`);
      }
    });
  }
});

// Error handling middleware
app.use((error, req, res, next) => {
  console.error('Error:', error);
  res.status(500).json({ error: error.message });
});

// Serve the main application
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log(`Open http://localhost:${PORT} to view the application`);
});