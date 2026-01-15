# HavoSec CMS - Product Requirements Document

## Original Problem Statement
Build an integrated HavoSec application with:
1. A public-facing cybersecurity website with dynamic content
2. An admin panel (CoreUI Vue.js) for managing website content
3. A client dashboard for authenticated users to access security analytics

## Project Structure
```
/app/
├── frontend/          # Public HavoSec Website (Vue.js 3 + Vite) - Port 3000
│   ├── src/
│   │   ├── views/     # Home, About, Blog, BookDemo, Dashboard, Auth
│   │   ├── components/# Navigation, Footer, 3D components
│   │   ├── stores/    # Pinia stores (auth, dashboard, theme, ui, content)
│   │   └── router/    # Vue Router with auth guards
│   └── .env
├── backend/           # Python FastAPI Backend - Port 8001
│   ├── routes/        # admin_auth, client_auth, content, blog, etc.
│   ├── models/        # Pydantic schemas
│   ├── utils/         # seed data
│   └── server.py
├── admin/             # Admin Panel (CoreUI Vue.js) - Port 3001
│   └── src/
│       ├── stores/    # adminAuth.js, adminData.js
│       └── views/     # Admin pages
└── memory/
    └── PRD.md
```

## What's Been Implemented (Jan 15, 2026)

### ✅ Public Website (localhost:3000)
- Home page with 3D lock animation, dynamic hero section, features, achievements
- About page with dynamic content from API
- Blog page fetching posts from backend API
- Book Demo page with form submission
- Login/Register pages for client users
- Client Dashboard with security analytics

### ✅ Backend API (localhost:8001) - 31/31 Tests Passed
- **Admin Routes:**
  - `POST /api/admin/auth/login` - Admin login
  - `GET /api/admin/dashboard` - Admin dashboard stats
  - `GET/PUT /api/admin/content/:section` - Content management
  - `CRUD /api/admin/blog` - Blog management
  - `CRUD /api/admin/clients` - Client companies
  - `CRUD /api/admin/demo-requests` - Demo requests

- **Public/Client Routes:**
  - `POST /api/auth/register` - Client registration
  - `POST /api/auth/login` - Client login
  - `GET /api/auth/me` - Get profile
  - `GET /api/dashboard/*` - Security analytics
  - `GET /api/content/:section` - Public content
  - `GET /api/blog` - Public blog posts
  - `POST /api/demo` - Submit demo request

- **File Upload Routes:**
  - `POST /api/uploads/` - Upload single image
  - `POST /api/uploads/multiple` - Upload multiple images
  - `GET /api/uploads/images/:filename` - Serve uploaded image
  - `DELETE /api/uploads/images/:filename` - Delete image
  - `GET /api/uploads/` - List all uploaded images

- **Password Reset & Email Verification Routes (NEW):**
  - `POST /api/auth/forgot-password` - Request password reset
  - `POST /api/auth/verify-reset-token` - Verify reset token
  - `POST /api/auth/reset-password` - Reset password with token
  - `POST /api/auth/send-verification` - Send/resend verification email
  - `POST /api/auth/verify-email` - Verify email with token
  - `GET /api/auth/verification-status/:email` - Check verification status

- **Real-time Notifications Routes (NEW):**
  - `GET /api/notifications/` - Get user notifications
  - `POST /api/notifications/` - Create notification
  - `PUT /api/notifications/:id/read` - Mark as read
  - `PUT /api/notifications/mark-all-read` - Mark all as read
  - `DELETE /api/notifications/:id` - Delete notification
  - `DELETE /api/notifications/` - Clear all notifications
  - `WebSocket /api/notifications/ws/:userId` - Real-time notification stream

### ✅ Admin Panel (localhost:3001)
- Dashboard with overview stats
- Website Content Management (all sections editable)
- Blog Post Management (CRUD) with Image Upload
- Demo Request Management
- Client Company Management

### ✅ Dynamic Content Integration
- Home page fetches hero/features from /api/content
- About page fetches about section from /api/content
- Blog page fetches posts from /api/blog
- Content editable from admin panel

### ✅ Image Upload Feature
- File upload endpoint with validation (10MB max, common image formats)
- Drag & drop or click to upload in admin panel
- Preview uploaded images before saving
- URL input option for external images
- Automatic unique filename generation

### ✅ Password Reset Flow (NEW)
- Forgot Password page at /auth/forgot-password
- Reset Password page at /auth/reset-password
- Secure token-based reset (1 hour expiry)
- Integration with login page (Forgot password? link)

### ✅ Email Verification (NEW)
- Verification token generated on registration
- Verify Email page at /auth/verify-email
- 24-hour token expiry
- Resend verification option
- emailVerified status tracked in user profile

### ✅ Real-time Notifications (NEW)
- Notifications dropdown in navigation (bell icon)
- WebSocket connection for real-time updates
- Welcome notification on registration
- Login notifications for security tracking
- Mark as read/unread functionality
- Clear all notifications option
- Browser notification permission support

## Credentials
- **Admin Panel:** admin@havosec.com / password123
- **Test Client:** test_debug2@test.com / password123

## Tech Stack
- **Frontend:** Vue.js 3, Vite, Pinia, TailwindCSS, Three.js, GSAP
- **Backend:** Python, FastAPI, Motor (async MongoDB), JWT, bcrypt
- **Database:** MongoDB
- **Admin:** CoreUI Vue.js template

## Testing Status
- Backend: 31/31 tests passed (100%)
- Frontend: 90% working (navigation, forms, admin panel functional)
- Test file: /app/tests/test_havosec_api.py

## Completed Tasks
- ✅ Restore website from backup
- ✅ Rebrand from LockShield to HavoSec
- ✅ Convert Node.js backend to Python FastAPI
- ✅ Make website content dynamic (fetches from API)
- ✅ Admin panel integration with backend
- ✅ Client authentication and dashboard
- ✅ Comprehensive API testing

## Pending/Backlog Tasks

### P1 - Medium Priority
1. ~~Add image upload functionality for blog posts~~ ✅ DONE
2. Implement password reset flow
3. Add email verification for new users

### P2 - Future/Backlog
1. Production deployment configuration
2. Add more dashboard widgets and charts
3. Real-time notifications
4. API rate limiting improvements
5. Caching layer for performance
6. Rich text editor for blog content
