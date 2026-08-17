"""
Script to add Pricing link to the header navigation
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def add_pricing_to_nav():
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.havosec
    
    # Get current header content
    header = await db.website_content.find_one({"section": "header"})
    
    if header:
        print("Current header content:")
        print(header.get("content", {}))
        
        # Update navLinks to include Pricing
        nav_links = header.get("content", {}).get("navLinks", [])
        
        # Check if Pricing already exists
        pricing_exists = any(link.get("name") == "Pricing" for link in nav_links)
        
        if not pricing_exists:
            # Insert Pricing between About and Blog
            new_nav_links = []
            for link in nav_links:
                new_nav_links.append(link)
                if link.get("name") == "About":
                    new_nav_links.append({"name": "Pricing", "path": "/pricing"})
            
            # If About wasn't found, just append
            if not any(link.get("name") == "Pricing" for link in new_nav_links):
                new_nav_links.append({"name": "Pricing", "path": "/pricing"})
            
            # Update the database
            await db.website_content.update_one(
                {"section": "header"},
                {"$set": {"content.navLinks": new_nav_links}}
            )
            
            print("\n✅ Pricing link added to navigation!")
            print("New nav links:", new_nav_links)
        else:
            print("\n✅ Pricing link already exists in navigation!")
    else:
        print("❌ Header content not found in database")
        print("Creating default header with Pricing link...")
        
        default_header = {
            "section": "header",
            "content": {
                "navLinks": [
                    {"name": "Home", "path": "/"},
                    {"name": "About", "path": "/about"},
                    {"name": "Pricing", "path": "/pricing"},
                    {"name": "Blog", "path": "/blog"}
                ]
            }
        }
        
        await db.website_content.insert_one(default_header)
        print("✅ Default header created with Pricing link!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(add_pricing_to_nav())
