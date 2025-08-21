const { chromium } = require('playwright');

async function testFix() {
  console.log('🔧 TESTING API RESPONSE FIX');
  console.log('===========================');
  
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 1000
  });
  
  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 }
  });
  
  const page = await context.newPage();
  
  try {
    console.log('🌐 Loading application...');
    await page.goto('http://localhost:3002');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Login first
    const loginVisible = await page.locator('input[type="email"]').isVisible().catch(() => false);
    
    if (loginVisible) {
      console.log('🔐 Logging in...');
      await page.fill('input[type="email"]', 'admin@restaurant.com');
      await page.fill('input[type="password"]', 'Admin123!');
      await page.click('button[type="submit"]');
      await page.waitForTimeout(3000);
    }
    
    console.log('📸 Taking screenshot: After login');
    await page.screenshot({ path: 'test-fix-dashboard.png', fullPage: true });
    
    // Check for error messages
    const errorMessage = await page.locator('text="customers.filter is not a function"').count();
    console.log(`Filter error still present: ${errorMessage > 0 ? '❌' : '✅'}`);
    
    // Check for dashboard content
    const dashboardTitle = await page.locator('h1').textContent().catch(() => 'Not found');
    console.log(`Dashboard title: "${dashboardTitle}"`);
    
    // Check for stats cards
    const statsCards = await page.locator('[class*="card"]').count();
    console.log(`Stats cards found: ${statsCards}`);
    
    console.log('👥 Testing Customers page...');
    await page.goto('http://localhost:3002/customers');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    console.log('📸 Taking screenshot: Customers page');
    await page.screenshot({ path: 'test-fix-customers.png', fullPage: true });
    
    // Check for customers page content
    const customersTitle = await page.locator('h1').textContent().catch(() => 'Not found');
    console.log(`Customers title: "${customersTitle}"`);
    
    // Check for Add Customer button
    const addButtonExists = await page.locator('text="Add Customer", text="إضافة عميل"').count() > 0;
    console.log(`Add Customer button exists: ${addButtonExists ? '✅' : '❌'}`);
    
    // Check for error messages on customers page
    const customersError = await page.locator('text="customers.filter is not a function"').count();
    console.log(`Customers filter error: ${customersError > 0 ? '❌ Still present' : '✅ Fixed'}`);
    
    console.log('\n🎯 FIX TEST RESULTS:');
    console.log(`- Dashboard loads: ${dashboardTitle !== 'Not found' ? '✅' : '❌'}`);
    console.log(`- No filter errors: ${(errorMessage === 0 && customersError === 0) ? '✅' : '❌'}`);
    console.log(`- Add Customer button: ${addButtonExists ? '✅' : '❌'}`);
    
    if (addButtonExists && customersError === 0) {
      console.log('\n✨ SUCCESS! The API fix appears to be working!');
    } else {
      console.log('\n⚠️ Issue may still persist, check screenshots for details');
    }
    
    console.log('\nBrowser will close in 5 seconds...');
    await page.waitForTimeout(5000);
    
  } catch (error) {
    console.error('❌ Error during test:', error.message);
    await page.screenshot({ path: 'test-fix-error.png', fullPage: true });
  } finally {
    await browser.close();
  }
}

testFix().catch(console.error);