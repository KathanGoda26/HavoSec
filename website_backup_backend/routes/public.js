const express = require('express');
const { body, validationResult } = require('express-validator');
const { sendEmail } = require('../utils/email');
const router = express.Router();

// Home page - basic info
router.get('/', (req, res) => {
  res.json({
    message: 'Welcome to LockShield Analytics API',
    service: 'Cybersecurity Defense Platform',
    version: '1.0.0',
    features: [
      'Real-time threat detection',
      'Advanced analytics dashboard',
      'Automated incident response',
      'Comprehensive security monitoring'
    ]
  });
});

// Book a demo endpoint
router.post('/book-demo', [
  body('firstName').trim().isLength({ min: 1 }).withMessage('First name is required'),
  body('lastName').trim().isLength({ min: 1 }).withMessage('Last name is required'),
  body('email').isEmail().normalizeEmail().withMessage('Valid email is required'),
  body('company').trim().isLength({ min: 1 }).withMessage('Company is required'),
  body('phone').optional().isMobilePhone().withMessage('Valid phone number required'),
  body('message').optional().trim(),
  body('preferredDate').optional().isISO8601().withMessage('Valid date required'),
  body('companySize').optional().isIn(['1-10', '11-50', '51-200', '201-1000', '1000+'])
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        message: 'Validation failed',
        errors: errors.array()
      });
    }

    const { firstName, lastName, email, company, phone, message, preferredDate, companySize } = req.body;

    // Send demo request email to company
    try {
      await sendEmail({
        to: process.env.DEMO_EMAIL || 'demo@lockshield.com',
        subject: `New Demo Request from ${firstName} ${lastName} at ${company}`,
        html: `
          <h2>New Demo Request</h2>
          <p><strong>Name:</strong> ${firstName} ${lastName}</p>
          <p><strong>Email:</strong> ${email}</p>
          <p><strong>Company:</strong> ${company}</p>
          ${phone ? `<p><strong>Phone:</strong> ${phone}</p>` : ''}
          ${companySize ? `<p><strong>Company Size:</strong> ${companySize}</p>` : ''}
          ${preferredDate ? `<p><strong>Preferred Date:</strong> ${new Date(preferredDate).toLocaleDateString()}</p>` : ''}
          ${message ? `<p><strong>Message:</strong> ${message}</p>` : ''}
          <p><strong>Submitted:</strong> ${new Date().toLocaleString()}</p>
        `
      });

      // Send confirmation email to user
      await sendEmail({
        to: email,
        subject: 'Demo Request Received - LockShield Analytics',
        html: `
          <h2>Thank you for your interest in LockShield Analytics!</h2>
          <p>Hi ${firstName},</p>
          <p>We've received your demo request and our team will contact you within 24 hours to schedule your personalized demonstration.</p>
          <p>In the meantime, feel free to explore our website to learn more about our cybersecurity solutions.</p>
          <p>Best regards,<br>The LockShield Team</p>
        `
      });
    } catch (emailError) {
      console.error('Email sending failed:', emailError);
      // Continue with success response even if email fails
    }

    res.json({
      message: 'Demo request submitted successfully',
      status: 'received',
      contactInfo: {
        firstName,
        lastName,
        email,
        company
      }
    });
  } catch (error) {
    console.error('Book demo error:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Contact form endpoint
router.post('/contact', [
  body('name').trim().isLength({ min: 1 }).withMessage('Name is required'),
  body('email').isEmail().normalizeEmail().withMessage('Valid email is required'),
  body('subject').trim().isLength({ min: 1 }).withMessage('Subject is required'),
  body('message').trim().isLength({ min: 10 }).withMessage('Message must be at least 10 characters')
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        message: 'Validation failed',
        errors: errors.array()
      });
    }

    const { name, email, subject, message } = req.body;

    try {
      await sendEmail({
        to: process.env.CONTACT_EMAIL || 'contact@lockshield.com',
        subject: `Contact Form: ${subject}`,
        html: `
          <h2>New Contact Form Submission</h2>
          <p><strong>Name:</strong> ${name}</p>
          <p><strong>Email:</strong> ${email}</p>
          <p><strong>Subject:</strong> ${subject}</p>
          <p><strong>Message:</strong></p>
          <p>${message.replace(/\n/g, '<br>')}</p>
          <p><strong>Submitted:</strong> ${new Date().toLocaleString()}</p>
        `
      });
    } catch (emailError) {
      console.error('Contact email failed:', emailError);
    }

    res.json({
      message: 'Message sent successfully',
      status: 'received'
    });
  } catch (error) {
    console.error('Contact form error:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Blog posts endpoint (mock data for now)
router.get('/blog', (req, res) => {
  const { limit = 10, offset = 0 } = req.query;
  
  const mockPosts = [
    {
      id: '1',
      title: 'Advanced Threat Detection: AI-Powered Security',
      excerpt: 'Learn how artificial intelligence is revolutionizing cybersecurity threat detection and response.',
      author: 'Sarah Chen',
      publishedDate: '2024-01-15',
      readTime: '5 min read',
      tags: ['AI', 'Threat Detection', 'Cybersecurity'],
      image: 'https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=800'
    },
    {
      id: '2',
      title: 'Zero Trust Architecture: Implementation Guide',
      excerpt: 'A comprehensive guide to implementing zero trust security architecture in your organization.',
      author: 'Marcus Rodriguez',
      publishedDate: '2024-01-10',
      readTime: '8 min read',
      tags: ['Zero Trust', 'Architecture', 'Security'],
      image: 'https://images.unsplash.com/photo-1563986768609-322da13575f3?w=800'
    },
    {
      id: '3',
      title: 'Ransomware Prevention: Best Practices',
      excerpt: 'Essential strategies to protect your organization from ransomware attacks.',
      author: 'Jennifer Kim',
      publishedDate: '2024-01-05',
      readTime: '6 min read',
      tags: ['Ransomware', 'Prevention', 'Best Practices'],
      image: 'https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=800'
    },
    {
      id: '4',
      title: 'Cloud Security Monitoring at Scale',
      excerpt: 'How to effectively monitor and secure cloud infrastructure across multiple environments.',
      author: 'David Thompson',
      publishedDate: '2024-01-01',
      readTime: '7 min read',
      tags: ['Cloud Security', 'Monitoring', 'Scale'],
      image: 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800'
    }
  ];

  const startIndex = parseInt(offset);
  const endIndex = startIndex + parseInt(limit);
  const posts = mockPosts.slice(startIndex, endIndex);

  res.json({
    posts,
    total: mockPosts.length,
    hasMore: endIndex < mockPosts.length
  });
});

// Get single blog post
router.get('/blog/:id', (req, res) => {
  const { id } = req.params;
  
  // Mock blog post content
  const post = {
    id: id,
    title: 'Advanced Threat Detection: AI-Powered Security',
    content: `
      <p>Artificial Intelligence is transforming the landscape of cybersecurity, offering unprecedented capabilities in threat detection and response.</p>
      
      <h2>The Evolution of Threat Detection</h2>
      <p>Traditional signature-based detection methods are no longer sufficient against modern threats. AI-powered systems can identify patterns and anomalies that would be impossible for human analysts to detect.</p>
      
      <h2>Machine Learning in Security</h2>
      <p>Machine learning algorithms can process vast amounts of data in real-time, learning from each interaction to improve detection accuracy and reduce false positives.</p>
    `,
    author: 'Sarah Chen',
    publishedDate: '2024-01-15',
    readTime: '5 min read',
    tags: ['AI', 'Threat Detection', 'Cybersecurity'],
    image: 'https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=800'
  };

  res.json({ post });
});

// Company information endpoint
router.get('/company', (req, res) => {
  res.json({
    name: 'LockShield Analytics',
    mission: 'Protecting organizations with advanced cybersecurity analytics and threat detection',
    founded: '2020',
    team: {
      size: '50-100 employees',
      locations: ['San Francisco', 'New York', 'London']
    },
    values: [
      'Security First',
      'Innovation',
      'Transparency',
      'Customer Success'
    ],
    certifications: [
      'SOC 2 Type II',
      'ISO 27001',
      'GDPR Compliant',
      'CCPA Compliant'
    ]
  });
});

module.exports = router;