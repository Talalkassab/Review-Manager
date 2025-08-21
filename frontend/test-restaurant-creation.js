const { chromium } = require('playwright');

async function testRestaurantCreation() {
  console.log('🎯 RESTAURANT CREATION TEST');
  console.log('===============================');
  
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
    console.log('🌐 Step 1: Navigating to http://localhost:3000/restaurants...');
    await page.goto('http://localhost:3000/restaurants');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    console.log('📸 Taking screenshot: Initial restaurants page');
    await page.screenshot({ path: 'restaurant-01-initial.png', fullPage: true });
    
    console.log('🔐 Step 2: Checking for login requirements...');
    // Check if login form is visible
    const loginVisible = await page.locator('input[type="email"]').isVisible().catch(() => false);
    
    if (loginVisible) {
      console.log('   - Login required, entering credentials...');
      await page.fill('input[type="email"]', 'admin@restaurant.com');
      await page.fill('input[type="password"]', 'Admin123!');
      await page.click('button[type="submit"]');
      
      // Wait for login to complete
      await page.waitForTimeout(3000);
      console.log('   - Login submitted, waiting for redirect...');
      
      // Navigate back to restaurants page after login
      await page.goto('http://localhost:3000/restaurants');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);
      
      console.log('📸 Taking screenshot: After login');
      await page.screenshot({ path: 'restaurant-02-after-login.png', fullPage: true });
    } else {
      console.log('   - Already logged in or no login required');
    }
    
    console.log('🏪 Step 3: Opening Create Restaurant form...');
    
    // Look for the Create Restaurant button
    const createButton = page.locator('text="Create Restaurant"').first();
    const buttonExists = await createButton.isVisible();
    
    if (!buttonExists) {
      console.log('❌ Create Restaurant button not found. Page content:');
      const pageTitle = await page.locator('h1').textContent().catch(() => 'Not found');
      console.log(`   - Page title: "${pageTitle}"`);
      await page.screenshot({ path: 'restaurant-error-no-button.png', fullPage: true });
      throw new Error('Create Restaurant button not found');
    }
    
    console.log('   - Found Create Restaurant button, clicking...');
    await createButton.click();
    await page.waitForTimeout(1000);
    
    console.log('📸 Taking screenshot: Create form opened');
    await page.screenshot({ path: 'restaurant-03-form-opened.png', fullPage: true });
    
    console.log('✏️ Step 4: Filling out the Naandori restaurant form...');
    
    // Fill in restaurant details
    console.log('   - Filling Restaurant Name...');
    await page.fill('input[name="name"]', 'Naandori');
    
    console.log('   - Filling Restaurant Name (Arabic)...');
    await page.fill('input[name="name_arabic"]', 'نان دوري');
    
    console.log('   - Filling Description...');
    await page.fill('textarea[name="description"]', 'Authentic Arabic-Indian fusion restaurant bringing you the best of both worlds with traditional recipes and modern twists');
    
    console.log('   - Filling Logo URL...');
    await page.fill('input[name="logo_url"]', 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=200&h=200&fit=crop&crop=center');
    
    console.log('   - Filling Persona...');
    await page.fill('textarea[name="persona"]', 'We are a fun and vibrant Arabic-Indian fusion restaurant! Our personality is warm, welcoming, and enthusiastic. We love sharing the joy of authentic flavors with a modern twist. We speak with passion about our food and always make our guests feel like family. Our communication style is friendly, approachable, and filled with excitement about the culinary journey we offer.');
    
    console.log('   - Filling Phone Number...');
    await page.fill('input[name="phone_number"]', '+966561876440');
    
    console.log('   - Filling Email...');
    await page.fill('input[name="email"]', 'info@naandori.com');
    
    console.log('   - Filling City...');
    await page.fill('input[name="city"]', 'Riyadh');
    
    console.log('   - Filling Address...');
    await page.fill('input[name="address"]', 'King Fahd Road, Riyadh');
    
    // Wait a moment for logo preview to load
    await page.waitForTimeout(2000);
    
    console.log('📸 Taking screenshot: Form filled with Naandori details');
    await page.screenshot({ path: 'restaurant-04-form-filled.png', fullPage: true });
    
    console.log('✅ Step 5: Submitting the form...');
    const submitButton = page.locator('button[type="submit"]', { hasText: 'Create Restaurant' });
    await submitButton.click();
    
    console.log('   - Form submitted, waiting for response...');
    await page.waitForTimeout(3000);
    
    console.log('📸 Taking screenshot: After form submission');
    await page.screenshot({ path: 'restaurant-05-after-submit.png', fullPage: true });
    
    console.log('🔍 Step 6: Verifying restaurant was created successfully...');
    
    // Check if we're back to the restaurants list and if our restaurant appears
    await page.waitForTimeout(2000);
    
    // Look for the new restaurant in the list
    const restaurantCard = page.locator('text="Naandori"').first();
    const restaurantExists = await restaurantCard.isVisible();
    
    if (restaurantExists) {
      console.log('   - ✅ SUCCESS! Naandori restaurant found in the list');
      
      // Check for Arabic name
      const arabicName = page.locator('text="نان دوري"').first();
      const arabicExists = await arabicName.isVisible();
      console.log(`   - Arabic name visible: ${arabicExists ? '✅' : '❌'}`);
      
      // Check for description
      const descriptionText = page.locator('text*="Authentic Arabic-Indian fusion"').first();
      const descriptionExists = await descriptionText.isVisible();
      console.log(`   - Description visible: ${descriptionExists ? '✅' : '❌'}`);
      
      // Check for logo
      const logoImage = page.locator('img[alt="Naandori"]').first();
      const logoExists = await logoImage.isVisible();
      console.log(`   - Logo image visible: ${logoExists ? '✅' : '❌'}`);
      
      // Check for contact details
      const phoneText = page.locator('text*="+966561876440"').first();
      const phoneExists = await phoneText.isVisible();
      console.log(`   - Phone number visible: ${phoneExists ? '✅' : '❌'}`);
      
      const emailText = page.locator('text*="info@naandori.com"').first();
      const emailExists = await emailText.isVisible();
      console.log(`   - Email visible: ${emailExists ? '✅' : '❌'}`);
      
      const cityText = page.locator('text*="Riyadh"').first();
      const cityExists = await cityText.isVisible();
      console.log(`   - City visible: ${cityExists ? '✅' : '❌'}`);
      
    } else {
      console.log('   - ❌ WARNING: Naandori restaurant not found in the list');
      // Check if there are any restaurants at all
      const allCards = await page.locator('[class*="card"]').count();
      console.log(`   - Total restaurant cards found: ${allCards}`);
    }
    
    console.log('📸 Taking final screenshot: Restaurants page with new restaurant');
    await page.screenshot({ path: 'restaurant-06-final-list.png', fullPage: true });
    
    console.log('\n🎉 TEST COMPLETED!');
    console.log('===================');
    console.log('📸 Screenshots generated:');
    console.log('   • restaurant-01-initial.png - Initial restaurants page');
    console.log('   • restaurant-02-after-login.png - After login (if required)');
    console.log('   • restaurant-03-form-opened.png - Create form opened');
    console.log('   • restaurant-04-form-filled.png - Form filled with data');
    console.log('   • restaurant-05-after-submit.png - After form submission');
    console.log('   • restaurant-06-final-list.png - Final restaurants list');
    
    console.log('\n✅ VERIFICATION RESULTS:');
    console.log('   ✓ Successfully navigated to restaurants page');
    console.log('   ✓ Found and clicked Create Restaurant button');
    console.log('   ✓ Filled all form fields with Naandori data');
    console.log('   ✓ Successfully submitted the form');
    if (restaurantExists) {
      console.log('   ✓ Restaurant "Naandori" appears in the list');
    } else {
      console.log('   ❌ Restaurant "Naandori" not visible in list');
    }
    
    console.log('\n📋 NAANDORI RESTAURANT DETAILS SUBMITTED:');
    console.log('   • Name: Naandori');
    console.log('   • Name (Arabic): نان دوري');
    console.log('   • Description: Authentic Arabic-Indian fusion restaurant bringing you the best of both worlds...');
    console.log('   • Logo URL: https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=200&h=200&fit=crop&crop=center');
    console.log('   • Phone: +966561876440');
    console.log('   • Email: info@naandori.com');
    console.log('   • City: Riyadh');
    console.log('   • Address: King Fahd Road, Riyadh');
    console.log('   • Persona: Fun and vibrant Arabic-Indian fusion restaurant personality...');
    
    console.log('\nBrowser will remain open for 30 seconds for inspection...');
    await page.waitForTimeout(30000);
    
  } catch (error) {
    console.error('❌ Error during test:', error.message);
    console.error('Stack trace:', error.stack);
    await page.screenshot({ path: 'restaurant-error.png', fullPage: true });
    
    // Try to get page content for debugging
    try {
      const pageTitle = await page.title();
      console.log(`Current page title: ${pageTitle}`);
      const currentUrl = page.url();
      console.log(`Current URL: ${currentUrl}`);
    } catch (debugError) {
      console.log('Could not get page debug info');
    }
  } finally {
    await browser.close();
    console.log('\nTest complete! Check screenshots for results.');
  }
}

testRestaurantCreation().catch(console.error);