#!/usr/bin/env python3
"""
Automatically remove all customers from the database
"""
import asyncio
import sys
sys.path.append('/Users/hanouf/Desktop/projects/Customer-Whatsapp-agent/backend')

from app.database import db_manager
from app.models import Customer, WhatsAppMessage
from sqlalchemy import select, delete

async def cleanup_customers_auto():
    """Remove all customers and their related data automatically"""
    
    print("🧹 CLEANING UP DATABASE - REMOVING ALL CUSTOMERS")
    print("="*60)
    
    await db_manager.initialize()
    
    async with db_manager.get_session() as session:
        # Count existing customers
        stmt = select(Customer)
        result = await session.execute(stmt)
        customers = result.scalars().all()
        customer_count = len(customers)
        
        if customer_count == 0:
            print("✅ Database is already clean - no customers found")
            return
        
        print(f"📊 Found {customer_count} customers to remove:")
        for customer in customers:
            name = customer.customer_number or "None"
            print(f"   • {name} ({customer.phone_number})")
        
        # Count related WhatsApp messages
        stmt = select(WhatsAppMessage)
        result = await session.execute(stmt)
        messages = result.scalars().all()
        message_count = len(messages)
        
        print(f"📨 Found {message_count} WhatsApp messages to remove")
        
        print(f"\n🔄 Starting automatic cleanup...")
        
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
            
            # Verify cleanup
            print(f"\n🔍 Verifying cleanup...")
            stmt = select(Customer)
            result = await session.execute(stmt)
            remaining_customers = result.scalars().all()
            
            stmt = select(WhatsAppMessage)
            result = await session.execute(stmt)
            remaining_messages = result.scalars().all()
            
            print(f"📊 Remaining customers: {len(remaining_customers)}")
            print(f"📨 Remaining messages: {len(remaining_messages)}")
            
            if len(remaining_customers) == 0 and len(remaining_messages) == 0:
                print("✅ Database cleanup verification successful!")
            else:
                print("⚠️  Some data may still remain")
            
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
            await session.rollback()
            print("🔄 Database changes rolled back")
            
            # Show error details
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting automatic database cleanup...")
    asyncio.run(cleanup_customers_auto())