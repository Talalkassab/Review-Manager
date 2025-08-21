const { chromium } = require('playwright');

async function runDemo() {
  console.log('🚀 Starting Restaurant AI Demo...');
  
  // Launch browser with head mode so you can watch
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 1000 // Slow down actions so you can follow
  });
  
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 }
  });
  
  const page = await context.newPage();
  
  try {
    console.log('📱 Step 1: Navigating to the application...');
    await page.goto('http://localhost:3002');
    await page.waitForTimeout(2000);
    
    console.log('🔐 Step 2: Looking for login form...');
    // Check if we need to login or if we're already logged in
    const loginForm = await page.locator('input[type="email"]').isVisible().catch(() => false);
    
    if (loginForm) {
      console.log('✅ Login form found, logging in...');
      await page.fill('input[type="email"]', 'admin@restaurant.com');
      await page.fill('input[type="password"]', 'Admin123!');
      await page.click('button[type="submit"]');
      await page.waitForTimeout(3000);
    } else {
      console.log('✅ Already logged in or no login required');
    }
    
    console.log('🏠 Step 3: Viewing Dashboard...');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'demo-dashboard.png' });
    
    console.log('👥 Step 4: Navigating to Customers page...');
    // Look for customers link in navigation
    await page.click('text=Customers').catch(async () => {
      // Try alternative selectors
      await page.click('[href="/customers"]').catch(async () => {
        await page.goto('http://localhost:3002/customers');
      });
    });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'demo-customers-page.png' });
    
    console.log('➕ Step 5: Adding first customer...');
    // Click Add Customer button
    await page.click('text=Add Customer').catch(async () => {
      await page.click('button:has-text("إضافة عميل")');
    });
    await page.waitForTimeout(1000);
    
    // Fill customer form
    console.log('📝 Filling customer form for Ahmed Hassan...');
    await page.fill('input[id="first_name"]', 'Ahmed');
    await page.fill('input[id="last_name"]', 'Hassan');
    await page.fill('input[id="phone_number"]', '+966501234567');
    await page.fill('input[id="email"]', 'ahmed.hassan@gmail.com');
    
    // Submit form
    await page.click('button:has-text("Save")').catch(async () => {
      await page.click('button:has-text("حفظ")');
    });
    await page.waitForTimeout(3000);
    
    console.log('📸 Taking screenshot after first customer...');
    await page.screenshot({ path: 'demo-customer-1-added.png' });
    
    console.log('➕ Step 6: Adding second customer...');
    await page.click('text=Add Customer').catch(async () => {
      await page.click('button:has-text("إضافة عميل")');
    });
    await page.waitForTimeout(1000);
    
    console.log('📝 Filling customer form for Sarah Johnson...');
    await page.fill('input[id="first_name"]', 'Sarah');
    await page.fill('input[id="last_name"]', 'Johnson');
    await page.fill('input[id="phone_number"]', '+966507654321');
    await page.fill('input[id="email"]', 'sarah.johnson@outlook.com');
    
    await page.click('button:has-text("Save")').catch(async () => {
      await page.click('button:has-text("حفظ")');
    });
    await page.waitForTimeout(3000);
    
    console.log('📸 Taking screenshot after second customer...');
    await page.screenshot({ path: 'demo-customer-2-added.png' });
    
    console.log('➕ Step 7: Adding third customer (Arabic name)...');
    await page.click('text=Add Customer').catch(async () => {
      await page.click('button:has-text("إضافة عميل")');
    });
    await page.waitForTimeout(1000);
    
    console.log('📝 Filling customer form for فاطمة محمد...');
    await page.fill('input[id="first_name"]', 'فاطمة');
    await page.fill('input[id="last_name"]', 'محمد');
    await page.fill('input[id="phone_number"]', '+966512345678');
    await page.fill('input[id="email"]', 'fatima.mohammed@gmail.com');
    
    // Set language to Arabic
    await page.selectOption('select[id="preferred_language"]', 'ar');
    
    await page.click('button:has-text("Save")').catch(async () => {
      await page.click('button:has-text("حفظ")');
    });
    await page.waitForTimeout(3000);
    
    console.log('📸 Taking screenshot after third customer...');
    await page.screenshot({ path: 'demo-customer-3-added.png' });
    
    console.log('🔍 Step 8: Testing search functionality...');
    await page.fill('input[placeholder*="Search"]', 'Ahmed').catch(async () => {
      await page.fill('input[placeholder*="بحث"]', 'Ahmed');
    });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'demo-search-results.png' });
    
    // Clear search
    await page.fill('input[placeholder*="Search"]', '').catch(async () => {
      await page.fill('input[placeholder*="بحث"]', '');
    });
    await page.waitForTimeout(1000);
    
    console.log('🏠 Step 9: Going back to Dashboard to see updated stats...');
    await page.click('text=Dashboard').catch(async () => {
      await page.click('[href="/"]').catch(async () => {
        await page.goto('http://localhost:3002');
      });
    });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: 'demo-dashboard-updated.png' });
    
    console.log('📊 Step 10: Exploring Analytics page...');
    await page.click('text=Analytics').catch(async () => {
      await page.goto('http://localhost:3002/analytics');
    });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'demo-analytics.png' });
    
    console.log('🤖 Step 11: Checking AI Chat page...');
    await page.click('text=AI Chat').catch(async () => {
      await page.goto('http://localhost:3002/ai-chat');
    });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'demo-ai-chat.png' });
    
    console.log('⚙️ Step 12: Viewing Settings page...');
    await page.click('text=Settings').catch(async () => {
      await page.goto('http://localhost:3002/settings');
    });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'demo-settings.png' });
    
    console.log('🎉 Demo completed successfully!');
    console.log('📸 Screenshots saved:');
    console.log('- demo-dashboard.png');
    console.log('- demo-customers-page.png');
    console.log('- demo-customer-1-added.png');
    console.log('- demo-customer-2-added.png');
    console.log('- demo-customer-3-added.png');
    console.log('- demo-search-results.png');
    console.log('- demo-dashboard-updated.png');
    console.log('- demo-analytics.png');
    console.log('- demo-ai-chat.png');
    console.log('- demo-settings.png');
    
    // Keep browser open for manual inspection
    console.log('🔍 Browser will stay open for manual inspection...');
    console.log('Press Ctrl+C to close when done.');
    
    // Wait indefinitely so you can inspect manually
    await new Promise(() => {});
    
  } catch (error) {
    console.error('❌ Demo failed:', error);
  } finally {
    await browser.close();
  }
}

runDemo();