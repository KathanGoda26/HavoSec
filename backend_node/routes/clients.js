const express = require('express');
const { body, validationResult } = require('express-validator');
const ClientCompany = require('../models/ClientCompany');
const { verifyAdminToken } = require('./adminAuth');
const router = express.Router();

// Get all clients (admin)
router.get('/', verifyAdminToken, async (req, res) => {
  try {
    const { status, plan, industry, search } = req.query;
    const query = {};
    if (status) query['subscription.status'] = status;
    if (plan) query['subscription.plan'] = plan;
    if (industry) query.industry = industry;
    if (search) {
      query.$or = [
        { name: { $regex: search, $options: 'i' } },
        { email: { $regex: search, $options: 'i' } }
      ];
    }
    const clients = await ClientCompany.find(query).sort({ createdAt: -1 });
    res.json({ clients });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Get single client (admin)
router.get('/:id', verifyAdminToken, async (req, res) => {
  try {
    const client = await ClientCompany.findById(req.params.id);
    if (!client) return res.status(404).json({ message: 'Client not found' });
    res.json({ client });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Create client (admin)
router.post('/', verifyAdminToken, [
  body('name').trim().notEmpty(),
  body('email').isEmail().normalizeEmail()
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ message: 'Validation failed', errors: errors.array() });
    }
    const existingClient = await ClientCompany.findOne({ email: req.body.email });
    if (existingClient) {
      return res.status(409).json({ message: 'Client already exists' });
    }
    const client = new ClientCompany(req.body);
    await client.save();
    res.status(201).json({ message: 'Client created', client });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Update client (admin)
router.put('/:id', verifyAdminToken, async (req, res) => {
  try {
    const client = await ClientCompany.findByIdAndUpdate(req.params.id, req.body, { new: true });
    if (!client) return res.status(404).json({ message: 'Client not found' });
    res.json({ message: 'Client updated', client });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Delete client (admin)
router.delete('/:id', verifyAdminToken, async (req, res) => {
  try {
    await ClientCompany.findByIdAndDelete(req.params.id);
    res.json({ message: 'Client deleted' });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Get stats (admin)
router.get('/stats/overview', verifyAdminToken, async (req, res) => {
  try {
    const [total, active, byPlan, byIndustry] = await Promise.all([
      ClientCompany.countDocuments(),
      ClientCompany.countDocuments({ isActive: true, 'subscription.status': 'active' }),
      ClientCompany.aggregate([{ $group: { _id: '$subscription.plan', count: { $sum: 1 } } }]),
      ClientCompany.aggregate([{ $group: { _id: '$industry', count: { $sum: 1 } } }])
    ]);
    res.json({
      stats: {
        total, active,
        byPlan: byPlan.reduce((acc, curr) => { acc[curr._id || 'none'] = curr.count; return acc; }, {}),
        byIndustry: byIndustry.reduce((acc, curr) => { acc[curr._id || 'none'] = curr.count; return acc; }, {})
      }
    });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

module.exports = router;
