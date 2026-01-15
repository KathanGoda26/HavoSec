const express = require('express');
const WebsiteContent = require('../models/WebsiteContent');
const { verifyAdminToken } = require('./adminAuth');
const router = express.Router();

// Get all content (admin)
router.get('/', verifyAdminToken, async (req, res) => {
  try {
    const content = await WebsiteContent.find();
    res.json({ content });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Get specific section (admin)
router.get('/:section', verifyAdminToken, async (req, res) => {
  try {
    const content = await WebsiteContent.findOne({ section: req.params.section });
    if (!content) {
      return res.status(404).json({ message: 'Content not found' });
    }
    res.json({ content });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Update/create content section (admin)
router.put('/:section', verifyAdminToken, async (req, res) => {
  try {
    const { content, isActive } = req.body;
    const websiteContent = await WebsiteContent.findOneAndUpdate(
      { section: req.params.section },
      { section: req.params.section, content, isActive: isActive !== undefined ? isActive : true, lastUpdatedBy: req.admin._id },
      { new: true, upsert: true }
    );
    res.json({ message: 'Content updated', content: websiteContent });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Delete content section (admin)
router.delete('/:section', verifyAdminToken, async (req, res) => {
  try {
    await WebsiteContent.findOneAndDelete({ section: req.params.section });
    res.json({ message: 'Content deleted' });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// PUBLIC: Get all active content
router.get('/public/all', async (req, res) => {
  try {
    const content = await WebsiteContent.find({ isActive: true });
    const contentMap = {};
    content.forEach(item => { contentMap[item.section] = item.content; });
    res.json({ content: contentMap });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// PUBLIC: Get specific section
router.get('/public/:section', async (req, res) => {
  try {
    const content = await WebsiteContent.findOne({ section: req.params.section, isActive: true });
    if (!content) {
      return res.status(404).json({ message: 'Content not found' });
    }
    res.json({ content: content.content });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

module.exports = router;
