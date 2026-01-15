const AdminUser = require('./models/AdminUser');
const WebsiteContent = require('./models/WebsiteContent');
const BlogPost = require('./models/BlogPost');

const defaultContent = {
  hero: {
    title: 'Secure Your Digital Assets with',
    subtitle: 'HavoSec',
    description: 'AI-powered cybersecurity platform with Offensive and Defensive models. Real-time threat detection, automated response, and comprehensive security analytics for modern enterprises.',
    primaryButtonText: 'Book a Demo',
    primaryButtonLink: '/book-demo',
    secondaryButtonText: 'Learn More',
    secondaryButtonLink: '/about'
  },
  achievements: {
    items: [
      { id: 1, number: '50M+', label: 'Threats Blocked Daily' },
      { id: 2, number: '99.9%', label: 'Uptime Guarantee' },
      { id: 3, number: '500+', label: 'Enterprise Clients' },
      { id: 4, number: '24/7', label: 'Security Monitoring' }
    ]
  },
  features: {
    title: 'Advanced Security Features',
    features: [
      { id: 1, icon: 'ShieldCheckIcon', title: 'Real-Time Threat Detection', description: 'AI-powered detection identifies and blocks attacks instantly.', benefit: 'Reduce incidents by 95%' },
      { id: 2, icon: 'EyeIcon', title: 'Advanced Monitoring', description: 'Complete visibility across your digital infrastructure.', benefit: 'Zero blind spots' },
      { id: 3, icon: 'BoltIcon', title: 'Automated Response', description: 'Instant automated responses to security threats.', benefit: 'Response under 10 seconds' },
      { id: 4, icon: 'ChartBarIcon', title: 'Analytics Dashboard', description: 'Rich analytics for security insights and compliance.', benefit: 'Data-driven decisions' },
      { id: 5, icon: 'ExclamationTriangleIcon', title: 'Incident Management', description: 'Streamlined incident response workflows.', benefit: '80% faster resolution' },
      { id: 6, icon: 'ClockIcon', title: '24/7 Monitoring', description: 'Round-the-clock security monitoring and threat hunting.', benefit: 'Never miss a threat' }
    ]
  },
  offensive_model: {
    title: 'Offensive Security Model',
    description: 'Our AI-powered offensive model proactively attacks your systems to find vulnerabilities before hackers do.',
    features: [
      'Automated Penetration Testing',
      'Vulnerability Assessment',
      'Red Team Simulations',
      'Attack Surface Mapping',
      'Exploit Detection'
    ]
  },
  defensive_model: {
    title: 'Defensive Security Model',
    description: 'Real-time protection that defends your assets against all types of cyber threats.',
    features: [
      'Intrusion Detection & Prevention',
      'Threat Intelligence',
      'Incident Response',
      'Security Monitoring',
      'Compliance Management'
    ]
  },
  services: {
    title: 'Security Services',
    services: [
      { id: 1, name: 'Web Security', description: 'Comprehensive web application security testing and protection.', icon: 'GlobeAltIcon' },
      { id: 2, name: 'App Security', description: 'Mobile and desktop application security assessment.', icon: 'DevicePhoneMobileIcon' },
      { id: 3, name: 'Network Security', description: 'Network infrastructure security and monitoring.', icon: 'ServerIcon' },
      { id: 4, name: 'Cloud Security', description: 'Cloud infrastructure security and compliance.', icon: 'CloudIcon' },
      { id: 5, name: 'API Security', description: 'API security testing and protection.', icon: 'CodeBracketIcon' },
      { id: 6, name: 'IoT Security', description: 'Internet of Things device security.', icon: 'CpuChipIcon' }
    ]
  },
  about_hero: {
    title: 'About HavoSec',
    description: 'Protecting organizations with AI-powered cybersecurity since 2020'
  },
  about_mission: {
    title: 'Our Mission',
    text: 'To empower organizations with advanced cybersecurity that transforms how they detect, respond to, and prevent cyber threats.'
  },
  about_vision: {
    title: 'Our Vision',
    text: 'To be the global leader in AI-powered cybersecurity, creating a safer digital world.'
  },
  about_company_info: {
    founded: '2020',
    teamSize: '50-100 employees',
    locations: ['San Francisco', 'New York', 'London']
  },
  about_values: {
    values: [
      { id: 1, icon: 'ShieldCheckIcon', title: 'Security First', description: 'Security is our foundation.' },
      { id: 2, icon: 'LightBulbIcon', title: 'Innovation', description: 'Pushing cybersecurity boundaries.' },
      { id: 3, icon: 'EyeIcon', title: 'Transparency', description: 'Clear communication builds trust.' },
      { id: 4, icon: 'HeartIcon', title: 'Customer Success', description: 'Your security is our success.' }
    ]
  },
  demo_cta: {
    title: 'Ready to Secure Your Organization?',
    description: 'Get a personalized demo of HavoSec and see our Offensive and Defensive models in action.',
    buttonText: 'Schedule Your Demo',
    buttonLink: '/book-demo'
  },
  footer: {
    companyName: 'HavoSec',
    tagline: 'AI-Powered Cybersecurity',
    copyrightText: '© 2025 HavoSec. All rights reserved.'
  }
};

const defaultBlogPosts = [
  {
    title: 'Understanding Offensive vs Defensive Security Models',
    slug: 'offensive-vs-defensive-security',
    excerpt: 'Learn how combining offensive and defensive security approaches creates comprehensive protection.',
    content: '<p>Modern cybersecurity requires both offensive and defensive strategies...</p>',
    featuredImage: 'https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=800',
    author: { name: 'HavoSec Team' },
    category: 'cybersecurity',
    tags: ['Offensive Security', 'Defensive Security', 'Best Practices'],
    status: 'published',
    publishedAt: new Date()
  },
  {
    title: 'AI in Threat Detection: The Future of Cybersecurity',
    slug: 'ai-threat-detection-future',
    excerpt: 'How artificial intelligence is revolutionizing threat detection and response.',
    content: '<p>AI-powered threat detection represents the future of cybersecurity...</p>',
    featuredImage: 'https://images.unsplash.com/photo-1563986768609-322da13575f3?w=800',
    author: { name: 'HavoSec Research' },
    category: 'ai',
    tags: ['AI', 'Machine Learning', 'Threat Detection'],
    status: 'published',
    publishedAt: new Date()
  }
];

const seedDatabase = async () => {
  try {
    // Create super admin
    const existingAdmin = await AdminUser.findOne({ email: 'admin@havosec.com' });
    if (!existingAdmin) {
      const admin = new AdminUser({
        email: 'admin@havosec.com',
        password: 'HavoSec@2025',
        firstName: 'Super',
        lastName: 'Admin',
        role: 'super_admin',
        permissions: ['content', 'blog', 'users', 'clients', 'demo_requests', 'settings', 'analytics']
      });
      await admin.save();
      console.log('\x1b[33m%s\x1b[0m', '✓ Default admin created: admin@havosec.com / HavoSec@2025');
    }

    // Seed website content
    const existingContent = await WebsiteContent.countDocuments();
    if (existingContent === 0) {
      for (const [section, content] of Object.entries(defaultContent)) {
        await WebsiteContent.create({ section, content, isActive: true });
      }
      console.log('\x1b[33m%s\x1b[0m', '✓ Website content seeded');
    }

    // Seed blog posts
    const existingPosts = await BlogPost.countDocuments();
    if (existingPosts === 0) {
      for (const post of defaultBlogPosts) {
        await BlogPost.create(post);
      }
      console.log('\x1b[33m%s\x1b[0m', '✓ Blog posts seeded');
    }
  } catch (error) {
    console.error('Seed error:', error);
  }
};

module.exports = { seedDatabase };
