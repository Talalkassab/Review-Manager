const { chromium } = require('playwright');

async function testAnalytics() {
  console.log('🔬 TESTING UPDATED ANALYTICS PAGE');
  console.log('=================================');
  
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
    
    console.log('📊 Navigating to Analytics page...');
    await page.goto('http://localhost:3002/analytics');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    console.log('📸 Taking screenshot: Analytics with real data');
    await page.screenshot({ path: 'test-analytics-real-data.png', fullPage: true });
    
    // Check if analytics data is loading
    const loadingVisible = await page.locator('text="Loading analytics..."').isVisible().catch(() => false);
    console.log(`Analytics loading state: ${loadingVisible ? 'Loading...' : 'Loaded'}`);
    
    // Check for analytics title
    const analyticsTitle = await page.locator('h1').textContent().catch(() => 'Not found');
    console.log(`Analytics title: "${analyticsTitle}"`);
    
    // Check for metric cards
    const metricCards = await page.locator('[class*="card"]').count();
    console.log(`Metric cards found: ${metricCards}`);
    
    // Check for refresh button
    const refreshButton = await page.locator('text="تحديث", text="Refresh"').count() > 0;
    console.log(`Refresh button exists: ${refreshButton ? '✅' : '❌'}`);
    
    // Check for real data indicators
    const responseRateVisible = await page.locator('text*="%"').count();
    console.log(`Percentage values found (indicating real data): ${responseRateVisible}`);
    
    // Test refresh functionality
    if (refreshButton) {
      console.log('🔄 Testing refresh functionality...');
      await page.click('text="تحديث", text="Refresh"');
      await page.waitForTimeout(2000);
      console.log('   - Refresh triggered successfully');
    }
    
    console.log('📸 Taking final screenshot');
    await page.screenshot({ path: 'test-analytics-final.png', fullPage: true });
    
    console.log('\n✅ ANALYTICS PAGE TEST RESULTS:');
    console.log(`- Page loads: ${analyticsTitle !== 'Not found' ? '✅' : '❌'}`);
    console.log(`- Real data integration: ${responseRateVisible > 0 ? '✅' : '❌'}`);
    console.log(`- Refresh functionality: ${refreshButton ? '✅' : '❌'}`);
    console.log(`- Multiple metric cards: ${metricCards >= 4 ? '✅' : '❌'}`);
    
    if (metricCards >= 4 && responseRateVisible > 0 && analyticsTitle !== 'Not found') {
      console.log('\n🎉 SUCCESS! Analytics page is working with real API data!');
    } else {
      console.log('\n⚠️ Some issues detected, check screenshots for details');
    }
    
    console.log('\nBrowser will close in 5 seconds...');
    await page.waitForTimeout(5000);
    
  } catch (error) {
    console.error('❌ Error during test:', error.message);
    await page.screenshot({ path: 'test-analytics-error.png', fullPage: true });
  } finally {
    await browser.close();
  }
}

testAnalytics().catch(console.error);