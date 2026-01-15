const express = require('express');
const jwt = require('jsonwebtoken');
const SecurityEvent = require('../models/SecurityEvent');
const User = require('../models/User');
const router = express.Router();

const JWT_SECRET = process.env.JWT_SECRET || 'your-super-secret-jwt-key-change-in-production';

// Middleware to verify JWT token
const verifyToken = async (req, res, next) => {
  try {
    const token = req.header('Authorization')?.replace('Bearer ', '');
    if (!token) {
      return res.status(401).json({ message: 'Access denied. No token provided.' });
    }

    const decoded = jwt.verify(token, JWT_SECRET);
    const user = await User.findOne({ id: decoded.userId });
    
    if (!user) {
      return res.status(401).json({ message: 'Invalid token.' });
    }

    req.user = user;
    next();
  } catch (error) {
    res.status(401).json({ message: 'Invalid token.' });
  }
};

// Middleware to check role permissions
const checkRole = (allowedRoles) => {
  return (req, res, next) => {
    if (!allowedRoles.includes(req.user.role)) {
      return res.status(403).json({ message: 'Access denied. Insufficient permissions.' });
    }
    next();
  };
};

// Get dashboard overview statistics
router.get('/overview', verifyToken, async (req, res) => {
  try {
    const now = new Date();
    const last24h = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    const last7d = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    const last30d = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

    // Get attack statistics
    const [
      totalEvents,
      events24h,
      events7d,
      criticalEvents,
      blockedAttacks,
      systemUptime
    ] = await Promise.all([
      SecurityEvent.countDocuments(),
      SecurityEvent.countDocuments({ createdAt: { $gte: last24h } }),
      SecurityEvent.countDocuments({ createdAt: { $gte: last7d } }),
      SecurityEvent.countDocuments({ severity: 'critical', createdAt: { $gte: last7d } }),
      SecurityEvent.countDocuments({ status: 'blocked', createdAt: { $gte: last24h } }),
      // Mock uptime - in real scenario this would come from monitoring service
      Promise.resolve(99.87)
    ]);

    // Calculate trends
    const prevWeekEvents = await SecurityEvent.countDocuments({ 
      createdAt: { $gte: new Date(last7d.getTime() - 7 * 24 * 60 * 60 * 1000), $lt: last7d } 
    });
    const eventsTrend = events7d > prevWeekEvents ? 'increase' : 'decrease';
    const trendsPercentage = prevWeekEvents > 0 ? Math.abs(((events7d - prevWeekEvents) / prevWeekEvents) * 100) : 0;

    res.json({
      overview: {
        totalEvents,
        events24h,
        events7d,
        criticalEvents,
        blockedAttacks,
        systemUptime,
        trends: {
          direction: eventsTrend,
          percentage: Math.round(trendsPercentage * 100) / 100
        }
      },
      lastUpdated: now.toISOString()
    });
  } catch (error) {
    console.error('Dashboard overview error:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Get attack insights with aggregation
router.get('/attack-insights', verifyToken, async (req, res) => {
  try {
    const { period = '7d' } = req.query;
    let startDate;
    
    switch (period) {
      case '24h':
        startDate = new Date(Date.now() - 24 * 60 * 60 * 1000);
        break;
      case '7d':
        startDate = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
        break;
      case '30d':
        startDate = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
        break;
      default:
        startDate = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
    }

    // Aggregate by event type
    const eventsByType = await SecurityEvent.aggregate([
      { $match: { createdAt: { $gte: startDate } } },
      { $group: { _id: '$eventType', count: { $sum: 1 } } },
      { $sort: { count: -1 } }
    ]);

    // Aggregate by severity
    const eventsBySeverity = await SecurityEvent.aggregate([
      { $match: { createdAt: { $gte: startDate } } },
      { $group: { _id: '$severity', count: { $sum: 1 } } },
      { $sort: { count: -1 } }
    ]);

    // Top source IPs
    const topSourceIPs = await SecurityEvent.aggregate([
      { $match: { createdAt: { $gte: startDate }, 'source.ip': { $exists: true } } },
      { $group: { _id: '$source.ip', count: { $sum: 1 } } },
      { $sort: { count: -1 } },
      { $limit: 10 }
    ]);

    // Timeline data for charts (hourly for 24h, daily for others)
    const timelineGrouping = period === '24h' 
      ? { 
          year: { $year: '$createdAt' },
          month: { $month: '$createdAt' },
          day: { $dayOfMonth: '$createdAt' },
          hour: { $hour: '$createdAt' }
        }
      : {
          year: { $year: '$createdAt' },
          month: { $month: '$createdAt' },
          day: { $dayOfMonth: '$createdAt' }
        };

    const timeline = await SecurityEvent.aggregate([
      { $match: { createdAt: { $gte: startDate } } },
      { $group: { _id: timelineGrouping, count: { $sum: 1 } } },
      { $sort: { '_id.year': 1, '_id.month': 1, '_id.day': 1, '_id.hour': 1 } }
    ]);

    res.json({
      attackInsights: {
        eventsByType,
        eventsBySeverity,
        topSourceIPs,
        timeline,
        period
      }
    });
  } catch (error) {
    console.error('Attack insights error:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Get defense metrics
router.get('/defense-metrics', verifyToken, async (req, res) => {
  try {
    const last7d = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
    
    const [
      totalBlocked,
      totalDetected,
      responseTime,
      mitigationRate
    ] = await Promise.all([
      SecurityEvent.countDocuments({ status: 'blocked', createdAt: { $gte: last7d } }),
      SecurityEvent.countDocuments({ createdAt: { $gte: last7d } }),
      // Mock response time - would come from monitoring
      Promise.resolve(0.85),
      SecurityEvent.countDocuments({ status: { $in: ['blocked', 'resolved'] }, createdAt: { $gte: last7d } })
    ]);

    const blockingEfficiency = totalDetected > 0 ? (totalBlocked / totalDetected) * 100 : 0;
    const mitigationEfficiency = totalDetected > 0 ? (mitigationRate / totalDetected) * 100 : 0;

    res.json({
      defenseMetrics: {
        blockingEfficiency: Math.round(blockingEfficiency * 100) / 100,
        mitigationEfficiency: Math.round(mitigationEfficiency * 100) / 100,
        averageResponseTime: responseTime,
        totalBlocked,
        totalDetected,
        securityScore: Math.round((blockingEfficiency + mitigationEfficiency) / 2 * 100) / 100
      }
    });
  } catch (error) {
    console.error('Defense metrics error:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Get activity logs with pagination
router.get('/activity-logs', verifyToken, async (req, res) => {
  try {
    const { page = 1, limit = 50, eventType, severity, startDate, endDate } = req.query;
    
    const query = {};
    if (eventType) query.eventType = eventType;
    if (severity) query.severity = severity;
    if (startDate || endDate) {
      query.createdAt = {};
      if (startDate) query.createdAt.$gte = new Date(startDate);
      if (endDate) query.createdAt.$lte = new Date(endDate);
    }

    const logs = await SecurityEvent.find(query)
      .sort({ createdAt: -1 })
      .limit(limit * 1)
      .skip((page - 1) * limit);

    const totalLogs = await SecurityEvent.countDocuments(query);
    const totalPages = Math.ceil(totalLogs / limit);

    res.json({
      activityLogs: logs,
      pagination: {
        currentPage: parseInt(page),
        totalPages,
        totalLogs,
        hasNextPage: page < totalPages,
        hasPrevPage: page > 1
      }
    });
  } catch (error) {
    console.error('Activity logs error:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Export activity logs (CSV/JSON)
router.get('/export-logs', verifyToken, checkRole(['admin', 'analyst']), async (req, res) => {
  try {
    const { format = 'json', startDate, endDate, eventType, severity } = req.query;
    
    const query = {};
    if (eventType) query.eventType = eventType;
    if (severity) query.severity = severity;
    if (startDate || endDate) {
      query.createdAt = {};
      if (startDate) query.createdAt.$gte = new Date(startDate);
      if (endDate) query.createdAt.$lte = new Date(endDate);
    }

    const logs = await SecurityEvent.find(query).sort({ createdAt: -1 }).limit(10000);

    if (format === 'csv') {
      const csvHeader = 'ID,Event Type,Severity,Source IP,Target,Description,Status,Created At\n';
      const csvData = logs.map(log => 
        `${log.id},"${log.eventType}","${log.severity}","${log.source?.ip || ''}","${log.target?.endpoint || ''}","${log.description}","${log.status}","${log.createdAt}"`
      ).join('\n');
      
      res.setHeader('Content-Type', 'text/csv');
      res.setHeader('Content-Disposition', 'attachment; filename="security-logs.csv"');
      res.send(csvHeader + csvData);
    } else {
      res.setHeader('Content-Type', 'application/json');
      res.setHeader('Content-Disposition', 'attachment; filename="security-logs.json"');
      res.json({ logs, exportedAt: new Date().toISOString() });
    }
  } catch (error) {
    console.error('Export logs error:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

// System health endpoint
router.get('/system-health', verifyToken, async (req, res) => {
  try {
    // Mock system health data - in production this would come from monitoring services
    const healthData = {
      services: [
        { name: 'API Gateway', status: 'healthy', uptime: '99.9%', responseTime: '45ms' },
        { name: 'Database', status: 'healthy', uptime: '99.8%', responseTime: '12ms' },
        { name: 'Authentication', status: 'healthy', uptime: '99.9%', responseTime: '23ms' },
        { name: 'Monitoring', status: 'healthy', uptime: '99.7%', responseTime: '67ms' },
        { name: 'Email Service', status: 'warning', uptime: '98.5%', responseTime: '156ms' }
      ],
      serverStats: {
        cpuUsage: 45.2,
        memoryUsage: 67.8,
        diskUsage: 34.1,
        networkLatency: 12.5
      },
      alerts: [
        { type: 'warning', message: 'High memory usage detected on server-02', timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000) },
        { type: 'info', message: 'Scheduled maintenance completed successfully', timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000) }
      ],
      lastCheck: new Date().toISOString()
    };

    res.json({ systemHealth: healthData });
  } catch (error) {
    console.error('System health error:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

module.exports = router;