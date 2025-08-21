const { chromium } = require('playwright');

async function liveDemo() {
  console.log('🎬 LIVE DEMONSTRATION: Restaurant AI Customer Feedback Agent');
  console.log('====================================================');
  
  // Launch browser in visible mode with slower automation
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 2000,  // 2 seconds between actions
    args: ['--start-maximized']
  });
  
  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 }
  });
  
  const page = await context.newPage();
  
  try {
    console.log('\n🌐 Step 1: Opening the Restaurant AI application...');
    await page.goto('http://localhost:3002');
    await page.waitForLoadState('networkidle');
    
    console.log('📸 Taking screenshot: Application loaded');
    await page.screenshot({ path: 'live-demo-01-app-loaded.png', fullPage: true });
    
    // Wait to see the page
    await page.waitForTimeout(3000);
    
    console.log('\n🏠 Step 2: Exploring the Dashboard...');
    console.log('   - Viewing dashboard statistics');
    console.log('   - Checking recent feedback section');
    console.log('   - Looking at quick actions');
    
    await page.screenshot({ path: 'live-demo-02-dashboard.png', fullPage: true });
    await page.waitForTimeout(3000);
    
    console.log('\n👥 Step 3: Navigating to Customers page...');
    // Navigate to customers page
    await page.goto('http://localhost:3002/customers');
    await page.waitForLoadState('networkidle');
    
    console.log('📸 Taking screenshot: Customers page');
    await page.screenshot({ path: 'live-demo-03-customers-page.png', fullPage: true });
    await page.waitForTimeout(3000);
    
    console.log('\n➕ Step 4: Adding Customer #1 - Ahmed Hassan...');
    // Click Add Customer button
    const addButton = await page.locator('button:has-text("Add Customer"), button:has-text("إضافة عميل")').first();
    await addButton.click();
    await page.waitForTimeout(2000);
    
    console.log('📸 Taking screenshot: Add customer modal opened');
    await page.screenshot({ path: 'live-demo-04-add-modal.png', fullPage: true });
    
    // Fill the form
    console.log('   - Entering first name: Ahmed');
    await page.fill('input[id="first_name"]', 'Ahmed');
    await page.waitForTimeout(1000);
    
    console.log('   - Entering last name: Hassan');
    await page.fill('input[id="last_name"]', 'Hassan');
    await page.waitForTimeout(1000);
    
    console.log('   - Entering phone: +966501234567');
    await page.fill('input[id="phone_number"]', '+966501234567');
    await page.waitForTimeout(1000);
    
    console.log('   - Entering email: ahmed.hassan@gmail.com');
    await page.fill('input[id="email"]', 'ahmed.hassan@gmail.com');
    await page.waitForTimeout(1000);
    
    console.log('📸 Taking screenshot: Form filled');
    await page.screenshot({ path: 'live-demo-05-form-filled.png', fullPage: true });
    
    // Submit the form
    console.log('   - Saving customer...');
    const saveButton = await page.locator('button:has-text("Save"), button:has-text("حفظ")').first();
    await saveButton.click();
    
    // Wait for the customer to be added
    await page.waitForTimeout(4000);
    
    console.log('📸 Taking screenshot: Customer #1 added');
    await page.screenshot({ path: 'live-demo-06-customer-1-added.png', fullPage: true });
    
    console.log('\n➕ Step 5: Adding Customer #2 - Sarah Johnson...');
    await addButton.click();
    await page.waitForTimeout(1000);
    
    console.log('   - Entering first name: Sarah');
    await page.fill('input[id="first_name"]', 'Sarah');
    await page.waitForTimeout(800);
    
    console.log('   - Entering last name: Johnson');
    await page.fill('input[id="last_name"]', 'Johnson');
    await page.waitForTimeout(800);
    
    console.log('   - Entering phone: +966507654321');
    await page.fill('input[id="phone_number"]', '+966507654321');
    await page.waitForTimeout(800);
    
    console.log('   - Entering email: sarah.johnson@outlook.com');
    await page.fill('input[id="email"]', 'sarah.johnson@outlook.com');
    await page.waitForTimeout(800);
    
    // Set language to English
    await page.selectOption('select[id="preferred_language"]', 'en');
    await page.waitForTimeout(500);
    
    console.log('   - Saving customer...');
    await saveButton.click();
    await page.waitForTimeout(4000);
    
    console.log('📸 Taking screenshot: Customer #2 added');
    await page.screenshot({ path: 'live-demo-07-customer-2-added.png', fullPage: true });
    
    console.log('\n➕ Step 6: Adding Customer #3 - فاطمة محمد (Arabic)...');
    await addButton.click();
    await page.waitForTimeout(1000);
    
    console.log('   - Entering Arabic first name: فاطمة');
    await page.fill('input[id="first_name"]', 'فاطمة');
    await page.waitForTimeout(800);
    
    console.log('   - Entering Arabic last name: محمد');
    await page.fill('input[id="last_name"]', 'محمد');
    await page.waitForTimeout(800);
    
    console.log('   - Entering phone: +966512345678');
    await page.fill('input[id="phone_number"]', '+966512345678');
    await page.waitForTimeout(800);
    
    console.log('   - Entering email: fatima.mohammed@gmail.com');
    await page.fill('input[id="email"]', 'fatima.mohammed@gmail.com');
    await page.waitForTimeout(800);
    
    // Set language to Arabic
    await page.selectOption('select[id="preferred_language"]', 'ar');
    await page.waitForTimeout(500);
    
    console.log('   - Saving Arabic customer...');
    await saveButton.click();
    await page.waitForTimeout(4000);
    
    console.log('📸 Taking screenshot: Customer #3 (Arabic) added');
    await page.screenshot({ path: 'live-demo-08-customer-3-arabic.png', fullPage: true });
    
    console.log('\n🔍 Step 7: Testing search functionality...');
    const searchBox = await page.locator('input[placeholder*="Search"], input[placeholder*="بحث"]').first();
    
    console.log('   - Searching for "Ahmed"...');
    await searchBox.fill('Ahmed');
    await page.waitForTimeout(2000);
    
    console.log('📸 Taking screenshot: Search results for Ahmed');
    await page.screenshot({ path: 'live-demo-09-search-ahmed.png', fullPage: true });
    
    console.log('   - Searching for Arabic name "فاطمة"...');
    await searchBox.fill('فاطمة');
    await page.waitForTimeout(2000);
    
    console.log('📸 Taking screenshot: Search results for فاطمة');
    await page.screenshot({ path: 'live-demo-10-search-arabic.png', fullPage: true });
    
    // Clear search
    console.log('   - Clearing search to show all customers...');
    await searchBox.fill('');
    await page.waitForTimeout(2000);
    
    console.log('📸 Taking screenshot: All customers displayed');
    await page.screenshot({ path: 'live-demo-11-all-customers.png', fullPage: true });
    
    console.log('\n🏠 Step 8: Returning to Dashboard to see updated statistics...');
    await page.goto('http://localhost:3002');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    console.log('📸 Taking screenshot: Updated dashboard with real data');
    await page.screenshot({ path: 'live-demo-12-dashboard-updated.png', fullPage: true });
    
    console.log('\n📊 Step 9: Exploring Analytics page...');
    await page.goto('http://localhost:3002/analytics');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    console.log('📸 Taking screenshot: Analytics page');
    await page.screenshot({ path: 'live-demo-13-analytics.png', fullPage: true });
    
    console.log('\n🤖 Step 10: Checking AI Chat interface...');
    await page.goto('http://localhost:3002/ai-chat');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    console.log('📸 Taking screenshot: AI Chat page');
    await page.screenshot({ path: 'live-demo-14-ai-chat.png', fullPage: true });
    
    console.log('\n⚙️ Step 11: Viewing Settings configuration...');
    await page.goto('http://localhost:3002/settings');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    console.log('📸 Taking screenshot: Settings page');
    await page.screenshot({ path: 'live-demo-15-settings.png', fullPage: true });
    
    console.log('\n🎉 LIVE DEMONSTRATION COMPLETED SUCCESSFULLY!');
    console.log('==========================================');
    console.log('\n📸 Screenshots captured:');
    console.log('   • live-demo-01-app-loaded.png - Initial application');
    console.log('   • live-demo-02-dashboard.png - Dashboard overview');
    console.log('   • live-demo-03-customers-page.png - Customers page');
    console.log('   • live-demo-04-add-modal.png - Add customer modal');
    console.log('   • live-demo-05-form-filled.png - Form with data');
    console.log('   • live-demo-06-customer-1-added.png - Ahmed Hassan added');
    console.log('   • live-demo-07-customer-2-added.png - Sarah Johnson added');
    console.log('   • live-demo-08-customer-3-arabic.png - فاطمة محمد added');
    console.log('   • live-demo-09-search-ahmed.png - Search for Ahmed');
    console.log('   • live-demo-10-search-arabic.png - Search for فاطمة');
    console.log('   • live-demo-11-all-customers.png - All customers view');
    console.log('   • live-demo-12-dashboard-updated.png - Updated dashboard');
    console.log('   • live-demo-13-analytics.png - Analytics page');
    console.log('   • live-demo-14-ai-chat.png - AI Chat interface');
    console.log('   • live-demo-15-settings.png - Settings page');
    
    console.log('\n✅ DEMONSTRATED FEATURES:');
    console.log('   ✓ Real-time customer management');
    console.log('   ✓ Bilingual support (Arabic/English)');
    console.log('   ✓ Search functionality');
    console.log('   ✓ Form validation and submission');
    console.log('   ✓ Dashboard statistics updates');
    console.log('   ✓ Multi-page navigation');
    console.log('   ✓ Responsive user interface');
    
    console.log('\n🔧 Browser will remain open for manual inspection...');
    console.log('Press Ctrl+C in terminal to close the demo.');
    
    // Keep browser open for manual exploration
    await new Promise(() => {});
    
  } catch (error) {
    console.error('\n❌ Demo encountered an error:', error.message);
    console.log('\nTaking error screenshot...');
    await page.screenshot({ path: 'live-demo-error.png', fullPage: true });
  } finally {
    // Browser will stay open until manually closed
  }
}

console.log('🚀 Starting Live Demo...');
console.log('Make sure both frontend (localhost:3002) and backend (localhost:8000) are running!');
console.log('');

liveDemo().catch(console.error);