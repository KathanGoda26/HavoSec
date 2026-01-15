const express = require('express');
const { body, validationResult } = require('express-validator');
const BlogPost = require('../models/BlogPost');
const { verifyAdminToken } = require('./adminAuth');
const router = express.Router();

// Get all posts (admin)
router.get('/', verifyAdminToken, async (req, res) => {
  try {
    const { status, category, search } = req.query;
    const query = {};
    if (status) query.status = status;
    if (category) query.category = category;
    if (search) {
      query.$or = [
        { title: { $regex: search, $options: 'i' } },
        { excerpt: { $regex: search, $options: 'i' } }
      ];
    }
    const posts = await BlogPost.find(query).sort({ createdAt: -1 });
    res.json({ posts });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Get single post (admin)
router.get('/:id', verifyAdminToken, async (req, res) => {
  try {
    const post = await BlogPost.findById(req.params.id);
    if (!post) return res.status(404).json({ message: 'Post not found' });
    res.json({ post });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Create post (admin)
router.post('/', verifyAdminToken, [
  body('title').trim().notEmpty(),
  body('excerpt').trim().notEmpty(),
  body('content').trim().notEmpty(),
  body('author.name').trim().notEmpty()
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ message: 'Validation failed', errors: errors.array() });
    }
    const postData = { ...req.body };
    if (postData.status === 'published' && !postData.publishedAt) {
      postData.publishedAt = new Date();
    }
    const post = new BlogPost(postData);
    await post.save();
    res.status(201).json({ message: 'Post created', post });
  } catch (error) {
    if (error.code === 11000) {
      return res.status(409).json({ message: 'Slug already exists' });
    }
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Update post (admin)
router.put('/:id', verifyAdminToken, async (req, res) => {
  try {
    const updateData = { ...req.body };
    if (updateData.status === 'published') {
      const existingPost = await BlogPost.findById(req.params.id);
      if (existingPost && existingPost.status !== 'published') {
        updateData.publishedAt = new Date();
      }
    }
    const post = await BlogPost.findByIdAndUpdate(req.params.id, updateData, { new: true });
    if (!post) return res.status(404).json({ message: 'Post not found' });
    res.json({ message: 'Post updated', post });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Delete post (admin)
router.delete('/:id', verifyAdminToken, async (req, res) => {
  try {
    await BlogPost.findByIdAndDelete(req.params.id);
    res.json({ message: 'Post deleted' });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// PUBLIC: Get published posts
router.get('/public/posts', async (req, res) => {
  try {
    const { category, limit = 10 } = req.query;
    const query = { status: 'published' };
    if (category) query.category = category;
    const posts = await BlogPost.find(query)
      .select('-content')
      .sort({ publishedAt: -1 })
      .limit(parseInt(limit));
    res.json({ posts });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// PUBLIC: Get single published post by slug
router.get('/public/posts/:slug', async (req, res) => {
  try {
    const post = await BlogPost.findOneAndUpdate(
      { slug: req.params.slug, status: 'published' },
      { $inc: { views: 1 } },
      { new: true }
    );
    if (!post) return res.status(404).json({ message: 'Post not found' });
    res.json({ post });
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

module.exports = router;
