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

const authRoutes = require('./routes/auth');
const dashboardRoutes = require('./routes/dashboard');
const publicRoutes = require('./routes/public');
const { seedDatabase } = require('./middleware/seedData');

const app = express();
const PORT = process.env.PORT || 8001;

// Security Middleware
app.use(helmet());
app.use(mongoSanitize());
app.use(hpp());
app.use(compression());

// CORS Configuration
app.use(cors({
  origin: process.env.CORS_ORIGINS ? process.env.CORS_ORIGINS.split(',').map(url => url.trim()) : ['http://localhost:3000'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

// Rate Limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.',
  standardHeaders: true,
  legacyHeaders: false,
});
app.use(limiter);

// Stricter rate limiting for auth routes
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 50, // limit each IP to 5 auth requests per windowMs
  message: 'Too many authentication attempts, please try again later.',
});

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Logging
app.use(morgan('combined'));

// MongoDB Connection
const MONGO_URL = process.env.MONGO_URL || 'mongodb://127.0.0.1:27017/lockshield';
mongoose.connect(MONGO_URL, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
})
.then(() => {
  console.log('MongoDB Connected Successfully');
  // Seed database with mock data (only in non-production)
  if (process.env.NODE_ENV !== 'production') {
    seedDatabase();
  }
})
.catch(err => console.error('MongoDB Connection Error:', err));

// Routes
app.use('/api', publicRoutes);
app.use('/api/auth', authLimiter, authRoutes);
app.use('/api/dashboard', dashboardRoutes);

// Health Check
app.get('/api/health', (req, res) => {
  res.json({
    status: 'OK',
    timestamp: new Date().toISOString(),
    service: 'LockShield Analytics API'
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({
    message: 'Something went wrong!',
    error: process.env.NODE_ENV === 'production' ? {} : err.message
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({ message: 'Route not found' });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Backend running on port ${PORT}`);
  // console.log(`🌍 Environment: ${process.env.NODE_ENV || 'development'}`);
});