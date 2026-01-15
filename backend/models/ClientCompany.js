const mongoose = require('mongoose');

const clientCompanySchema = new mongoose.Schema({
  name: {
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
  website: String,
  industry: {
    type: String,
    enum: ['technology', 'finance', 'healthcare', 'retail', 'manufacturing', 'government', 'education', 'other'],
    default: 'technology'
  },
  size: {
    type: String,
    enum: ['1-10', '11-50', '51-200', '201-1000', '1000+'],
    default: '1-10'
  },
  subscription: {
    plan: {
      type: String,
      enum: ['free', 'starter', 'professional', 'enterprise'],
      default: 'free'
    },
    status: {
      type: String,
      enum: ['active', 'inactive', 'suspended', 'cancelled', 'trial'],
      default: 'trial'
    },
    startDate: Date,
    endDate: Date
  },
  services: [{
    type: String,
    enum: ['web_security', 'app_security', 'network_security', 'cloud_security', 'api_security', 'iot_security', 'automobile_security']
  }],
  securityModels: {
    offensive: { type: Boolean, default: false },
    defensive: { type: Boolean, default: false }
  },
  isActive: {
    type: Boolean,
    default: true
  }
}, {
  timestamps: true
});

module.exports = mongoose.model('ClientCompany', clientCompanySchema);
