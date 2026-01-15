const mongoose = require('mongoose');

const securityEventSchema = new mongoose.Schema({
  id: {
    type: String,
    default: () => new mongoose.Types.ObjectId().toString(),
    unique: true
  },
  eventType: {
    type: String,
    required: true,
    enum: ['attack_blocked', 'intrusion_attempt', 'malware_detected', 'phishing_blocked', 'ddos_mitigated', 'vulnerability_scan', 'system_alert']
  },
  severity: {
    type: String,
    required: true,
    enum: ['low', 'medium', 'high', 'critical']
  },
  source: {
    ip: String,
    country: String,
    userAgent: String,
    referrer: String
  },
  target: {
    endpoint: String,
    service: String,
    port: Number
  },
  description: {
    type: String,
    required: true
  },
  details: {
    type: mongoose.Schema.Types.Mixed,
    default: {}
  },
  status: {
    type: String,
    enum: ['detected', 'blocked', 'investigating', 'resolved', 'false_positive'],
    default: 'detected'
  },
  assignedTo: {
    type: String,
    ref: 'User'
  },
  tags: [String],
  mitigationActions: [{
    action: String,
    timestamp: Date,
    performedBy: String
  }]
}, {
  timestamps: true
});

// Index for better query performance
securityEventSchema.index({ eventType: 1, createdAt: -1 });
securityEventSchema.index({ severity: 1, createdAt: -1 });
securityEventSchema.index({ 'source.ip': 1 });

module.exports = mongoose.model('SecurityEvent', securityEventSchema);