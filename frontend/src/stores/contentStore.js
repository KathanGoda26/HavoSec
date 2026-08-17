import { create } from 'zustand'

const useContentStore = create(() => ({
  // All content is now static — no API calls
  hero: {
    title: "Secure Your Digital Assets",
    subtitle: "Advanced cybersecurity analytics and threat detection platform designed for modern organizations.",
    demoTitle: "Ready to Protect Your",
    demoTitle2: "Organization?",
    demoDescription: "Get a personalized demonstration of HavoSec.",
    demoButtonText: "Schedule Your Demo Today",
    demoButtonLink: "/book-demo",
    animation: {
      modelPath: "/lock.glb",
      primaryColor: "#673ee6",
      secondaryColor: "#00b090",
      scale: 3,
      rotationSpeed: 0.005,
    },
  },

  features: {
    title: "Advanced Security Features",
    items: [
      {
        title: "Real-Time Threat Detection",
        description: "AI-powered detection identifies attacks in milliseconds.",
        benefit: "Stay ahead of emerging threats",
      },
      {
        title: "Advanced Monitoring",
        description: "Comprehensive visibility across your entire digital infrastructure.",
        benefit: "Complete oversight of your security landscape",
      },
      {
        title: "Automated Response",
        description: "Instant automated responses to security threats.",
        benefit: "Minimize damage immediately",
      },
      {
        title: "Analytics Dashboard",
        description: "Rich analytics and reporting for security insights.",
        benefit: "Data-driven security decisions",
      },
    ],
  },

  about: {
    title: "About HavoSec",
    description: "Protecting organizations with cutting-edge cybersecurity analytics and threat detection since 2020",
    mission: "To empower organizations with advanced cybersecurity analytics that transform how they detect, respond to, and prevent cyber threats. We believe that proactive security should be accessible, intelligent, and automated.",
    vision: "To create a world where every organization, regardless of size, has access to enterprise-grade cybersecurity protection powered by artificial intelligence.",
    companyInfo: [
      { title: "Founded", value: "2020" },
      { title: "Team Size", value: "50-100 employees" },
      { title: "Global Offices", value: "San Francisco, New York, London" },
    ],
    values: [
      { id: 1, icon: "ShieldCheckIcon", title: "Security First", description: "Everything we do is designed with security as the foundation, never as an afterthought." },
      { id: 2, icon: "LightBulbIcon", title: "Innovation", description: "We continuously push the boundaries of what's possible in cybersecurity technology." },
      { id: 3, icon: "EyeIcon", title: "Transparency", description: "Clear communication and honest practices build trust with our clients and partners." },
      { id: 4, icon: "HeartIcon", title: "Customer Success", description: "Our success is measured by the security and peace of mind we provide our clients." },
    ],
  },

  services: null,
  testimonials: null,

  header: {
    navLinks: [
      { name: "About", path: "/about" },
      { name: "Pricing", path: "/pricing" },
      { name: "Blog", path: "/blog" },
    ],
  },

  footer: {
    sections: [
      {
        title: "Product",
        links: [
          { name: "Features", path: "/" },
          { name: "Security", path: "/about" },
          { name: "Integrations", path: "#" },
          { name: "Pricing", path: "/pricing" },
          { name: "API", path: "#" },
        ],
      },
      {
        title: "Solutions",
        links: [
          { name: "Enterprise", path: "#" },
          { name: "Small Business", path: "#" },
          { name: "Government", path: "#" },
          { name: "Healthcare", path: "#" },
          { name: "Finance", path: "#" },
        ],
      },
      {
        title: "Resources",
        links: [
          { name: "Blog", path: "/blog" },
          { name: "Documentation", path: "#" },
          { name: "Help Center", path: "#" },
          { name: "Case Studies", path: "#" },
          { name: "Webinars", path: "#" },
        ],
      },
      {
        title: "Company",
        links: [
          { name: "About Us", path: "/about" },
          { name: "Careers", path: "#" },
          { name: "News", path: "#" },
          { name: "Contact", path: "#" },
          { name: "Partners", path: "#" },
        ],
      },
    ],
  },

  bookDemo: null,

  pricing: {
    hero: {
      title: "Simple, Transparent Pricing",
      subtitle: "Choose the perfect plan for your organization's security needs",
      savingsPercent: 20,
    },
    plans: [
      {
        name: "Starter",
        description: "Perfect for small teams getting started",
        monthlyPrice: 49,
        annualPrice: 39,
        features: ["Up to 10 scans per month", "Basic vulnerability detection", "Email support", "1 user account", "30-day scan history", "PDF reports"],
        ctaText: "Get Started",
        isPopular: false,
        isCustom: false,
      },
      {
        name: "Professional",
        description: "For growing teams with advanced needs",
        monthlyPrice: 99,
        annualPrice: 79,
        features: ["Unlimited scans", "Advanced threat detection", "Priority support (24/7)", "Up to 5 user accounts", "1-year scan history", "Custom reports & exports", "API access", "Compliance templates"],
        ctaText: "Get Started",
        isPopular: true,
        isCustom: false,
      },
      {
        name: "Enterprise",
        description: "For large organizations with custom requirements",
        monthlyPrice: 0,
        annualPrice: 0,
        features: ["Everything in Professional", "Unlimited scans & users", "Dedicated account manager", "Custom integrations", "On-premise deployment", "Advanced analytics", "SLA guarantees", "Custom training", "White-label options"],
        ctaText: "Contact Sales",
        isPopular: false,
        isCustom: true,
      },
    ],
    comparison: [
      { feature: "Scans per month", starter: "10", professional: "Unlimited", enterprise: "Unlimited" },
      { feature: "User accounts", starter: "1", professional: "5", enterprise: "Unlimited" },
      { feature: "Scan history", starter: "30 days", professional: "1 year", enterprise: "Unlimited" },
      { feature: "Support", starter: "Email", professional: "24/7 Priority", enterprise: "Dedicated Manager" },
      { feature: "API Access", starter: "false", professional: "true", enterprise: "true" },
    ],
    faq: [
      { question: "Can I change plans later?", answer: "Yes! You can upgrade or downgrade your plan at any time. Changes will be reflected in your next billing cycle." },
      { question: "What payment methods do you accept?", answer: "We accept all major credit cards (Visa, MasterCard, American Express), PayPal, and wire transfers for Enterprise plans." },
      { question: "Is there a free trial?", answer: "Yes! All plans come with a 14-day free trial. No credit card required to start." },
      { question: "What happens after my trial ends?", answer: "You'll be automatically enrolled in your selected plan. You can cancel anytime before the trial ends with no charges." },
      { question: "Do you offer refunds?", answer: "Yes, we offer a 30-day money-back guarantee. If you're not satisfied, contact us for a full refund." },
      { question: "Can I get a custom plan?", answer: "Absolutely! Contact our sales team to discuss custom requirements and pricing for your organization." },
    ],
    cta: {
      title: "Ready to secure your digital assets?",
      subtitle: "Start your 14-day free trial today. No credit card required.",
      primaryButton: "Start Free Trial",
      secondaryButton: "Contact Sales",
    },
  },

  auth: null,
  clientDashboard: {},
  isLoading: false,
  error: null,
}))

export { useContentStore }
