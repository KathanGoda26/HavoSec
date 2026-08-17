import { create } from 'zustand'

const useSEOStore = create((set, get) => ({
  // Static SEO store — no API calls
  globalSEO: {
    siteName: "HavoSec",
    siteUrl: "https://havosec.com",
    defaultOgImage: "/logo1.png",
    themeColor: "#8b5cf6",
    twitterSite: "@HavoSec",
    defaultAuthor: "HavoSec Team",
  },

  pageSEO: {
    home: {
      page: "home",
      seo: {
        title: "Advanced Cybersecurity Platform",
        description: "Protect your organization with HavoSec's comprehensive cybersecurity solutions.",
        keywords: "cybersecurity, security platform, threat detection",
      },
    },
    about: {
      page: "about",
      seo: {
        title: "About Us",
        description: "Learn about HavoSec's mission to protect organizations with cutting-edge cybersecurity.",
        keywords: "about havosec, cybersecurity company, security team",
      },
    },
    blog: {
      page: "blog",
      seo: {
        title: "Security Insights & Updates",
        description: "Stay informed with the latest cybersecurity trends and threat analysis.",
        keywords: "cybersecurity blog, security insights, threat analysis",
      },
    },
    pricing: {
      page: "pricing",
      seo: {
        title: "Pricing Plans",
        description: "Simple, transparent pricing for HavoSec cybersecurity solutions.",
        keywords: "cybersecurity pricing, security plans, havosec pricing",
      },
    },
    "book-demo": {
      page: "book-demo",
      seo: {
        title: "Book Your Demo",
        description: "Schedule a personalized demonstration of HavoSec's security platform.",
        keywords: "book demo, security demo, havosec demo",
      },
    },
  },

  loading: false,
  error: null,

  // All fetch/update functions are no-ops in static mode
  fetchGlobalSEO: () => get().globalSEO,
  fetchPageSEO: (page) => get().pageSEO[page] || {},
  updateGlobalSEO: () => {},
  updatePageSEO: () => {},
  fetchAllPagesSEO: () => Object.values(get().pageSEO),
  deletePageSEO: () => {},
  bulkUpdateSEO: () => {},

  // Derived
  get isLoading() { return get().loading },
  get hasError() { return get().error !== null },
}))

export { useSEOStore }
