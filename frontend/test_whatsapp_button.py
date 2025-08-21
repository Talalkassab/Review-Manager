#!/usr/bin/env python3
"""
Test WhatsApp button functionality on frontend with created customer.
This script tests the customer list and WhatsApp button click.
"""
import asyncio
import random
from playwright.async_api import async_playwright
import time

async def test_whatsapp_button():
    print("🚀 Starting WhatsApp button test...")
    print("🎯 Target: Test WhatsApp functionality for Talal customer")
    print("📱 Phone: +966561876440")
    print("="*60)
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='ar-SA'
        )
        page = await context.new_page()
        
        try:
            # Navigate to the application
            print("🌐 Opening application on port 3001...")
            await page.goto('http://localhost:3001')
            await page.wait_for_load_state('networkidle')
            
            # Take screenshot
            await page.screenshot(path='1_homepage_test.png', full_page=True)
            print("✅ Page loaded successfully")
            print("📸 Screenshot: 1_homepage_test.png")
            
            # Check for sign-in button and sign in
            print("🔍 Checking for sign-in button...")
            sign_in_button = await page.query_selector("button:has-text('Sign In'), button:has-text('تسجيل الدخول')")
            
            if sign_in_button:
                print("🔐 Signing in...")
                await sign_in_button.click()
                await page.wait_for_timeout(2000)
            
            # Navigate to customers page
            print("🔍 Looking for customers navigation...")
            customers_nav = await page.query_selector("[href*='customer'], a:has-text('العملاء'), a:has-text('Customer')")
            
            if customers_nav:
                print("✅ Found navigation: [href*='customer']")
                await customers_nav.click()
                await page.wait_for_timeout(2000)
                await page.screenshot(path='2_customers_page_test.png', full_page=True)
                print("📸 Screenshot: 2_customers_page_test.png")
            
            # Look for customer table or list
            print("🔍 Looking for customer list...")
            await page.wait_for_timeout(3000)
            
            # Look for Talal customer row
            print("🔍 Looking for Talal customer...")
            
            # Look for the specific customer card/row structure
            customers = await page.query_selector_all(".bg-white, .customer-card, div:has(button:has-text('واتساب')), div:has(button:has-text('WhatsApp'))")
            print(f"🔍 Found {len(customers)} potential customer entries")
            
            # Also try looking for WhatsApp buttons directly
            all_whatsapp_buttons = await page.query_selector_all("button:has-text('واتساب'), button:has-text('WhatsApp')")
            print(f"🔍 Found {len(all_whatsapp_buttons)} WhatsApp buttons total")
            
            talal_found = False
            whatsapp_button = None
            
            # First, try to find Talal by looking at the entire page content
            page_content = await page.text_content('body')
            if "Talal" in page_content and "+966561876440" in page_content:
                print("✅ Talal customer found on page!")
                talal_found = True
                
                # Now look for WhatsApp button - try the first one since there's only one customer
                if all_whatsapp_buttons:
                    whatsapp_button = all_whatsapp_buttons[0]
                    print("✅ Found WhatsApp button!")
                else:
                    print("⚠️ No WhatsApp button found")
            
            # Alternative approach - look in customer entries
            if not talal_found:
                for i, customer in enumerate(customers):
                    try:
                        text_content = await customer.text_content()
                        if text_content and ("Talal" in text_content or "+966561876440" in text_content or "561876440" in text_content):
                            print(f"✅ Found Talal customer in entry {i}: {text_content[:100]}...")
                            talal_found = True
                            
                            # Look for WhatsApp button in this entry
                            whatsapp_buttons = await customer.query_selector_all("button:has-text('WhatsApp'), button:has-text('واتساب'), button[title*='whatsapp' i], .whatsapp-btn, [data-action='whatsapp']")
                            
                            if whatsapp_buttons:
                                whatsapp_button = whatsapp_buttons[0]
                                print("✅ Found WhatsApp button for Talal!")
                                break
                            else:
                                print("⚠️ Talal found but no WhatsApp button in this entry")
                    except Exception as e:
                        continue
            
            if not talal_found:
                print("❌ Talal customer not found in the list")
                print("🔍 Let's check what customers are available...")
                
                # Try to get all text from customer rows
                for i, customer in enumerate(customers[:5]):  # Check first 5 rows
                    try:
                        text = await customer.text_content()
                        if text and len(text.strip()) > 0:
                            print(f"Customer {i}: {text.strip()[:200]}...")
                    except Exception as e:
                        continue
            
            # Screenshot before clicking
            await page.screenshot(path='3_before_whatsapp_click.png', full_page=True)
            print("📸 Screenshot: 3_before_whatsapp_click.png")
            
            if whatsapp_button:
                print("🚀 Clicking WhatsApp button...")
                await whatsapp_button.click()
                
                # Wait for potential response or modal
                await page.wait_for_timeout(3000)
                
                # Screenshot after clicking
                await page.screenshot(path='4_after_whatsapp_click.png', full_page=True)
                print("📸 Screenshot: 4_after_whatsapp_click.png")
                
                # Check for success/error messages
                success_msg = await page.query_selector(".success, .alert-success, [class*='success' i]")
                error_msg = await page.query_selector(".error, .alert-error, .alert-danger, [class*='error' i]")
                
                if success_msg:
                    success_text = await success_msg.text_content()
                    print(f"✅ Success message: {success_text}")
                elif error_msg:
                    error_text = await error_msg.text_content()
                    print(f"❌ Error message: {error_text}")
                else:
                    print("ℹ️ No visible success/error message found")
                
                print("✅ WhatsApp button test completed!")
            else:
                print("❌ WhatsApp button not found for any customer")
            
            # Final screenshot
            await page.screenshot(path='5_final_test.png', full_page=True)
            print("📸 Screenshot: 5_final_test.png")
            
            print("\n" + "="*60)
            print("🎯 SUMMARY:")
            print(f"✅ Customer page accessed: {'✅' if customers else '❌'}")
            print(f"✅ Talal customer found: {'✅' if talal_found else '❌'}")
            print(f"✅ WhatsApp button found: {'✅' if whatsapp_button else '❌'}")
            print(f"✅ WhatsApp button clicked: {'✅' if whatsapp_button else '❌'}")
            
            if whatsapp_button:
                print("\n📱 Note: For Twilio sandbox testing:")
                print("   Customer needs to send 'join out-when' to +14155238886")
                print("   Then they'll receive the greeting message")
            
        except Exception as e:
            print(f"❌ Error during test: {str(e)}")
            await page.screenshot(path='error_test.png', full_page=True)
            print("📸 Error screenshot: error_test.png")
        
        finally:
            # Close browser
            print("🧹 Closing browser...")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_whatsapp_button())