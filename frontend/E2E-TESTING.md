# E2E Testing with Playwright

## Customer Visit Creation Test

This test suite automates the complete customer visit creation workflow through the web interface.

### Test Scenarios

1. **Main Test**: Create a customer visit with the following specifications:
   - Phone number: +966561876440
   - Leave name fields empty (tests "Dear Customer" functionality)
   - Select today's date as visit date
   - Use default restaurant (Naandori - hardcoded in API)
   - Arabic language preference
   - Party size: 1 (dine-in)

2. **Validation Test**: Tests form validation by submitting empty required fields

3. **Debug Test**: Same as main test but takes screenshots at each step

### Prerequisites

1. **Backend Server**: Ensure the backend server is running on `localhost:8000`
2. **Frontend Server**: Ensure the frontend is running on `localhost:3000`
3. **Authentication**: You may need to be logged in to access the customers page

### Running the Tests

#### Basic test run
```bash
npm run test:e2e
```

#### Run with browser UI (see test execution visually)
```bash
npm run test:e2e:ui
```

#### Run in headed mode (see browser window)
```bash
npm run test:e2e:headed
```

#### Debug mode (pause on each action)
```bash
npm run test:e2e:debug
```

#### Direct Playwright commands
```bash
# Run all tests
npx playwright test customer-visit-test.js

# Run specific test
npx playwright test customer-visit-test.js -g "should create a customer visit"

# Run with UI mode
npx playwright test customer-visit-test.js --ui

# Run in debug mode
npx playwright test customer-visit-test.js --debug

# Run with specific browser
npx playwright test customer-visit-test.js --project=chromium
```

### Test Steps Breakdown

The main test performs these steps:

1. **Navigation**: Navigate to the customer management page (`/customers`)
2. **Form Opening**: Click the "Add Customer" button to open the form modal
3. **Data Entry**: Fill the form with:
   - Unique customer number (generated with timestamp)
   - Phone number: +966561876440
   - Empty first name and last name (testing "Dear Customer")
   - Today's date and time for visit
   - Arabic language preference
4. **Submission**: Submit the form and wait for processing
5. **Verification**: Verify the customer appears in the list with correct data
6. **WhatsApp Test**: Try to send a WhatsApp message to the new customer

### Expected Behavior

- Customer should be created successfully
- Customer should appear in the list as "Customer #[generated_number]" since names are empty
- Phone number +966561876440 should be displayed
- Visit date should show today's date
- WhatsApp button should be available and functional

### Debugging

If tests fail:

1. **Screenshots**: Check the `test-results` folder for failure screenshots
2. **Debug Mode**: Run with `--debug` flag to step through manually
3. **Console Logs**: Check browser console for JavaScript errors
4. **Network**: Verify API calls are successful in browser dev tools

### Debug Screenshots

The debug test creates these screenshots:
- `debug-01-customers-page.png` - Initial customers page
- `debug-02-form-opened.png` - Add customer form opened
- `debug-03-form-filled.png` - Form filled with data
- `debug-04-after-submit.png` - After form submission

### Customization

To modify the test:

1. **Phone Number**: Change the phone number in the test file
2. **Restaurant**: Modify the hardcoded restaurant ID in the API client
3. **Additional Fields**: Add more form fields as needed
4. **Validation**: Add more validation scenarios

### Troubleshooting

**Common Issues:**

1. **Server not running**: Ensure both backend and frontend servers are running
2. **Authentication required**: You may need to implement login flow in the test
3. **Element selectors**: If UI changes, update the element selectors in the test
4. **Timing issues**: Adjust wait times if elements load slowly

**Restaurant Selection:**

Note: The current implementation hardcodes the restaurant ID in the API client. If you need to test restaurant selection:

1. Modify the customer form to include restaurant selection
2. Update the test to select "Naandori" restaurant
3. Remove the hardcoded restaurant ID from the API client