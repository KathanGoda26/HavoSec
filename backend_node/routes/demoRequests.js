const express = require('express');
const { body, validationResult } = require('express-validator');
const DemoRequest = require('../models/DemoRequest');
const { verifyAdminToken } = require('./adminAuth');
const router = express.Router();

// Get all demo requests (admin)
router.get('/', verifyAdminToken, async (req, res) => {
  try {
    const { status, priority, search } = req.query;
    const query = {};
    if (status) query.status = status;
    if (priority) query.priority = priority;
    if (search) {
      query.$or = [
        { firstName: { $regex: search, $options: 'i' } },
        { lastName: { $regex: search, $options: 'i' } },
        { email: { $regex: search, $options: 'i' } },
        { company: { $regex: search, $options: 'i' } }
      ];
    }
    const requests = await DemoRequest.find(query).sort({ createdAt: -1 });
    const statusCounts = await DemoRequest.aggregate([{ $group: { _id: '$status', count: { $sum: 1 } } }]);
    res.json({ 
      requests, 
      statusCounts: statusCounts.reduce((acc, curr) => { acc[curr._id] = curr.count; return acc; }, {}) 
    });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Get single demo request (admin)
router.get('/:id', verifyAdminToken, async (req, res) => {
  try {
    const request = await DemoRequest.findById(req.params.id);
    if (!request) return res.status(404).json({ message: 'Request not found' });
    res.json({ request });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Update demo request (admin)
router.put('/:id', verifyAdminToken, async (req, res) => {
  try {
    const request = await DemoRequest.findByIdAndUpdate(req.params.id, req.body, { new: true });
    if (!request) return res.status(404).json({ message: 'Request not found' });
    res.json({ message: 'Request updated', request });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Add note (admin)
router.post('/:id/notes', verifyAdminToken, [
  body('content').trim().notEmpty()
], async (req, res) => {
  try {
    const request = await DemoRequest.findByIdAndUpdate(
      req.params.id,
      { $push: { notes: { content: req.body.content, addedBy: req.admin.email, addedAt: new Date() } } },
      { new: true }
    );
    if (!request) return res.status(404).json({ message: 'Request not found' });
    res.json({ message: 'Note added', request });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Delete demo request (admin)
router.delete('/:id', verifyAdminToken, async (req, res) => {
  try {
    await DemoRequest.findByIdAndDelete(req.params.id);
    res.json({ message: 'Request deleted' });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// PUBLIC: Submit demo request
router.post('/public/submit', [
  body('firstName').trim().notEmpty(),
  body('lastName').trim().notEmpty(),
  body('email').isEmail().normalizeEmail(),
  body('company').trim().notEmpty()
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ message: 'Validation failed', errors: errors.array() });
    }
    const demoRequest = new DemoRequest(req.body);
    await demoRequest.save();
    res.status(201).json({ message: 'Demo request submitted successfully' });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

module.exports = router;
