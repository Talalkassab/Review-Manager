#!/usr/bin/env python3
"""
Remove all customers from the database
"""
import asyncio
import sys
sys.path.append('/Users/hanouf/Desktop/projects/Customer-Whatsapp-agent/backend')

from app.database import db_manager
from app.models import Customer, WhatsAppMessage
from sqlalchemy import select, delete

async def cleanup_customers():
    """Remove all customers and their related data"""
    
    print("🧹 CLEANING UP DATABASE - REMOVING ALL CUSTOMERS")
    print("="*60)
    
    await db_manager.initialize()
    
    async with db_manager.get_session() as session:
        # First, count existing customers
        stmt = select(Customer)
        result = await session.execute(stmt)
        customers = result.scalars().all()
        customer_count = len(customers)
        
        if customer_count == 0:
            print("✅ Database is already clean - no customers found")
            return
        
        print(f"📊 Found {customer_count} customers to remove:")
        for customer in customers:
            print(f"   • {customer.customer_number} ({customer.phone_number})")
        
        # Count related WhatsApp messages
        stmt = select(WhatsAppMessage)
        result = await session.execute(stmt)
        messages = result.scalars().all()
        message_count = len(messages)
        
        print(f"📨 Found {message_count} WhatsApp messages to remove")
        
        # Confirm deletion
        print(f"\n⚠️  WARNING: This will permanently delete:")
        print(f"   • {customer_count} customers")
        print(f"   • {message_count} WhatsApp messages")
        print(f"   • All related customer data")
        
        proceed = input("\n❓ Are you sure you want to proceed? (yes/no): ").lower().strip()
        
        if proceed != 'yes':
            print("❌ Cleanup cancelled")
            return
        
        print(f"\n🔄 Starting cleanup...")
        
        try:
            # Delete WhatsApp messages first (due to foreign key constraints)
            if message_count > 0:
                stmt = delete(WhatsAppMessage)
                result = await session.execute(stmt)
                print(f"✅ Deleted {result.rowcount} WhatsApp messages")
            
            # Delete customers
            if customer_count > 0:
                stmt = delete(Customer)
                result = await session.execute(stmt)
                print(f"✅ Deleted {result.rowcount} customers")
            
            # Commit the changes
            await session.commit()
            
            print(f"\n🎯 CLEANUP COMPLETED SUCCESSFULLY!")
            print("="*60)
            print("✅ All customers removed from database")
            print("✅ All WhatsApp messages removed")
            print("✅ Database is now clean")
            print("="*60)
            
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
            await session.rollback()
            print("🔄 Database changes rolled back")
            
            # Show error details
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting database cleanup...")
    asyncio.run(cleanup_customers())