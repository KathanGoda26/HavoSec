const express = require('express');
const jwt = require('jsonwebtoken');
const { body, validationResult } = require('express-validator');
const AdminUser = require('../models/AdminUser');
const router = express.Router();

const ADMIN_JWT_SECRET = process.env.ADMIN_JWT_SECRET || 'havosec-admin-secret';

// Generate JWT Token
const generateToken = (userId) => {
  return jwt.sign({ userId, isAdmin: true }, ADMIN_JWT_SECRET, { expiresIn: '24h' });
};

// Middleware to verify admin token
const verifyAdminToken = async (req, res, next) => {
  try {
    const token = req.header('Authorization')?.replace('Bearer ', '');
    if (!token) {
      return res.status(401).json({ message: 'Access denied. No token provided.' });
    }
    const decoded = jwt.verify(token, ADMIN_JWT_SECRET);
    const admin = await AdminUser.findById(decoded.userId);
    if (!admin || !admin.isActive) {
      return res.status(401).json({ message: 'Invalid token.' });
    }
    req.admin = admin;
    next();
  } catch (error) {
    res.status(401).json({ message: 'Invalid token.' });
  }
};

// Admin Login
router.post('/login', [
  body('email').isEmail().normalizeEmail(),
  body('password').exists()
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ message: 'Validation failed', errors: errors.array() });
    }
    const { email, password } = req.body;
    const admin = await AdminUser.findOne({ email });
    if (!admin) {
      return res.status(401).json({ message: 'Invalid credentials' });
    }
    if (!admin.isActive) {
      return res.status(403).json({ message: 'Account is deactivated' });
    }
    const isPasswordValid = await admin.comparePassword(password);
    if (!isPasswordValid) {
      return res.status(401).json({ message: 'Invalid credentials' });
    }
    admin.lastLogin = new Date();
    await admin.save();
    const token = generateToken(admin._id);
    res.json({
      message: 'Login successful',
      token,
      admin: {
        id: admin._id,
        email: admin.email,
        firstName: admin.firstName,
        lastName: admin.lastName,
        role: admin.role,
        permissions: admin.permissions
      }
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Get current admin profile
router.get('/me', verifyAdminToken, async (req, res) => {
  res.json({
    admin: {
      id: req.admin._id,
      email: req.admin.email,
      firstName: req.admin.firstName,
      lastName: req.admin.lastName,
      role: req.admin.role,
      permissions: req.admin.permissions
    }
  });
});

// Get all admin users (super_admin only)
router.get('/users', verifyAdminToken, async (req, res) => {
  try {
    if (req.admin.role !== 'super_admin') {
      return res.status(403).json({ message: 'Access denied' });
    }
    const admins = await AdminUser.find().select('-password');
    res.json({ admins });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Create admin user (super_admin only)
router.post('/users', verifyAdminToken, [
  body('email').isEmail().normalizeEmail(),
  body('password').isLength({ min: 8 }),
  body('firstName').trim().notEmpty(),
  body('lastName').trim().notEmpty(),
  body('role').isIn(['super_admin', 'admin', 'editor'])
], async (req, res) => {
  try {
    if (req.admin.role !== 'super_admin') {
      return res.status(403).json({ message: 'Access denied' });
    }
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ message: 'Validation failed', errors: errors.array() });
    }
    const { email, password, firstName, lastName, role, permissions } = req.body;
    const existingAdmin = await AdminUser.findOne({ email });
    if (existingAdmin) {
      return res.status(409).json({ message: 'Admin already exists' });
    }
    const admin = new AdminUser({ email, password, firstName, lastName, role, permissions: permissions || ['content', 'blog'] });
    await admin.save();
    res.status(201).json({ message: 'Admin created', admin: { id: admin._id, email, firstName, lastName, role } });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Update admin user
router.put('/users/:id', verifyAdminToken, async (req, res) => {
  try {
    if (req.admin.role !== 'super_admin') {
      return res.status(403).json({ message: 'Access denied' });
    }
    const { firstName, lastName, role, permissions, isActive } = req.body;
    const admin = await AdminUser.findByIdAndUpdate(
      req.params.id,
      { firstName, lastName, role, permissions, isActive },
      { new: true }
    ).select('-password');
    if (!admin) {
      return res.status(404).json({ message: 'Admin not found' });
    }
    res.json({ message: 'Admin updated', admin });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Delete admin user
router.delete('/users/:id', verifyAdminToken, async (req, res) => {
  try {
    if (req.admin.role !== 'super_admin') {
      return res.status(403).json({ message: 'Access denied' });
    }
    if (req.params.id === req.admin._id.toString()) {
      return res.status(400).json({ message: 'Cannot delete yourself' });
    }
    await AdminUser.findByIdAndDelete(req.params.id);
    res.json({ message: 'Admin deleted' });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

module.exports = { router, verifyAdminToken };
