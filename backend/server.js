const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const mongoSanitize = require('express-mongo-sanitize');
const hpp = require('hpp');
const compression = require('compression');
const morgan = require('morgan');
require('dotenv').config();

// Import routes
const { router: adminAuthRoutes } = require('./routes/adminAuth');
const contentRoutes = require('./routes/content');
const blogRoutes = require('./routes/blog');
const demoRequestsRoutes = require('./routes/demoRequests');
const clientsRoutes = require('./routes/clients');

// Import seed data
const { seedDatabase } = require('./seed');

const app = express();
const PORT = process.env.PORT || 8001;

// Security Middleware
app.use(helmet());
app.use(mongoSanitize());
app.use(hpp());
app.use(compression());

// CORS - Allow admin and website
app.use(cors({
  origin: ['http://localhost:3000', 'http://localhost:3001'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

// Rate Limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 200,
  message: 'Too many requests'
});
app.use(limiter);

// Body parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Logging
app.use(morgan('dev'));

// MongoDB Connection
const MONGO_URL = process.env.MONGO_URL || 'mongodb://127.0.0.1:27017/havosec';
mongoose.connect(MONGO_URL)
.then(() => {
  console.log('\x1b[32m%s\x1b[0m', '✓ MongoDB Connected');
  seedDatabase();
})
.catch(err => console.error('MongoDB Error:', err));

// API Routes
app.use('/api/admin/auth', adminAuthRoutes);
app.use('/api/admin/content', contentRoutes);
app.use('/api/admin/blog', blogRoutes);
app.use('/api/admin/demo-requests', demoRequestsRoutes);
app.use('/api/admin/clients', clientsRoutes);

// Public routes
app.use('/api/content', contentRoutes);
app.use('/api/blog', blogRoutes);
app.use('/api/demo', demoRequestsRoutes);

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'OK', service: 'HavoSec API', timestamp: new Date().toISOString() });
});

// Dashboard stats (admin)
app.get('/api/admin/dashboard', async (req, res) => {
  try {
    const BlogPost = require('./models/BlogPost');
    const DemoRequest = require('./models/DemoRequest');
    const ClientCompany = require('./models/ClientCompany');
    
    const [totalPosts, publishedPosts, totalDemos, newDemos, totalClients, activeClients] = await Promise.all([
      BlogPost.countDocuments(),
      BlogPost.countDocuments({ status: 'published' }),
      DemoRequest.countDocuments(),
      DemoRequest.countDocuments({ status: 'new' }),
      ClientCompany.countDocuments(),
      ClientCompany.countDocuments({ isActive: true })
    ]);
    
    res.json({
      overview: {
        blog: { total: totalPosts, published: publishedPosts },
        demoRequests: { total: totalDemos, pending: newDemos },
        clients: { total: totalClients, active: activeClients }
      }
    });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Error handling
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ message: 'Something went wrong!' });
});

// 404
app.use('*', (req, res) => {
  res.status(404).json({ message: 'Route not found' });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log('\x1b[36m%s\x1b[0m', `✓ HavoSec Backend running on port ${PORT}`);
});
