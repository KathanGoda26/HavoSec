const mongoose = require('mongoose');

const demoRequestSchema = new mongoose.Schema({
  firstName: {
    type: String,
    required: true,
    trim: true
  },
  lastName: {
    type: String,
    required: true,
    trim: true
  },
  email: {
    type: String,
    required: true,
    lowercase: true
  },
  phone: String,
  company: {
    type: String,
    required: true
  },
  companySize: {
    type: String,
    enum: ['1-10', '11-50', '51-200', '201-1000', '1000+'],
    default: '1-10'
  },
  jobTitle: String,
  message: String,
  interestedServices: [{
    type: String,
    enum: ['web_security', 'app_security', 'network_security', 'cloud_security', 'api_security', 'iot_security', 'automobile_security', 'offensive_model', 'defensive_model']
  }],
  status: {
    type: String,
    enum: ['new', 'contacted', 'scheduled', 'completed', 'cancelled'],
    default: 'new'
  },
  priority: {
    type: String,
    enum: ['low', 'medium', 'high', 'urgent'],
    default: 'medium'
  },
  notes: [{
    content: String,
    addedBy: String,
    addedAt: { type: Date, default: Date.now }
  }]
}, {
  timestamps: true
});

module.exports = mongoose.model('DemoRequest', demoRequestSchema);
