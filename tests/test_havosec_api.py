"""
HavoSec API Backend Tests
Tests for: Content API, Client Auth, Admin Auth, Blog, Demo Requests, Client Dashboard
"""
import pytest
import requests
import os
import time

# Use localhost for testing since public URL returns 404
BASE_URL = "http://localhost:8001"

# Test credentials
ADMIN_EMAIL = "admin@havosec.com"
ADMIN_PASSWORD = "password123"
TEST_CLIENT_EMAIL = f"test_client_{int(time.time())}@test.com"
TEST_CLIENT_PASSWORD = "password123"


class TestHealthCheck:
    """Health check endpoint tests"""
    
    def test_health_endpoint(self):
        """Test /api/health returns OK"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "OK"
        assert data["service"] == "HavoSec API"
        print("✓ Health check passed")


class TestPublicContentAPI:
    """Public content API tests - fetching dynamic website content"""
    
    def test_get_all_content(self):
        """Test GET /api/content/ returns all website sections"""
        response = requests.get(f"{BASE_URL}/api/content/")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data or "sections" in data
        print(f"✓ Got {len(data.get('content', data.get('sections', [])))} content sections")
    
    def test_get_hero_content(self):
        """Test GET /api/content/hero returns hero section"""
        response = requests.get(f"{BASE_URL}/api/content/hero")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "title" in data["content"]
        assert "subtitle" in data["content"]
        print(f"✓ Hero content: {data['content']['title'][:50]}...")
    
    def test_get_features_content(self):
        """Test GET /api/content/features returns features section"""
        response = requests.get(f"{BASE_URL}/api/content/features")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "items" in data["content"]
        print(f"✓ Features content: {len(data['content']['items'])} items")
    
    def test_get_about_content(self):
        """Test GET /api/content/about returns about section"""
        response = requests.get(f"{BASE_URL}/api/content/about")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        print("✓ About content retrieved")
    
    def test_get_nonexistent_content(self):
        """Test GET /api/content/nonexistent returns 404"""
        response = requests.get(f"{BASE_URL}/api/content/nonexistent_section")
        assert response.status_code == 404
        print("✓ Nonexistent content returns 404")


class TestPublicBlogAPI:
    """Public blog API tests"""
    
    def test_get_blog_posts(self):
        """Test GET /api/blog/ returns blog posts"""
        response = requests.get(f"{BASE_URL}/api/blog/")
        assert response.status_code == 200
        data = response.json()
        assert "posts" in data
        assert "total" in data
        print(f"✓ Got {len(data['posts'])} blog posts, total: {data['total']}")
    
    def test_get_blog_posts_with_pagination(self):
        """Test GET /api/blog/ with limit and offset"""
        response = requests.get(f"{BASE_URL}/api/blog/?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["posts"]) <= 2
        print(f"✓ Pagination works: got {len(data['posts'])} posts with limit=2")


class TestClientAuth:
    """Client authentication tests - register and login"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.test_email = TEST_CLIENT_EMAIL
        self.test_password = TEST_CLIENT_PASSWORD
    
    def test_register_new_client(self):
        """Test POST /api/auth/register creates new client"""
        payload = {
            "email": self.test_email,
            "password": self.test_password,
            "firstName": "Test",
            "lastName": "User",
            "company": "Test Company"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == self.test_email.lower()
        print(f"✓ Client registered: {data['user']['email']}")
    
    def test_register_missing_fields(self):
        """Test POST /api/auth/register with missing fields returns 400"""
        payload = {
            "email": "incomplete@test.com",
            "password": "password123"
            # Missing firstName, lastName, company
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        assert response.status_code == 400
        print("✓ Missing fields returns 400")
    
    def test_register_short_password(self):
        """Test POST /api/auth/register with short password returns 400"""
        payload = {
            "email": "shortpass@test.com",
            "password": "short",
            "firstName": "Test",
            "lastName": "User",
            "company": "Test Company"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        assert response.status_code == 400
        print("✓ Short password returns 400")
    
    def test_login_client(self):
        """Test POST /api/auth/login with valid credentials"""
        # First register a user
        unique_email = f"login_test_{int(time.time())}@test.com"
        register_payload = {
            "email": unique_email,
            "password": "password123",
            "firstName": "Login",
            "lastName": "Test",
            "company": "Test Company"
        }
        requests.post(f"{BASE_URL}/api/auth/register", json=register_payload)
        
        # Now login
        login_payload = {
            "email": unique_email,
            "password": "password123"
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_payload)
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["success"] == True
        print(f"✓ Client login successful: {data['user']['email']}")
        return data["token"]
    
    def test_login_invalid_credentials(self):
        """Test POST /api/auth/login with invalid credentials returns 401"""
        payload = {
            "email": "nonexistent@test.com",
            "password": "wrongpassword"
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        assert response.status_code == 401
        print("✓ Invalid credentials returns 401")
    
    def test_get_profile_with_token(self):
        """Test GET /api/auth/me with valid token"""
        # Register and login to get token
        unique_email = f"profile_test_{int(time.time())}@test.com"
        register_payload = {
            "email": unique_email,
            "password": "password123",
            "firstName": "Profile",
            "lastName": "Test",
            "company": "Test Company"
        }
        requests.post(f"{BASE_URL}/api/auth/register", json=register_payload)
        
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": unique_email,
            "password": "password123"
        })
        token = login_response.json()["token"]
        
        # Get profile
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == unique_email.lower()
        print(f"✓ Profile retrieved: {data['user']['email']}")
    
    def test_get_profile_without_token(self):
        """Test GET /api/auth/me without token returns 401"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        print("✓ No token returns 401")


class TestAdminAuth:
    """Admin authentication tests"""
    
    def test_admin_login_success(self):
        """Test POST /api/admin/auth/login with valid admin credentials"""
        payload = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        response = requests.post(f"{BASE_URL}/api/admin/auth/login", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "token" in data
        assert "admin" in data
        assert data["admin"]["email"] == ADMIN_EMAIL
        print(f"✓ Admin login successful: {data['admin']['email']}")
        return data["token"]
    
    def test_admin_login_invalid_credentials(self):
        """Test POST /api/admin/auth/login with invalid credentials"""
        payload = {
            "email": "wrong@admin.com",
            "password": "wrongpassword"
        }
        response = requests.post(f"{BASE_URL}/api/admin/auth/login", json=payload)
        assert response.status_code == 401
        print("✓ Invalid admin credentials returns 401")
    
    def test_admin_get_me(self):
        """Test GET /api/admin/auth/me with valid admin token"""
        # Login first
        login_response = requests.post(f"{BASE_URL}/api/admin/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = login_response.json()["token"]
        
        # Get admin profile
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/admin/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        print(f"✓ Admin profile retrieved: {data['user']['email']}")


class TestAdminContentManagement:
    """Admin content management tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/admin/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_get_all_admin_content(self, admin_token):
        """Test GET /api/admin/content/ returns all content sections"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/content/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data or "sections" in data
        print(f"✓ Admin content retrieved: {len(data.get('content', data.get('sections', [])))} sections")
    
    def test_update_hero_content(self, admin_token):
        """Test PUT /api/admin/content/hero updates hero section"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get current content
        current = requests.get(f"{BASE_URL}/api/admin/content/hero", headers=headers).json()
        
        # Update content
        new_content = {
            "content": {
                "title": "Updated Hero Title",
                "subtitle": "Updated subtitle for testing",
                "ctaText": "Get Started",
                "ctaLink": "/book-demo"
            }
        }
        response = requests.put(f"{BASE_URL}/api/admin/content/hero", headers=headers, json=new_content)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print("✓ Hero content updated")
        
        # Verify update persisted
        verify = requests.get(f"{BASE_URL}/api/admin/content/hero", headers=headers)
        assert verify.status_code == 200
        verify_data = verify.json()
        assert verify_data["content"]["title"] == "Updated Hero Title"
        print("✓ Hero content update verified")
        
        # Restore original content
        restore_content = {"content": current.get("content", {})}
        requests.put(f"{BASE_URL}/api/admin/content/hero", headers=headers, json=restore_content)


class TestAdminBlogManagement:
    """Admin blog CRUD tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/admin/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_get_admin_blog_posts(self, admin_token):
        """Test GET /api/admin/blog/ returns blog posts"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/blog/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "posts" in data
        print(f"✓ Admin blog posts: {len(data['posts'])} posts")
    
    def test_create_blog_post(self, admin_token):
        """Test POST /api/admin/blog/ creates new blog post"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        payload = {
            "title": f"TEST_Blog Post {int(time.time())}",
            "content": "<p>This is a test blog post content.</p>",
            "excerpt": "Test excerpt for the blog post",
            "author": "Test Author",
            "category": "Testing",
            "tags": ["test", "automation"],
            "status": "draft"
        }
        response = requests.post(f"{BASE_URL}/api/admin/blog/", headers=headers, json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "post" in data
        assert data["post"]["title"] == payload["title"]
        print(f"✓ Blog post created: {data['post']['title']}")
        return data["post"]["id"]
    
    def test_create_and_delete_blog_post(self, admin_token):
        """Test full CRUD cycle for blog post"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create
        payload = {
            "title": f"TEST_Delete Post {int(time.time())}",
            "content": "<p>This post will be deleted.</p>",
            "excerpt": "Delete test",
            "author": "Test Author",
            "category": "Testing",
            "status": "draft"
        }
        create_response = requests.post(f"{BASE_URL}/api/admin/blog/", headers=headers, json=payload)
        assert create_response.status_code == 200
        post_id = create_response.json()["post"]["id"]
        print(f"✓ Created post: {post_id}")
        
        # Read
        get_response = requests.get(f"{BASE_URL}/api/admin/blog/{post_id}", headers=headers)
        assert get_response.status_code == 200
        print(f"✓ Retrieved post: {post_id}")
        
        # Delete
        delete_response = requests.delete(f"{BASE_URL}/api/admin/blog/{post_id}", headers=headers)
        assert delete_response.status_code == 200
        print(f"✓ Deleted post: {post_id}")
        
        # Verify deletion
        verify_response = requests.get(f"{BASE_URL}/api/admin/blog/{post_id}", headers=headers)
        assert verify_response.status_code == 404
        print("✓ Post deletion verified")


class TestDemoRequests:
    """Demo request submission tests"""
    
    def test_submit_demo_request(self):
        """Test POST /api/demo/ submits demo request"""
        payload = {
            "firstName": "Test",
            "lastName": "Demo",
            "email": f"demo_{int(time.time())}@test.com",
            "company": "Test Company",
            "phone": "+1234567890",
            "message": "I would like to schedule a demo",
            "companySize": "50-100",
            "preferredDate": "2025-02-01"
        }
        response = requests.post(f"{BASE_URL}/api/demo/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["status"] == "received"
        assert "id" in data
        print(f"✓ Demo request submitted: {data['id']}")
        return data["id"]


class TestClientDashboard:
    """Client dashboard API tests (requires authentication)"""
    
    @pytest.fixture
    def client_token(self):
        """Get client token for authenticated requests"""
        unique_email = f"dashboard_test_{int(time.time())}@test.com"
        # Register
        requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "password123",
            "firstName": "Dashboard",
            "lastName": "Test",
            "company": "Test Company"
        })
        # Login
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": unique_email,
            "password": "password123"
        })
        return response.json()["token"]
    
    def test_get_dashboard_overview(self, client_token):
        """Test GET /api/dashboard/overview returns security overview"""
        headers = {"Authorization": f"Bearer {client_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/overview", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "overview" in data
        assert "totalEvents" in data["overview"]
        assert "events24h" in data["overview"]
        assert "blockedAttacks" in data["overview"]
        print(f"✓ Dashboard overview: {data['overview']['totalEvents']} total events")
    
    def test_get_dashboard_overview_without_auth(self):
        """Test GET /api/dashboard/overview without token returns 401"""
        response = requests.get(f"{BASE_URL}/api/dashboard/overview")
        assert response.status_code == 401
        print("✓ Dashboard without auth returns 401")
    
    def test_get_attack_insights(self, client_token):
        """Test GET /api/dashboard/attack-insights returns attack data"""
        headers = {"Authorization": f"Bearer {client_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/attack-insights", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "attackInsights" in data
        print(f"✓ Attack insights retrieved")
    
    def test_get_defense_metrics(self, client_token):
        """Test GET /api/dashboard/defense-metrics returns defense data"""
        headers = {"Authorization": f"Bearer {client_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/defense-metrics", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "defenseMetrics" in data
        assert "blockingEfficiency" in data["defenseMetrics"]
        print(f"✓ Defense metrics: {data['defenseMetrics']['blockingEfficiency']}% blocking efficiency")
    
    def test_get_activity_logs(self, client_token):
        """Test GET /api/dashboard/activity-logs returns security logs"""
        headers = {"Authorization": f"Bearer {client_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/activity-logs", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "activityLogs" in data
        assert "pagination" in data
        print(f"✓ Activity logs: {len(data['activityLogs'])} logs, total: {data['pagination']['totalLogs']}")
    
    def test_get_system_health(self, client_token):
        """Test GET /api/dashboard/system-health returns system status"""
        headers = {"Authorization": f"Bearer {client_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/system-health", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "systemHealth" in data
        assert "services" in data["systemHealth"]
        print(f"✓ System health: {len(data['systemHealth']['services'])} services monitored")


class TestAdminDashboard:
    """Admin dashboard tests"""
    
    def test_admin_dashboard_stats(self):
        """Test GET /api/admin/dashboard returns admin stats"""
        response = requests.get(f"{BASE_URL}/api/admin/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "overview" in data
        assert "blog" in data["overview"]
        assert "demoRequests" in data["overview"]
        assert "clients" in data["overview"]
        print(f"✓ Admin dashboard: {data['overview']['blog']['total']} blog posts, {data['overview']['demoRequests']['total']} demo requests")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
