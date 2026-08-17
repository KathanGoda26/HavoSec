"""
Simple script to add Pricing link to header navigation via API
"""
import requests
import json

API_BASE = "http://localhost:8000/api"

def add_pricing_to_nav():
    try:
        # Get current header content
        response = requests.get(f"{API_BASE}/content/header")
        
        if response.status_code == 200:
            header_data = response.json()
            print("✅ Current header content retrieved")
            print(json.dumps(header_data, indent=2))
            
            # Get nav links
            nav_links = header_data.get("content", {}).get("navLinks", [])
            
            # Check if Pricing already exists
            pricing_exists = any(link.get("path") == "/pricing" for link in nav_links)
            
            if pricing_exists:
                print("\n✅ Pricing link already exists in navigation!")
                return
            
            # Insert Pricing after About
            new_nav_links = []
            for link in nav_links:
                new_nav_links.append(link)
                if link.get("path") == "/about":
                    new_nav_links.append({"name": "Pricing", "path": "/pricing"})
            
            # If About wasn't found, just append
            if not any(link.get("path") == "/pricing" for link in new_nav_links):
                new_nav_links.append({"name": "Pricing", "path": "/pricing"})
            
            # Update header content
            updated_content = header_data.get("content", {})
            updated_content["navLinks"] = new_nav_links
            
            # Send update request
            update_response = requests.put(
                f"{API_BASE}/content/header",
                json={"content": updated_content}
            )
            
            if update_response.status_code == 200:
                print("\n✅ Pricing link added to navigation successfully!")
                print("\nNew nav links:")
                print(json.dumps(new_nav_links, indent=2))
            else:
                print(f"\n❌ Failed to update: {update_response.status_code}")
                print(update_response.text)
                
        elif response.status_code == 404:
            print("❌ Header content not found in database")
            print("Creating default header with Pricing link...")
            
            default_header = {
                "content": {
                    "navLinks": [
                        {"name": "Home", "path": "/"},
                        {"name": "About", "path": "/about"},
                        {"name": "Pricing", "path": "/pricing"},
                        {"name": "Blog", "path": "/blog"}
                    ]
                }
            }
            
            create_response = requests.put(
                f"{API_BASE}/content/header",
                json=default_header
            )
            
            if create_response.status_code == 200:
                print("✅ Default header created with Pricing link!")
            else:
                print(f"❌ Failed to create header: {create_response.status_code}")
        else:
            print(f"❌ Error fetching header: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend API")
        print("Make sure the backend is running at http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("Adding Pricing link to navigation...\n")
    add_pricing_to_nav()
