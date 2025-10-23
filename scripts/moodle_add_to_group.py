"""
Moodle Group Member Addition Script with Playwright
Uses session cookies to bypass SSO login

Preliminaries:

python3 -m pip install playwright
python3 -m playwright install chromium

Usage:

1) Customize:
- MOODLE_URL
- COURSE_ID
- CSV_FILE

2) Create a CSV file with the following format:
email,group
<email>,<group>
...

3) Create the groups in Moodle manually

4) Run the script

"""

from playwright.sync_api import sync_playwright
import time
import sys
import json
import os
import csv
from collections import defaultdict

class MoodleGroupManager:
    def __init__(self, moodle_url, cookies, headless=True):
        """
        Initialize the Moodle Group Manager
        
        Args:
            moodle_url: Base URL of your Moodle instance (e.g., 'https://moodle.example.com')
            cookies: List of cookie dictionaries to inject into the browser
                Example: [
                    {
                        'name': 'MoodleSession',
                        'value': 'your_session_value',
                        'domain': '.moodle.example.com',
                        'path': '/'
                    },
                    ...
                ]
            headless: Run browser in headless mode (default: True)
        """
        self.moodle_url = moodle_url
        self.cookies = cookies if isinstance(cookies, list) else [cookies]
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
    
    def start_browser(self):
        """Start the browser and inject all cookies"""
        print("Starting browser...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        
        # Create a new context (isolated browser session)
        self.context = self.browser.new_context()
        
        # Add all cookies
        self.context.add_cookies(self.cookies)
        
        # Create a new page
        self.page = self.context.new_page()
        print(f"Browser started with {len(self.cookies)} cookies injected!")
    
    def verify_authentication(self):
        """Verify that the session cookie is valid by checking if we're redirected to login"""
        print("Verifying authentication...")
        self.page.goto(self.moodle_url)
        self.page.wait_for_load_state('networkidle')
        time.sleep(1)
        
        # Check current URL - if we're on a login page, auth failed
        current_url = self.page.url.lower()
        
        # Check for login/SSO indicators in URL
        if any(indicator in current_url for indicator in ['login', 'sso', 'auth', 'signin']):
            print(f"✗ Authentication failed - redirected to login page")
            print(f"Current URL: {self.page.url}")
            return False
        
        # Check for login form on the page
        login_indicators = [
            'input[type="password"]',
            'button:has-text("Sign in")',
            'button:has-text("Login")',
            'a:has-text("Accedi con credenziali")',
        ]
        
        for indicator in login_indicators:
            try:
                element = self.page.query_selector(indicator)
                if element and element.is_visible():
                    print(f"✗ Authentication failed - login form detected")
                    return False
            except:
                continue
        
        # Check for logged-in indicators
        selectors_to_try = [
            '[data-region="user-menu"]',
            '.usermenu',
            '#user-menu-toggle',
            'a[href*="logout"]',
        ]
        
        for selector in selectors_to_try:
            try:
                element = self.page.wait_for_selector(selector, timeout=2000)
                if element:
                    print(f"✓ Authentication verified! (found: {selector})")
                    return True
            except:
                continue
        
        print("✗ Authentication could not be verified")
        return False
    
    def navigate_to_course_groups(self, course_id):
        """
        Navigate to the groups page of a specific course
        
        Args:
            course_id: The ID of the course
            
        Returns:
            True if navigation successful, False if redirected to login
        """
        print(f"Navigating to course {course_id} groups...")
        self.page.goto(f"{self.moodle_url}/group/index.php?id={course_id}")
        self.page.wait_for_load_state('networkidle')
        time.sleep(1)
        
        # Check if we got redirected to login
        current_url = self.page.url.lower()
        if any(indicator in current_url for indicator in ['login', 'sso', 'auth', 'signin']):
            print(f"✗ Redirected to login page - authentication failed")
            print(f"Current URL: {self.page.url}")
            return False
        
        # Check for login form
        password_field = self.page.query_selector('input[type="password"]')
        if password_field and password_field.is_visible():
            print(f"✗ Login form detected - authentication failed")
            return False
        
        return True
    
    def add_members_to_group(self, group_name, member_usernames):
        """
        Add members to a specific group
        
        Args:
            group_name: Name of the group to add members to
            member_usernames: List of usernames to add to the group
        """
        print(f"Adding members to group: {group_name}")
        
        try:
            # Wait for the groups dropdown to be available
            self.page.wait_for_selector('#groups', timeout=10000)
            
            # Get all available groups to help with debugging
            group_options = self.page.query_selector_all('#groups option')
            available_groups = [opt.inner_text() for opt in group_options]
            print(f"Available groups: {available_groups}")
            
            # Try to find and select the group (case-insensitive partial match)
            group_found = False
            for option in group_options:
                option_text = option.inner_text()
                if group_name.lower() in option_text.lower():
                    option_value = option.get_attribute('value')
                    self.page.select_option('#groups', value=option_value)
                    print(f"Selected group: {option_text}")
                    group_found = True
                    break
            
            if not group_found:
                print(f"✗ Group '{group_name}' not found in available groups!")
                return
            
            time.sleep(1)
            
            # Click "Add/remove users" button - try multiple selectors
            button_clicked = False
            button_selectors = [
                'input[value="Add/remove users"]',
                'button:has-text("Add/remove users")',
                'a:has-text("Add/remove users")',
                'input[type="submit"]',
                'button[type="submit"]',
            ]
            
            for selector in button_selectors:
                try:
                    element = self.page.wait_for_selector(selector, timeout=2000)
                    if element and element.is_visible():
                        print(f"Clicking button: {selector}")
                        element.click()
                        button_clicked = True
                        break
                except:
                    continue
            
            if not button_clicked:
                print("✗ Could not find 'Add/remove users' button")
                # Take a screenshot and save HTML to see what's on the page
                self.page.screenshot(path='groups_page.png')
                print("Screenshot saved as groups_page.png")
                
                # Save page HTML for inspection
                with open('groups_page.html', 'w', encoding='utf-8') as f:
                    f.write(self.page.content())
                print("Page HTML saved as groups_page.html")
                
                # List all buttons on the page
                all_buttons = self.page.query_selector_all('input[type="submit"], button, input[type="button"]')
                print(f"Found {len(all_buttons)} buttons on page:")
                for btn in all_buttons[:10]:  # Show first 10
                    btn_text = btn.get_attribute('value') or btn.inner_text() or btn.get_attribute('name')
                    print(f"  - {btn_text}")
                
                return
            
            self.page.wait_for_selector('#addselect', timeout=5000)
            time.sleep(1)
            
            # Check current members in the group
            current_members_select = self.page.query_selector('#removeselect')
            if current_members_select:
                current_members = self.page.query_selector_all('#removeselect option:not([disabled])')
                if current_members:
                    print(f"Current group members ({len(current_members)}):")
                    for member in current_members[:10]:
                        member_text = member.inner_text().strip()
                        if member_text:
                            print(f"  - {member_text}")
            
            # Check if there's a search box (for large user lists)
            has_search_box = self.page.query_selector('#addselect_searchtext') is not None
            if has_search_box:
                print("User list requires search (too many users to show all)")
            
            # Add each member
            for username in member_usernames:
                try:
                    print(f"  Searching for user: {username}")
                    
                    # Use the search box to filter users (re-query each time to avoid stale element)
                    if has_search_box:
                        # Re-query the search box element (it may be recreated by JavaScript)
                        search_box = self.page.wait_for_selector('#addselect_searchtext', timeout=5000)
                        
                        # Clear and type in search box
                        search_box.fill('')
                        time.sleep(0.3)
                        search_box.fill(username)
                        time.sleep(2.5)  # Wait longer for AJAX to populate results
                    
                    # Get all options from the potential members list
                    options = self.page.query_selector_all('#addselect option:not([disabled])')
                    print(f"  Found {len(options)} matching users")
                    
                    # If no results, check if user might already be in the group
                    if len(options) == 0:
                        print(f"  Note: User might already be in the group or not enrolled in the course")
                    
                    found = False
                    for option in options:
                        # Check all possible text sources
                        option_text = option.inner_text().strip()
                        option_value = option.get_attribute('value') or ''
                        option_label = option.get_attribute('label') or ''
                        
                        # Skip disabled options
                        if not option_value or option.get_attribute('disabled'):
                            continue
                        
                        # Show what we found
                        display_name = option_text or option_label or option_value
                        print(f"    - Found: {display_name}")
                        
                        # Select this option by value
                        self.page.select_option('#addselect', value=option_value)
                        
                        # Click the "Add" button
                        self.page.click('#add')
                        time.sleep(0.5)
                        
                        print(f"  ✓ Added: {display_name}")
                        found = True
                        break
                    
                    if not found:
                        print(f"  ✗ User not found: {username}")
                
                except Exception as e:
                    print(f"  ✗ Error adding {username}: {str(e)}")
            
            # Click "Back to groups" button
            self.page.click('input[value="Back to groups"]')
            time.sleep(1)
            
            print(f"Finished adding members to {group_name}")
        
        except Exception as e:
            print(f"Error in add_members_to_group: {str(e)}")
            # Take a screenshot for debugging
            self.page.screenshot(path='error_screenshot.png')
            print("Screenshot saved as error_screenshot.png")
    
    def close(self):
        """Close the browser"""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("Browser closed.")


def read_users_from_csv(csv_file):
    """
    Read users and their groups from a CSV file
    
    Args:
        csv_file: Path to CSV file with columns: email, group
        
    Returns:
        Dictionary mapping group names to lists of email addresses
    """
    groups_dict = defaultdict(list)
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Check if required columns exist
            if 'email' not in reader.fieldnames or 'group' not in reader.fieldnames:
                print(f"Error: CSV must have 'email' and 'group' columns")
                print(f"Found columns: {reader.fieldnames}")
                sys.exit(1)
            
            for row in reader:
                email = row['email'].strip()
                group = row['group'].strip()
                
                if email and group:
                    groups_dict[group].append(email)
        
        return dict(groups_dict)
    
    except FileNotFoundError:
        print(f"Error: CSV file '{csv_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV file: {str(e)}")
        sys.exit(1)


def extract_cookie_info(moodle_url):
    """
    Helper function to extract cookie information interactively
    This runs a browser where you can log in, then extracts the cookie
    Saves all cookies to cookies.json
    """
    print("Opening browser for cookie extraction...")
    print("Please log in to Moodle through SSO...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        page.goto(moodle_url)
        
        input("\nPress Enter AFTER you have logged in successfully...")
        
        # Get all cookies
        cookies = context.cookies()

        # Save all cookies to JSON file
        with open('cookies.json', 'w') as f:
            json.dump(cookies, f, indent=2)
        print(f"\n✓ All cookies saved to cookies.json ({len(cookies)} cookies)")
        
        browser.close()
    
    return  # Return to allow the main script to continue


# Example usage
if __name__ == "__main__":
    # Configuration
    MOODLE_URL = "https://my.luiss.it/"
    COURSE_ID = 1015  # Replace with your course ID
    CSV_FILE = "users_groups.csv"  # CSV file with email and group columns
    
    # Read users and groups from CSV
    print(f"Reading users from {CSV_FILE}...")
    groups_data = read_users_from_csv(CSV_FILE)
    
    print(f"\nFound {len(groups_data)} groups:")
    for group_name, members in groups_data.items():
        print(f"  - {group_name}: {len(members)} members")
    
    # Retry loop for authentication
    max_retries = 2
    for attempt in range(max_retries):
        # Check if cookies.json exists, if not, extract cookies
        if not os.path.exists('cookies.json'):
            print("\ncookies.json not found. Starting cookie extraction...")
            extract_cookie_info(MOODLE_URL)
        
        # Load cookies from file
        print("\nLoading cookies from cookies.json...")
        with open('cookies.json', 'r') as f:
            cookies = json.load(f)
        
        print(f"Loaded {len(cookies)} cookies from file")
        
        if not cookies:
            print("Error: No cookies available in cookies.json!")
            sys.exit(1)
        
        # Run the script with ALL cookies
        manager = MoodleGroupManager(MOODLE_URL, cookies, headless=True)
        
        try:
            manager.start_browser()
            
            if manager.verify_authentication():
                # Navigate to groups page once and check if auth is still valid
                if not manager.navigate_to_course_groups(COURSE_ID):
                    print("\n✗ Authentication failed when accessing course - cookies may be expired")
                    manager.close()
                    
                    if attempt < max_retries - 1:
                        print("Removing old cookies and re-extracting...")
                        if os.path.exists('cookies.json'):
                            os.remove('cookies.json')
                    else:
                        print("Maximum retry attempts reached. Exiting.")
                        sys.exit(1)
                    continue  # Retry the loop
                
                # Process each group
                for group_name, members in groups_data.items():
                    print(f"\n{'='*60}")
                    print(f"Processing group: {group_name}")
                    print(f"{'='*60}")
                    manager.add_members_to_group(group_name, members)
                    # add_members_to_group already clicks "Back to groups" button
                
                print("\n" + "="*60)
                print("✓ All operations completed successfully!")
                print("="*60)
                manager.close()
                break  # Success, exit the retry loop
            else:
                print("\n✗ Authentication failed - cookies may be expired")
                manager.close()
                
                if attempt < max_retries - 1:
                    print("Removing old cookies and re-extracting...")
                    # Remove old cookies file
                    if os.path.exists('cookies.json'):
                        os.remove('cookies.json')
                    # Loop will retry with fresh cookies
                else:
                    print("Maximum retry attempts reached. Exiting.")
                    sys.exit(1)
        
        except Exception as e:
            print(f"\n✗ Error occurred: {str(e)}")
            manager.close()
            if attempt < max_retries - 1:
                print("Retrying...")
                if os.path.exists('cookies.json'):
                    os.remove('cookies.json')
            else:
                sys.exit(1)