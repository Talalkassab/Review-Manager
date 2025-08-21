#!/usr/bin/env python3
"""
End-to-end Playwright test to create customer and send WhatsApp message
"""
import asyncio
import sys
import os
from playwright.async_api import async_playwright

async def test_customer_creation_and_whatsapp():
    """Test creating a customer visit through the web interface and send WhatsApp"""
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print("🌐 Opening web application...")
            await page.goto("http://localhost:3000", wait_until="networkidle")
            print("✅ Page loaded successfully")
            
            # Take a screenshot to see what we have
            await page.screenshot(path="homepage.png")
            print("📸 Screenshot taken: homepage.png")
            
            # Wait for page to be interactive
            await page.wait_for_timeout(2000)
            
            # Print page title and URL
            title = await page.title()
            url = page.url
            print(f"📄 Page title: {title}")
            print(f"🔗 Current URL: {url}")
            
            # Check if we need to sign in first
            print("🔍 Checking if authentication is needed...")
            sign_in_button = page.locator("button:has-text('Sign In')").first
            if await sign_in_button.is_visible():
                print("🔐 Need to sign in first...")
                await sign_in_button.click()
                await page.wait_for_timeout(2000)
                
                # Fill login form
                email_input = page.locator("input[type='email'], input[name*='email']").first
                password_input = page.locator("input[type='password'], input[name*='password']").first
                
                if await email_input.is_visible() and await password_input.is_visible():
                    print("📝 Filling login form...")
                    await email_input.fill("admin@restaurant.com")
                    await password_input.fill("admin123")
                    
                    # Submit login
                    login_submit = page.locator("button[type='submit'], button:has-text('Sign In'), button:has-text('Login')").first
                    if await login_submit.is_visible():
                        await login_submit.click()
                        await page.wait_for_timeout(3000)
                        print("✅ Signed in successfully")
                        
                        # Take screenshot after login
                        await page.screenshot(path="after_login.png")
                        print("📸 Screenshot taken: after_login.png")
                    else:
                        print("❌ Could not find login submit button")
                else:
                    print("❌ Could not find email/password inputs")
            
            # Look for navigation to customers page
            print("🔍 Looking for navigation to customers...")
            
            # Try different ways to navigate to customers
            navigation_attempts = [
                "text=customers",
                "text=Customers", 
                "[href*='customer']",
                "[href='/customers']",
                "text=Customer Management",
                "button:has-text('Customer')"
            ]
            
            customer_nav = None
            for selector in navigation_attempts:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible():
                        customer_nav = element
                        print(f"✅ Found navigation element: {selector}")
                        break
                except:
                    continue
            
            if customer_nav:
                print("🖱️  Clicking on customer navigation...")
                await customer_nav.click()
                await page.wait_for_load_state("networkidle")
                print("✅ Navigated to customers page")
                
                # Take screenshot of customers page
                await page.screenshot(path="customers_page.png")
                print("📸 Screenshot taken: customers_page.png")
            else:
                # Try directly navigating to customers URL
                print("🔄 Trying direct navigation to /customers...")
                await page.goto("http://localhost:3000/customers", wait_until="networkidle")
                await page.screenshot(path="customers_direct.png")
                print("📸 Screenshot taken: customers_direct.png")
            
            # Wait for the page to load completely
            await page.wait_for_timeout(3000)
            
            # Look for "Add Customer" or "Create Customer" button
            print("🔍 Looking for 'Add Customer' button...")
            add_buttons = [
                "text=Add Customer",
                "text=Create Customer", 
                "text=New Customer",
                "button:has-text('Add')",
                "button:has-text('Create')",
                "[data-testid*='add']",
                "[data-testid*='create']"
            ]
            
            add_button = None
            for selector in add_buttons:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible():
                        add_button = element
                        print(f"✅ Found add button: {selector}")
                        break
                except:
                    continue
            
            if add_button:
                print("🖱️  Clicking 'Add Customer' button...")
                await add_button.click()
                await page.wait_for_timeout(2000)
                
                # Take screenshot of form
                await page.screenshot(path="customer_form.png")
                print("📸 Screenshot taken: customer_form.png")
                
                # Fill out the form
                print("📝 Filling out customer form...")
                
                # Phone number (required)
                phone_input = page.locator("input[name*='phone'], input[placeholder*='phone'], input[id*='phone']").first
                if await phone_input.is_visible():
                    await phone_input.fill("+966561876440")
                    print("✅ Phone number filled: +966561876440")
                
                # Leave name fields empty to test "Dear Customer" functionality
                print("ℹ️  Leaving name fields empty to test 'Dear Customer' functionality")
                
                # Select restaurant (Naandori)
                print("🏪 Looking for restaurant selection...")
                restaurant_selectors = [
                    "select[name*='restaurant']",
                    "[data-testid*='restaurant']", 
                    "input[name*='restaurant']"
                ]
                
                for selector in restaurant_selectors:
                    try:
                        element = page.locator(selector).first
                        if await element.is_visible():
                            # Try to select Naandori
                            if await element.get_attribute("tagName") == "SELECT":
                                await element.select_option(label="Naandori")
                            else:
                                await element.fill("Naandori")
                            print("✅ Restaurant selected: Naandori")
                            break
                    except Exception as e:
                        print(f"⚠️  Restaurant selection attempt failed: {e}")
                        continue
                
                # Set visit details
                print("📅 Setting visit details...")
                
                # Party size
                party_input = page.locator("input[name*='party'], input[name*='size']").first
                if await party_input.is_visible():
                    await party_input.fill("1")
                    print("✅ Party size set to 1")
                
                # Submit the form
                print("🚀 Submitting customer form...")
                submit_buttons = [
                    "button[type='submit']",
                    "text=Save",
                    "text=Create",
                    "text=Submit",
                    "button:has-text('Save')",
                    "button:has-text('Create')"
                ]
                
                submit_button = None
                for selector in submit_buttons:
                    try:
                        element = page.locator(selector).first
                        if await element.is_visible():
                            submit_button = element
                            print(f"✅ Found submit button: {selector}")
                            break
                    except:
                        continue
                
                if submit_button:
                    await submit_button.click()
                    print("✅ Form submitted!")
                    
                    # Wait for success message or redirect
                    await page.wait_for_timeout(3000)
                    
                    # Take screenshot after submission
                    await page.screenshot(path="after_submission.png")
                    print("📸 Screenshot taken: after_submission.png")
                    
                    # Look for the created customer in the list
                    print("🔍 Looking for the created customer...")
                    customer_rows = page.locator("tr, .customer-row, [data-testid*='customer']")
                    count = await customer_rows.count()
                    print(f"📊 Found {count} customer rows")
                    
                    # Now try to send WhatsApp message
                    print("📱 Looking for WhatsApp/Message button...")
                    message_buttons = [
                        "text=Send Message",
                        "text=WhatsApp",
                        "button:has-text('Message')",
                        "[data-testid*='message']",
                        "[data-testid*='whatsapp']"
                    ]
                    
                    message_button = None
                    for selector in message_buttons:
                        try:
                            element = page.locator(selector).first
                            if await element.is_visible():
                                message_button = element
                                print(f"✅ Found message button: {selector}")
                                break
                        except:
                            continue
                    
                    if message_button:
                        print("📤 Sending WhatsApp message...")
                        await message_button.click()
                        await page.wait_for_timeout(2000)
                        
                        # Take final screenshot
                        await page.screenshot(path="message_sent.png")
                        print("📸 Screenshot taken: message_sent.png")
                        print("✅ WhatsApp message sending initiated!")
                    else:
                        print("⚠️  Could not find message/WhatsApp button")
                    
                else:
                    print("❌ Could not find submit button")
                    
            else:
                print("❌ Could not find 'Add Customer' button")
                
                # Show what's available on the page
                print("📋 Available elements:")
                all_buttons = page.locator("button, a")
                count = await all_buttons.count()
                print(f"Found {count} clickable elements:")
                
                for i in range(min(count, 10)):  # Show first 10
                    element = all_buttons.nth(i)
                    try:
                        text = await element.inner_text()
                        tag = await element.evaluate("el => el.tagName")
                        print(f"  {i+1}. <{tag.lower()}> '{text.strip()}'")
                    except:
                        print(f"  {i+1}. [Could not read element]")
        
        except Exception as e:
            print(f"❌ Error during test: {e}")
            await page.screenshot(path="error_state.png")
            print("📸 Error screenshot taken: error_state.png")
        
        finally:
            print("🧹 Closing browser...")
            await browser.close()
            print("✅ Test completed!")

if __name__ == "__main__":
    print("🚀 Starting Playwright E2E test...")
    asyncio.run(test_customer_creation_and_whatsapp())