const SecurityEvent = require('../models/SecurityEvent');

// Generate mock security events for demo
const generateMockEvents = () => {
  const eventTypes = ['attack_blocked', 'intrusion_attempt', 'malware_detected', 'phishing_blocked', 'ddos_mitigated', 'vulnerability_scan'];
  const severities = ['low', 'medium', 'high', 'critical'];
  const statuses = ['detected', 'blocked', 'investigating', 'resolved'];
  const countries = ['US', 'CN', 'RU', 'KP', 'IR', 'TR', 'BR', 'IN'];
  
  const events = [];
  
  for (let i = 0; i < 100; i++) {
    const randomDate = new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000); // Last 30 days
    
    events.push({
      eventType: eventTypes[Math.floor(Math.random() * eventTypes.length)],
      severity: severities[Math.floor(Math.random() * severities.length)],
      source: {
        ip: `${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`,
        country: countries[Math.floor(Math.random() * countries.length)],
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      },
      target: {
        endpoint: `/api/${['login', 'dashboard', 'admin', 'upload', 'search'][Math.floor(Math.random() * 5)]}`,
        service: ['web', 'api', 'database', 'auth'][Math.floor(Math.random() * 4)],
        port: [80, 443, 22, 3306][Math.floor(Math.random() * 4)]
      },
      description: [
        'Suspicious login attempt detected',
        'SQL injection attack blocked',
        'Malware signature detected in upload',
        'DDoS attack mitigated',
        'Brute force attack on admin panel',
        'Phishing attempt blocked',
        'Vulnerability scan detected'
      ][Math.floor(Math.random() * 7)],
      status: statuses[Math.floor(Math.random() * statuses.length)],
      tags: ['automated', 'high-priority', 'investigation'],
      createdAt: randomDate,
      updatedAt: randomDate
    });
  }
  
  return events;
};

// Seed the database with mock data
const seedDatabase = async () => {
  try {
    const existingEvents = await SecurityEvent.countDocuments();
    
    if (existingEvents === 0) {
      console.log('🌱 Seeding database with mock security events...');
      const mockEvents = generateMockEvents();
      await SecurityEvent.insertMany(mockEvents);
      console.log(`✅ Successfully seeded ${mockEvents.length} security events`);
    } else {
      // console.log(`📊 Database already contains ${existingEvents} security events`);
    }
  } catch (error) {
    console.error('❌ Database seeding failed:', error);
  }
};

module.exports = { seedDatabase };