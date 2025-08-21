const { chromium } = require('playwright');
const fs = require('fs');

async function debugAnalysis() {
  console.log('🔍 COMPREHENSIVE DEBUG ANALYSIS');
  console.log('================================');
  
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 1500,
    args: ['--start-maximized']
  });
  
  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 }
  });
  
  const page = await context.newPage();
  
  // Debug log to capture console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log(`🚨 Browser Console Error: ${msg.text()}`);
    }
  });
  
  page.on('pageerror', error => {
    console.log(`🚨 Page Error: ${error.message}`);
  });
  
  const analysis = {
    pages: [],
    issues: [],
    apiCalls: []
  };
  
  try {
    console.log('\n📱 STEP 1: Loading Application');
    await page.goto('http://localhost:3002', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);
    
    // Capture initial load screenshot
    await page.screenshot({ path: 'debug-01-initial-load.png', fullPage: true });
    
    // Check for any error messages on page
    const errorElements = await page.locator('text=/error/i, text=/404/i, text=/failed/i').count();
    if (errorElements > 0) {
      analysis.issues.push('Error messages found on initial load');
      console.log('⚠️ Error messages detected on initial page load');
    }
    
    // Test login if needed
    console.log('\n🔐 STEP 2: Testing Login');
    const loginVisible = await page.locator('input[type="email"]').isVisible().catch(() => false);
    
    if (loginVisible) {
      console.log('   - Login form detected, attempting login...');
      await page.fill('input[type="email"]', 'admin@restaurant.com');
      await page.fill('input[type="password"]', 'Admin123!');
      await page.click('button[type="submit"]');
      await page.waitForTimeout(3000);
    } else {
      console.log('   - No login required or already logged in');
    }
    
    await page.screenshot({ path: 'debug-02-after-login.png', fullPage: true });
    
    // Define pages to test
    const pagesToTest = [
      { name: 'Dashboard', url: '/', selector: 'h1' },
      { name: 'Customers', url: '/customers', selector: 'h1' },
      { name: 'Analytics', url: '/analytics', selector: 'h1' },
      { name: 'AI Chat', url: '/ai-chat', selector: 'h1' },
      { name: 'Settings', url: '/settings', selector: 'h1' }
    ];
    
    // Test each page systematically
    for (let i = 0; i < pagesToTest.length; i++) {
      const pageInfo = pagesToTest[i];
      console.log(`\n📊 STEP ${i + 3}: Testing ${pageInfo.name} Page`);
      
      try {
        // Navigate to page
        await page.goto(`http://localhost:3002${pageInfo.url}`, { waitUntil: 'networkidle' });
        await page.waitForTimeout(2000);
        
        // Take screenshot
        const screenshotPath = `debug-${String(i + 3).padStart(2, '0')}-${pageInfo.name.toLowerCase()}.png`;
        await page.screenshot({ path: screenshotPath, fullPage: true });
        
        // Check page title/header
        const hasHeader = await page.locator(pageInfo.selector).count() > 0;
        
        // Check for loading states
        const hasLoader = await page.locator('text=/loading/i, .animate-spin, [data-loading]').count() > 0;
        
        // Check for error states
        const hasError = await page.locator('text=/error/i, text=/404/i, text=/failed/i, text=/unauthorized/i').count() > 0;
        
        // Check for empty states
        const hasNoData = await page.locator('text=/no data/i, text=/no customers/i, text=/empty/i').count() > 0;
        
        // Check for actual content
        const hasContent = await page.locator('div, p, table, card').count() > 10; // Basic content check
        
        // Network requests analysis
        const failedRequests = [];
        page.on('response', response => {
          if (!response.ok()) {
            failedRequests.push({
              url: response.url(),
              status: response.status(),
              statusText: response.statusText()
            });
          }
        });
        
        const pageAnalysis = {
          name: pageInfo.name,
          url: pageInfo.url,
          screenshot: screenshotPath,
          hasHeader,
          hasLoader,
          hasError,
          hasNoData,
          hasContent,
          issues: []
        };
        
        // Analyze issues
        if (!hasHeader) pageAnalysis.issues.push('Missing page header');
        if (hasLoader) pageAnalysis.issues.push('Page stuck in loading state');
        if (hasError) pageAnalysis.issues.push('Error messages displayed');
        if (!hasContent) pageAnalysis.issues.push('Insufficient content detected');
        if (hasNoData && pageInfo.name === 'Customers') pageAnalysis.issues.push('No customer data (may be expected)');
        
        analysis.pages.push(pageAnalysis);
        
        console.log(`   - Header present: ${hasHeader ? '✅' : '❌'}`);
        console.log(`   - Loading state: ${hasLoader ? '⏳' : '✅'}`);
        console.log(`   - Error state: ${hasError ? '❌' : '✅'}`);
        console.log(`   - Has content: ${hasContent ? '✅' : '❌'}`);
        console.log(`   - Screenshot: ${screenshotPath}`);
        
        if (pageAnalysis.issues.length > 0) {
          console.log(`   - Issues: ${pageAnalysis.issues.join(', ')}`);
        }
        
        // Special checks per page type
        if (pageInfo.name === 'Customers') {
          // Check for Add Customer button
          const hasAddButton = await page.locator('text=/add customer/i, text=/إضافة عميل/i').count() > 0;
          if (!hasAddButton) pageAnalysis.issues.push('Missing Add Customer button');
          
          // Check for customer list or empty state
          const customerCount = await page.locator('[data-testid="customer-card"], .customer-item').count();
          console.log(`   - Customer count: ${customerCount}`);
          
          // Test Add Customer form if button exists
          if (hasAddButton) {
            console.log('   - Testing Add Customer functionality...');
            await page.click('text=/add customer/i, text=/إضافة عميل/i');
            await page.waitForTimeout(1000);
            
            const modalVisible = await page.locator('input[id="first_name"]').isVisible().catch(() => false);
            if (modalVisible) {
              console.log('   - Add customer modal opened successfully ✅');
              await page.screenshot({ path: `debug-${String(i + 3).padStart(2, '0')}-${pageInfo.name.toLowerCase()}-modal.png` });
              
              // Close modal
              await page.press('Escape');
              await page.waitForTimeout(500);
            } else {
              pageAnalysis.issues.push('Add customer modal failed to open');
              console.log('   - Add customer modal failed to open ❌');
            }
          }
        }
        
        if (pageInfo.name === 'Dashboard') {
          // Check for stats cards
          const statsCards = await page.locator('[class*="card"], [class*="stat"]').count();
          console.log(`   - Stats cards found: ${statsCards}`);
          if (statsCards < 3) pageAnalysis.issues.push('Insufficient dashboard stats');
        }
        
      } catch (error) {
        console.log(`   - ERROR: ${error.message}`);
        pageAnalysis.issues.push(`Navigation error: ${error.message}`);
        analysis.issues.push(`Failed to load ${pageInfo.name}: ${error.message}`);
      }
    }
    
    // Final analysis
    console.log('\n📋 COMPREHENSIVE ANALYSIS REPORT');
    console.log('================================');
    
    analysis.pages.forEach(page => {
      console.log(`\n📄 ${page.name} Page:`);
      console.log(`   URL: ${page.url}`);
      console.log(`   Screenshot: ${page.screenshot}`);
      console.log(`   Status: ${page.issues.length === 0 ? '✅ WORKING' : '❌ HAS ISSUES'}`);
      
      if (page.issues.length > 0) {
        console.log(`   Issues:`);
        page.issues.forEach(issue => console.log(`     - ${issue}`));
      }
    });
    
    // Summary
    const workingPages = analysis.pages.filter(p => p.issues.length === 0).length;
    const totalPages = analysis.pages.length;
    
    console.log('\n🎯 SUMMARY');
    console.log(`Working Pages: ${workingPages}/${totalPages}`);
    console.log(`Total Issues Found: ${analysis.issues.length + analysis.pages.reduce((acc, p) => acc + p.issues.length, 0)}`);
    
    if (analysis.issues.length > 0) {
      console.log('\n🚨 CRITICAL ISSUES:');
      analysis.issues.forEach(issue => console.log(`   - ${issue}`));
    }
    
    console.log('\n📸 SCREENSHOTS GENERATED:');
    const screenshots = analysis.pages.map(p => p.screenshot);
    screenshots.unshift('debug-01-initial-load.png', 'debug-02-after-login.png');
    screenshots.forEach(screenshot => console.log(`   - ${screenshot}`));
    
    // Keep browser open for manual inspection
    console.log('\n🔍 Browser will remain open for manual inspection...');
    console.log('Press Ctrl+C to close when done.');
    
    // Wait indefinitely for manual inspection
    await new Promise(() => {});
    
  } catch (error) {
    console.error('\n💥 CRITICAL ERROR:', error);
    await page.screenshot({ path: 'debug-error.png', fullPage: true });
  } finally {
    // Don't close browser automatically - let user inspect
  }
}

console.log('🚀 Starting comprehensive debug analysis...');
console.log('This will systematically test all pages and identify issues.');
debugAnalysis().catch(console.error);