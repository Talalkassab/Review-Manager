const { chromium } = require('playwright');

async function quickDebug() {
  console.log('🔍 QUICK DEBUG ANALYSIS');
  console.log('=======================');
  
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 1000,
    args: ['--start-maximized']
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
    
    console.log('📸 Taking screenshot of Dashboard...');
    await page.screenshot({ path: 'debug-dashboard.png', fullPage: true });
    
    // Check for errors in page content
    const errorText = await page.textContent('body');
    if (errorText.includes('404') || errorText.includes('Error')) {
      console.log('⚠️ Error content detected in dashboard');
    } else {
      console.log('✅ Dashboard appears to be working');
    }
    
    console.log('📊 Testing Customers page...');
    await page.goto('http://localhost:3002/customers');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    console.log('📸 Taking screenshot of Customers page...');
    await page.screenshot({ path: 'debug-customers.png', fullPage: true });
    
    // Check for Add Customer button
    const addButtonExists = await page.locator('text="Add Customer", text="إضافة عميل"').count() > 0;
    console.log(`Add Customer button exists: ${addButtonExists ? '✅' : '❌'}`);
    
    // Check for customer content
    const hasContent = await page.locator('h1').count() > 0;
    console.log(`Page has proper header: ${hasContent ? '✅' : '❌'}`);
    
    const customersPageText = await page.textContent('body');
    if (customersPageText.includes('404') || customersPageText.includes('Error')) {
      console.log('⚠️ Error content detected in customers page');
    } else {
      console.log('✅ Customers page appears to be working');
    }
    
    console.log('\n📋 QUICK ANALYSIS COMPLETE');
    console.log('Screenshots saved:');
    console.log('- debug-dashboard.png');
    console.log('- debug-customers.png');
    
    // Keep browser open for 10 seconds for manual inspection
    console.log('\nBrowser will close in 10 seconds...');
    await page.waitForTimeout(10000);
    
  } catch (error) {
    console.error('❌ Error during debug:', error.message);
    await page.screenshot({ path: 'debug-error-state.png', fullPage: true });
  } finally {
    await browser.close();
  }
}

quickDebug().catch(console.error);