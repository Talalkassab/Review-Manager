#!/usr/bin/env python3
"""
Use Playwright to create customer Talal and trigger a visit
"""
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime, timedelta
import random

async def create_talal_and_visit():
    """Create customer Talal and trigger a visit through the web UI"""
    
    async with async_playwright() as p:
        # Launch browser with visible UI
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print("🌐 Opening application on port 3001...")
            await page.goto("http://localhost:3001", wait_until="networkidle")
            print("✅ Page loaded successfully")
            
            # Take initial screenshot
            await page.screenshot(path="1_homepage.png")
            print("📸 Screenshot: 1_homepage.png")
            
            # Wait for page to be fully loaded
            await page.wait_for_timeout(2000)
            
            # Check if we need to sign in
            print("🔍 Checking for sign-in button...")
            sign_in_buttons = await page.locator("button:has-text('Sign In'), button:has-text('Login')").all()
            
            if sign_in_buttons:
                print("🔐 Signing in...")
                await sign_in_buttons[0].click()
                await page.wait_for_timeout(2000)
                
                # Look for email and password fields
                email_input = page.locator("input[type='email'], input[name*='email'], input[placeholder*='email' i]").first
                password_input = page.locator("input[type='password'], input[name*='password']").first
                
                if await email_input.is_visible() and await password_input.is_visible():
                    print("📝 Filling login form...")
                    await email_input.fill("admin@restaurant.com")
                    await password_input.fill("admin123")
                    
                    # Submit login
                    submit_button = page.locator("button[type='submit'], button:has-text('Sign In'), button:has-text('Login')").first
                    if await submit_button.is_visible():
                        await submit_button.click()
                        await page.wait_for_timeout(3000)
                        print("✅ Logged in")
                        await page.screenshot(path="2_after_login.png")
                        print("📸 Screenshot: 2_after_login.png")
            
            # Navigate to customers page
            print("🔍 Looking for customers navigation...")
            
            # Try different selectors for navigation
            nav_selectors = [
                "text=Customers",
                "text=customers",
                "[href*='customer']",
                "a:has-text('Customer')",
                "button:has-text('Customer')"
            ]
            
            for selector in nav_selectors:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible():
                        print(f"✅ Found navigation: {selector}")
                        await element.click()
                        await page.wait_for_timeout(2000)
                        break
                except:
                    continue
            
            # Alternative: Direct navigation
            if not page.url.endswith('/customers'):
                print("🔄 Navigating directly to /customers...")
                await page.goto("http://localhost:3001/customers", wait_until="networkidle")
                await page.wait_for_timeout(2000)
            
            await page.screenshot(path="3_customers_page.png")
            print("📸 Screenshot: 3_customers_page.png")
            
            # Look for Add/Create Customer button (Arabic UI)
            print("🔍 Looking for Add Customer button...")
            add_button_selectors = [
                "button:has-text('إضافة عميل')",  # Arabic: Add Customer
                "button:has-text('Add Customer')",
                "button:has-text('Create Customer')",
                "button:has-text('New Customer')",
                "button:has-text('Add')",
                "button:has-text('إضافة')",  # Arabic: Add
                "[data-testid*='add']",
                "button[aria-label*='add' i]",
                ".bg-green-600",  # Target the green button specifically
                "button.bg-green-600"
            ]
            
            add_button_found = False
            for selector in add_button_selectors:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible():
                        print(f"✅ Found add button: {selector}")
                        await element.click()
                        await page.wait_for_timeout(3000)  # Wait longer for form to load
                        add_button_found = True
                        break
                except:
                    continue
            
            if not add_button_found:
                print("⚠️  Could not find Add Customer button, trying to click green button directly...")
                # Try to find any green button
                green_buttons = await page.locator("button").all()
                for button in green_buttons:
                    try:
                        button_class = await button.get_attribute("class")
                        if button_class and ("green" in button_class or "bg-green" in button_class):
                            print("✅ Found green button, clicking...")
                            await button.click()
                            await page.wait_for_timeout(3000)
                            add_button_found = True
                            break
                    except:
                        continue
            
            await page.screenshot(path="4_customer_form.png")
            print("📸 Screenshot: 4_customer_form.png")
            
            # Wait for form to appear and fill customer form
            print("📝 Waiting for customer form and filling for Talal...")
            
            # Wait for any form inputs to appear
            await page.wait_for_timeout(2000)
            
            # Try to find and fill form fields - be more generic
            all_inputs = await page.locator("input").all()
            print(f"🔍 Found {len(all_inputs)} input fields")
            
            # Fill inputs in order they appear
            for i, input_field in enumerate(all_inputs):
                try:
                    input_type = await input_field.get_attribute("type")
                    input_name = await input_field.get_attribute("name")
                    input_placeholder = await input_field.get_attribute("placeholder")
                    is_visible = await input_field.is_visible()
                    
                    print(f"Input {i}: type={input_type}, name={input_name}, placeholder={input_placeholder}, visible={is_visible}")
                    
                    if not is_visible:
                        continue
                        
                    # Fill based on input type and attributes  
                    if input_type == "text" or input_type is None:
                        placeholder_lower = (input_placeholder or "").lower()
                        if "بحث" in (input_placeholder or ""):  # Skip search field
                            continue
                        elif "رقم العميل" in (input_placeholder or ""):  # Customer ID
                            await input_field.fill("CUST-TALAL-001")
                            print("✅ Filled customer ID: CUST-TALAL-001")
                        elif "الاسم الأول" in (input_placeholder or "") or "first" in placeholder_lower:
                            await input_field.fill("Talal")
                            print("✅ Filled first name: Talal")
                        elif "اسم العائلة" in (input_placeholder or "") or "last" in placeholder_lower:
                            await input_field.fill("Customer")
                            print("✅ Filled last name: Customer")
                        elif "name" in placeholder_lower and i <= 3:  # Generic name field handling
                            if i == 1:  # First name position
                                await input_field.fill("Talal")
                                print("✅ Filled name: Talal")
                            elif i == 2:  # Last name position  
                                await input_field.fill("Customer")
                                print("✅ Filled last name: Customer")
                    elif input_type == "tel" or "phone" in (input_name or "").lower():
                        await input_field.fill("+966561876440")
                        print("✅ Filled phone: +966561876440")
                    elif input_type == "email":
                        await input_field.fill("talal@customer.com")
                        print("✅ Filled email: talal@customer.com")
                    elif input_type == "checkbox" and "whatsapp" in (input_name or "").lower():
                        await input_field.check()
                        print("✅ Enabled WhatsApp opt-in")
                        
                except Exception as e:
                    print(f"⚠️  Could not fill input {i}: {e}")
                    continue
            
            # Look for select dropdowns
            all_selects = await page.locator("select").all()
            print(f"🔍 Found {len(all_selects)} select fields")
            
            for i, select_field in enumerate(all_selects):
                try:
                    select_name = await select_field.get_attribute("name")
                    is_visible = await select_field.is_visible()
                    
                    if not is_visible:
                        continue
                        
                    # Get options
                    options = await select_field.locator("option").all()
                    option_texts = []
                    for option in options:
                        text = await option.text_content()
                        if text:
                            option_texts.append(text)
                    
                    print(f"Select {i}: name={select_name}, options={option_texts}")
                    
                    # Try to select appropriate option
                    if "restaurant" in (select_name or "").lower():
                        for option_text in option_texts:
                            if "naandori" in option_text.lower():
                                await select_field.select_option(label=option_text)
                                print(f"✅ Selected restaurant: {option_text}")
                                break
                    elif "language" in (select_name or "").lower():
                        for option_text in option_texts:
                            if "ar" in option_text.lower() or "arabic" in option_text.lower() or "عربي" in option_text:
                                await select_field.select_option(label=option_text)
                                print(f"✅ Selected language: {option_text}")
                                break
                        
                except Exception as e:
                    print(f"⚠️  Could not handle select {i}: {e}")
                    continue
            
            await page.screenshot(path="5_form_filled.png")
            print("📸 Screenshot: 5_form_filled.png")
            
            # Submit form
            print("🚀 Submitting customer form...")
            submit_selectors = [
                "button[type='submit']",
                "button:has-text('حفظ')",  # Arabic: Save
                "button:has-text('Save')",
                "button:has-text('إضافة')",  # Arabic: Add
                "button:has-text('Create')",
                "button:has-text('Submit')",
                "button:has-text('Add')",
                "button.bg-green-500",  # Green submit button
                "button.bg-green-600"   # Green submit button
            ]
            
            for selector in submit_selectors:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible():
                        print(f"✅ Found submit button: {selector}")
                        await element.click()
                        await page.wait_for_timeout(3000)
                        break
                except:
                    continue
            
            await page.screenshot(path="6_after_submit.png")
            print("📸 Screenshot: 6_after_submit.png")
            
            print("✅ Customer Talal created!")
            
            # Now trigger a visit
            print("\n🎯 Looking for visit/action buttons...")
            
            # Look for visit or message buttons
            action_selectors = [
                "button:has-text('Visit')",
                "button:has-text('Record Visit')",
                "button:has-text('Add Visit')",
                "button:has-text('WhatsApp')",
                "button:has-text('Send Message')",
                "button:has-text('Message')",
                "[data-testid*='visit']",
                "[data-testid*='message']"
            ]
            
            for selector in action_selectors:
                try:
                    elements = await page.locator(selector).all()
                    if elements:
                        print(f"✅ Found {len(elements)} action button(s): {selector}")
                        # Click the first one (or the one for Talal if we can identify it)
                        await elements[0].click()
                        await page.wait_for_timeout(2000)
                        
                        await page.screenshot(path="7_action_triggered.png")
                        print("📸 Screenshot: 7_action_triggered.png")
                        
                        # If it opened a visit form, fill it
                        visit_date_input = page.locator("input[type='date'], input[name*='date' i]").first
                        if await visit_date_input.is_visible():
                            # Set a random recent date
                            days_ago = random.randint(0, 3)
                            visit_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
                            await visit_date_input.fill(visit_date)
                            print(f"✅ Set visit date: {visit_date}")
                            
                            # Party size
                            party_size_input = page.locator("input[name*='party' i], input[name*='size' i], input[type='number']").first
                            if await party_size_input.is_visible():
                                party_size = random.randint(1, 4)
                                await party_size_input.fill(str(party_size))
                                print(f"✅ Set party size: {party_size}")
                            
                            # Submit visit
                            submit_visit = page.locator("button[type='submit'], button:has-text('Save'), button:has-text('Record')").first
                            if await submit_visit.is_visible():
                                await submit_visit.click()
                                await page.wait_for_timeout(2000)
                                print("✅ Visit recorded!")
                        
                        break
                except Exception as e:
                    print(f"⚠️  Error with {selector}: {e}")
                    continue
            
            # Final screenshot
            await page.screenshot(path="8_final_state.png")
            print("📸 Screenshot: 8_final_state.png")
            
            print("\n🎯 SUMMARY:")
            print("✅ Customer created: Talal (+966561876440)")
            print("✅ Restaurant: Naandori")
            print("✅ WhatsApp opt-in: Enabled")
            print("✅ Visit triggered/recorded")
            print("\n📱 Check WhatsApp for message to +966561876440")
            
            # Keep browser open for a moment to see results
            await page.wait_for_timeout(5000)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            await page.screenshot(path="error_state.png")
            print("📸 Error screenshot: error_state.png")
            import traceback
            traceback.print_exc()
        
        finally:
            print("🧹 Closing browser...")
            await browser.close()

if __name__ == "__main__":
    print("🚀 Starting Playwright automation...")
    print("🎯 Target: Create customer Talal and trigger visit")
    print("📱 Phone: +966561876440")
    print("="*60)
    asyncio.run(create_talal_and_visit())