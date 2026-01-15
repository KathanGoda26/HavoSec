const mongoose = require('mongoose');

const websiteContentSchema = new mongoose.Schema({
  section: {
    type: String,
    required: true,
    unique: true,
    enum: ['hero', 'achievements', 'features', 'services', 'offensive_model', 'defensive_model', 'demo_cta', 'about_hero', 'about_mission', 'about_vision', 'about_values', 'about_company_info', 'footer', 'navigation', 'pricing']
  },
  content: {
    type: mongoose.Schema.Types.Mixed,
    required: true
  },
  isActive: {
    type: Boolean,
    default: true
  },
  lastUpdatedBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'AdminUser'
  }
}, {
  timestamps: true
});

module.exports = mongoose.model('WebsiteContent', websiteContentSchema);
