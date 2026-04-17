import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from dataclasses import dataclass, asdict, field
import pandas as pd
import argparse
import os
import sys

@dataclass
class Business:
    """holds business data"""
    name: str = None
    address: str = None
    domain: str = None
    website: str = None
    phone_number: str = None
    category: str = None
    location: str = None
    reviews_count: int = None
    reviews_average: float = None
    latitude: float = None
    longitude: float = None
    map_url: str = None
    status_hours: str = None
    
    def __hash__(self):
        """Make Business hashable for duplicate detection."""
        hash_fields = [self.name]
        if self.domain:
            hash_fields.append(f"domain:{self.domain}")
        if self.website:
            hash_fields.append(f"website:{self.website}")
        if self.phone_number:
            hash_fields.append(f"phone:{self.phone_number}")
        return hash(tuple(hash_fields))

@dataclass
class BusinessList:
    """holds list of Business objects, and save to both excel and csv"""
    business_list: list[Business] = field(default_factory=list)
    _seen_businesses: set = field(default_factory=set, init=False)
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    save_at = os.path.join('GMaps Data', today)
    os.makedirs(save_at, exist_ok=True)

    def add_business(self, business: Business):
        """Add a business to the list if it's not a duplicate based on key attributes"""
        business_hash = hash(business)
        if business_hash not in self._seen_businesses:
            self.business_list.append(business)
            self._seen_businesses.add(business_hash)
    
    def dataframe(self):
        """transform business_list to pandas dataframe"""
        return pd.json_normalize(
            (asdict(business) for business in self.business_list), sep="_"
        )

    def save_to_excel(self, filename):
        """saves pandas dataframe to excel (xlsx) file"""
        self.dataframe().to_excel(f"{self.save_at}/{filename}.xlsx", index=False)

    def save_to_csv(self, filename):
        """saves pandas dataframe to csv file"""
        self.dataframe().to_csv(f"{self.save_at}/{filename}.csv", index=False)

def extract_coordinates_from_url(url: str) -> tuple[float, float]:
    """helper function to extract coordinates from url"""
    try:
        coordinates = url.split('/@')[-1].split('/')[0]
        return float(coordinates.split(',')[0]), float(coordinates.split(',')[1])
    except Exception:
        return None, None

def dismiss_consent_popup(page):
    """Dismiss Google consent/cookie popup if it appears"""
    consent_selectors = [
        'button[aria-label="Accept all"]',
        'button[aria-label="Reject all"]',
        'button:has-text("Accept all")',
        'button:has-text("I agree")',
        'form[action*="consent"] button',
        '#L2AGLb',   # Google consent button ID
    ]
    for selector in consent_selectors:
        try:
            btn = page.locator(selector)
            if btn.count() > 0:
                btn.first.click(timeout=3000)
                page.wait_for_timeout(2000)
                print("  [Info] Dismissed consent popup.")
                return
        except Exception:
            continue

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--search", type=str)
    parser.add_argument("-t", "--total", type=int)
    args = parser.parse_args()
    
    if args.search:
        search_list = [args.search]
        
    if args.total:
        total = args.total
    else:
        # set to a large number to collect as much data as possible
        total = 1_000_000

    if not args.search:
        search_list = []
        input_file_name = 'input.txt'
        input_file_path = os.path.join(os.getcwd(), input_file_name)
        if os.path.exists(input_file_path):
            with open(input_file_path, 'r') as file:
                search_list = [line.strip() for line in file.readlines() if line.strip()]
                
        if len(search_list) == 0:
            print('Error occured: You must either pass the -s search argument, or add searches to input.txt')
            sys.exit()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(locale="en-GB")
        # Global default timeout - 60 seconds
        page.set_default_timeout(60000)

        print("  [Info] Navigating to Google Maps...")
        # Use 'commit' so we don't wait for all resources - just first response byte
        for attempt in range(3):
            try:
                page.goto("https://www.google.com/maps", timeout=90000, wait_until="commit")
                break
            except PlaywrightTimeoutError:
                print(f"  [Warn] goto attempt {attempt+1} timed out, retrying...")
                if attempt == 2:
                    print("  [Error] Could not load Google Maps after 3 attempts. Check your internet connection.")
                    browser.close()
                    sys.exit(1)
        # Now wait for the page to actually render
        try:
            page.wait_for_load_state("networkidle", timeout=60000)
        except PlaywrightTimeoutError:
            print("  [Warn] networkidle timed out, continuing anyway...")

        # Dismiss any consent/cookie popup first
        dismiss_consent_popup(page)
        page.wait_for_timeout(2000)

        business_list = BusinessList()

        for search_for_index, search_for in enumerate(search_list):
            print(f"-----\n{search_for_index} - {search_for}".strip())

            # Wait for the search box to be visible and fill it
            search_box = page.locator('//input[@name="q"]')
            search_box.wait_for(state="visible", timeout=60000)
            search_box.fill(search_for)
            page.wait_for_timeout(3000)

            page.keyboard.press("Enter")
            page.wait_for_timeout(5000)

            # Wait for results panel to load
            try:
                page.wait_for_selector(
                    '//a[contains(@href, "https://www.google.com/maps/place")]',
                    timeout=30000
                )
            except PlaywrightTimeoutError:
                print(f"  [Warn] No results found for: {search_for}. Skipping.")
                continue

            # scrolling to load maximum results
            page.hover('//a[contains(@href, "https://www.google.com/maps/place")]')

            previously_counted = 0
            no_change_streak = 0

            while True:
                page.mouse.wheel(0, 10000)
                page.wait_for_timeout(3000)

                current_count = page.locator(
                    '//a[contains(@href, "https://www.google.com/maps/place")]'
                ).count()

                if current_count >= total:
                    listings = page.locator(
                        '//a[contains(@href, "https://www.google.com/maps/place")]'
                    ).all()[:total]
                    listings = [listing.locator("xpath=..") for listing in listings]
                    print(f"Total Scraped: {len(listings)}")
                    break
                else:
                    if current_count == previously_counted:
                        no_change_streak += 1
                        if no_change_streak >= 3:
                            # Reached end of all listings
                            listings = page.locator(
                                '//a[contains(@href, "https://www.google.com/maps/place")]'
                            ).all()
                            print(f"Arrived at all available\nTotal Scraped: {len(listings)}")
                            break
                    else:
                        no_change_streak = 0
                        previously_counted = current_count
                        print(
                            f"Currently Scraped: {current_count}", end='\r'
                        )

            # scraping
            for idx, listing in enumerate(listings):
                try:                        
                    listing.click()
                    page.wait_for_timeout(2000)

                    name_attribute = 'h1.DUwDvf'
                    address_xpath = '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'
                    website_xpath = '//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]'
                    phone_number_xpath = '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'
                    review_count_xpath = '//div[@jsaction="pane.reviewChart.moreReviews"]//span'
                    reviews_average_xpath = '//div[@jsaction="pane.reviewChart.moreReviews"]//div[@role="img"]'
                                                           
                    business = Business()
                   
                    if name_value := page.locator(name_attribute).inner_text():
                        business.name = name_value.strip()
                    else:
                        business.name = ""

                    if page.locator(address_xpath).count() > 0:
                        business.address = page.locator(address_xpath).all()[0].inner_text()
                    else:
                        business.address = ""

                    if page.locator(website_xpath).count() > 0:
                        business.domain = page.locator(website_xpath).all()[0].inner_text()
                        business.website = f"https://www.{page.locator(website_xpath).all()[0].inner_text()}"
                    else:
                        business.website = ""

                    if page.locator(phone_number_xpath).count() > 0:
                        business.phone_number = page.locator(phone_number_xpath).all()[0].inner_text()
                    else:
                        business.phone_number = ""
                        
                    if page.locator(review_count_xpath).count() > 0:
                        business.reviews_count = int(page.locator(review_count_xpath).inner_text().split()[0].replace(',', '').strip())
                    else:
                        business.reviews_count = ""
                        
                    if page.locator(reviews_average_xpath).count() > 0:
                        business.reviews_average = float(page.locator(reviews_average_xpath).get_attribute('aria-label').split()[0].replace(',', '.').strip())
                    else:
                        business.reviews_average = ""
                
                    try:
                        business.status_hours = page.evaluate('''() => {
                            let h1 = document.querySelector('h1.DUwDvf');
                            let container = h1 ? (h1.closest('[role="main"]') || document.body) : document.body;
                            
                            let icon = container.querySelector('[aria-label*="open hours for the week"]');
                            if (icon && icon.parentElement) {
                                return icon.parentElement.innerText.trim().replace(/\\n/g, ' ');
                            }
                            
                            if (container.innerText.includes('Permanently closed')) return 'Permanently closed';
                            if (container.innerText.includes('Temporarily closed')) return 'Temporarily closed';
                            
                            return '';
                        }''')
                    except Exception:
                        business.status_hours = ""

                    business.category = search_for.split(' in ')[0].strip()
                    business.location = search_for.split(' in ')[-1].strip()
                    business.latitude, business.longitude = extract_coordinates_from_url(page.url)
                    business.map_url = page.url

                    business_list.add_business(business)
                    print(f"  [{idx+1}/{len(listings)}] Scraped: {business.name}", end='\r')
                except Exception as e:
                    print(f'  Error on listing {idx+1}: {e}', end='\r')
            
            print(f"\n  Done for '{search_for}'. Total unique businesses so far: {len(business_list.business_list)}")
            # output incrementally
            safe_filename = "Pokhara_Combined_Data"
            business_list.save_to_excel(safe_filename)
            business_list.save_to_csv(safe_filename)
            print(f"  Saved incrementally to GMaps Data/{business_list.today}/{safe_filename}.xlsx and .csv")

        print(f"\n  All queries finished! Total unique deduplicated businesses gathered: {len(business_list.business_list)}")
        browser.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f'Failed err: {e}')
