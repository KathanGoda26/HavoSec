export default [
  {
    component: 'CNavItem',
    name: 'Dashboard',
    to: '/dashboard',
    icon: 'cil-speedometer',
    badge: { color: 'primary', text: 'NEW' },
  },
  {
    component: 'CNavTitle',
    name: 'Content Management',
  },
  {
    component: 'CNavItem',
    name: 'Website Content',
    to: '/content/website',
    icon: 'cil-layers',
  },
  {
    component: 'CNavItem',
    name: 'Blog Posts',
    to: '/content/blog',
    icon: 'cil-newspaper',
  },
  {
    component: 'CNavTitle',
    name: 'Business',
  },
  {
    component: 'CNavItem',
    name: 'Demo Requests',
    to: '/business/demo-requests',
    icon: 'cil-calendar',
  },
  {
    component: 'CNavItem',
    name: 'Client Companies',
    to: '/business/clients',
    icon: 'cil-building',
  },
  {
    component: 'CNavTitle',
    name: 'Administration',
  },
  {
    component: 'CNavItem',
    name: 'Admin Users',
    to: '/admin/users',
    icon: 'cil-user',
  },
  {
    component: 'CNavItem',
    name: 'Settings',
    to: '/admin/settings',
    icon: 'cil-settings',
  },
]
