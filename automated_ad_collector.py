#!/usr/bin/env python3
"""
Automated Ad Collector
Automatically scrolls through pages, collects all ads, and moves to next pages.
No human intervention required.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
import time
import csv
from datetime import datetime
import os


class AutomatedAdCollector:
    def __init__(self, headless: bool = False, wait_timeout: int = 15, csv_filename: str = None):
        """
        Initialize the Automated Ad Collector.
        
        Args:
            headless: Run browser in headless mode
            wait_timeout: Timeout for WebDriverWait in seconds
            csv_filename: Custom CSV filename (optional)
        """
        self.wait_timeout = wait_timeout
        self.driver = None
        self.headless = headless
        
        # Use provided filename or default to a single persistent file
        if csv_filename:
            self.csv_filename = csv_filename
        else:
            self.csv_filename = "ad_data_collection.csv"
        
        self.fieldnames = ['page_url', 'advertiser', 'ad_tag', 'headline', 'body', 'image_src', 'destination_url', 'collected_at', 'context', 'page_number']
        self.total_ads_collected = 0
        self.current_page = 1
        
        # Initialize CSV file
        self._initialize_csv()
    
    def _initialize_csv(self):
        """Initialize CSV file with headers if it doesn't exist."""
        if not os.path.exists(self.csv_filename):
            with open(self.csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
                writer.writeheader()
            print(f"Created new CSV file: {self.csv_filename}")
    
    def create_driver(self, headless=False):
        """Create a Chrome driver with proper configuration."""
        chrome_options = Options()
        effective_headless = bool(headless or getattr(self, "headless", False))
        if effective_headless:
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--lang=en-US,en;q=0.9")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Auto-allow notifications and disable popups
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        
        # Prefs to auto-allow notifications
        prefs = {
            "profile.default_content_setting_values.notifications": 1,  # Allow notifications
            "profile.default_content_setting_values.popups": 0,  # Block popups
            "profile.default_content_setting_values.geolocation": 1,  # Allow location
            "profile.default_content_setting_values.media_stream": 2,  # Block camera/mic
        }
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        return webdriver.Chrome(options=chrome_options)
    
    def handle_popups_and_notifications(self):
        """Handle any popups, notifications, or cookie banners that might appear."""
        try:
            # Skip these unwanted elements (social media buttons, etc.)
            skip_texts = ['Share', 'share', 'Follow', 'follow', 'Like', 'like', 'Comment', 'comment', 'Reply', 'reply', 'Subscribe', 'subscribe']
            
            # Only handle actual notification prompts and cookie banners
            # Look for specific notification-related text patterns
            notification_patterns = [
                "wants to",
                "Show notifications",
                "Allow notifications",
                "Block notifications",
                "Enable notifications",
                "Receive notifications"
            ]
            
            # Check for actual notification prompts first
            for pattern in notification_patterns:
                try:
                    xpath = f"//*[contains(text(), '{pattern}')]"
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    
                    for element in elements:
                        try:
                            # Look for Allow button near this text
                            parent = element.find_element(By.XPATH, "./ancestor::*[position()<=3]")
                            allow_buttons = parent.find_elements(By.XPATH, ".//button[contains(text(), 'Allow') or contains(text(), 'allow')]")
                            
                            for button in allow_buttons:
                                if button.is_displayed() and button.is_enabled():
                                    button_text = button.text or button.get_attribute('aria-label') or ""
                                    if not any(skip_text in button_text for skip_text in skip_texts):
                                        print(f"    Clicking notification Allow button: {button_text}")
                                        button.click()
                                        time.sleep(1)
                                        break
                        except:
                            continue
                except:
                    continue
            
            # Fallback to general selectors for other popups
            notification_selectors = [
                "button[aria-label*='Allow']",
                "button[aria-label*='allow']",
                "button:contains('Allow')",
                "button:contains('allow')",
                "button:contains('Accept')",
                "button:contains('accept')",
                "button:contains('OK')",
                "button:contains('ok')",
                "button:contains('Yes')",
                "button:contains('yes')",
                "[data-testid*='allow']",
                "[data-testid*='accept']",
                ".notification-allow",
                ".popup-allow",
                ".cookie-accept",
                ".consent-accept"
            ]
            
            for selector in notification_selectors:
                try:
                    if ":contains(" in selector:
                        # Use XPath for text-based selectors
                        xpath = f"//{selector.split(':')[0]}[contains(text(), '{selector.split('(')[1].split(')')[0]}')]"
                        elements = self.driver.find_elements(By.XPATH, xpath)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        try:
                            if element.is_displayed() and element.is_enabled():
                                element_text = element.text or element.get_attribute('aria-label') or ""
                                
                                # Skip unwanted elements
                                if any(skip_text in element_text for skip_text in skip_texts):
                                    continue
                                
                                print(f"    Clicking notification/popup button: {element_text}")
                                element.click()
                                time.sleep(1)
                                break
                        except:
                            continue
                except:
                    continue
            
            # Handle cookie banners
            cookie_selectors = [
                "button:contains('Accept All')",
                "button:contains('Accept all')",
                "button:contains('Accept Cookies')",
                "button:contains('I Accept')",
                "button:contains('Agree')",
                "button:contains('Continue')",
                ".cookie-accept-all",
                ".consent-accept-all",
                "[data-testid*='cookie-accept']",
                "[data-testid*='consent-accept']"
            ]
            
            for selector in cookie_selectors:
                try:
                    if ":contains(" in selector:
                        xpath = f"//{selector.split(':')[0]}[contains(text(), '{selector.split('(')[1].split(')')[0]}')]"
                        elements = self.driver.find_elements(By.XPATH, xpath)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        try:
                            if element.is_displayed() and element.is_enabled():
                                element_text = element.text or element.get_attribute('aria-label') or ""
                                
                                # Skip unwanted elements
                                if any(skip_text in element_text for skip_text in skip_texts):
                                    continue
                                
                                print(f"    Clicking cookie banner button: {element_text}")
                                element.click()
                                time.sleep(1)
                                break
                        except:
                            continue
                except:
                    continue
            
            # Handle close buttons for any remaining popups
            close_selectors = [
                "button[aria-label*='Close']",
                "button[aria-label*='close']",
                "button:contains('×')",
                "button:contains('✕')",
                "button:contains('Close')",
                "button:contains('close')",
                ".close-button",
                ".popup-close",
                ".modal-close",
                "[data-testid*='close']"
            ]
            
            for selector in close_selectors:
                try:
                    if ":contains(" in selector:
                        xpath = f"//{selector.split(':')[0]}[contains(text(), '{selector.split('(')[1].split(')')[0]}')]"
                        elements = self.driver.find_elements(By.XPATH, xpath)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        try:
                            if element.is_displayed() and element.is_enabled():
                                element_text = element.text or element.get_attribute('aria-label') or ""
                                
                                # Skip unwanted elements
                                if any(skip_text in element_text for skip_text in skip_texts):
                                    continue
                                
                                print(f"    Clicking close button: {element_text}")
                                element.click()
                                time.sleep(1)
                                break
                        except:
                            continue
                except:
                    continue
                    
        except Exception as e:
            print(f"    Error handling popups: {e}")

    def scroll_and_load_content(self, max_scrolls: int = 10, scroll_delay: int = 3):
        """
        Scroll through the page to load all content and ads.
        
        Args:
            max_scrolls: Maximum number of scroll operations
            scroll_delay: Delay between scrolls in seconds
        """
        print(f"  Scrolling through page to load content...")
        
        # Handle any popups or notifications first
        self.handle_popups_and_notifications()
        
        for i in range(max_scrolls):
            # Get current scroll position
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for new content to load
            time.sleep(scroll_delay)

            # Nudge lazy-loaded ad slots to render
            try:
                self.driver.execute_script("window.dispatchEvent(new Event('scroll'));")
            except Exception:
                pass
            time.sleep(1.2)

            # Handle any popups that might have appeared
            self.handle_popups_and_notifications()
            
            # Check if new content loaded
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            print(f"    Scroll {i+1}/{max_scrolls}: Height changed from {last_height} to {new_height}")
            
            # If no new content loaded, we might be at the bottom
            if new_height == last_height:
                print(f"    No new content loaded, trying a few more scrolls...")
                # Try a few more scrolls in case content loads slowly
                for j in range(3):
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    # Handle popups during additional scrolls
                    self.handle_popups_and_notifications()
                break
        
        # Scroll back to top
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
    
    def collect_ads_from_current_page(self):
        """Collect all ads from the current page."""
        print(f"  Collecting ads from page {self.current_page}...")
        ads_found = []
        
        try:
            # Wait for page to load
            WebDriverWait(self.driver, self.wait_timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait for dynamic content
            time.sleep(6)
            
            # Scroll to load all content
            self.scroll_and_load_content()
            
            # Collect ads from mspai iframes
            mspai_ads = self._collect_ads_from_mspai_iframes()
            ads_found.extend(mspai_ads)
            
            # Collect ads from other iframes
            other_ads = self._collect_ads_from_other_iframes()
            ads_found.extend(other_ads)
            
            # Collect ads from main page
            main_ads = self._collect_ads_from_main_page()
            ads_found.extend(main_ads)
            
            # Remove duplicates
            unique_ads = self._remove_duplicates(ads_found)
            
            # Add page number to each ad
            for ad in unique_ads:
                ad['page_number'] = self.current_page
            
            print(f"  Found {len(unique_ads)} unique ads on page {self.current_page}")
            
            return unique_ads
            
        except Exception as e:
            print(f"  Error collecting ads from page {self.current_page}: {e}")
            return []
    
    def _collect_ads_from_mspai_iframes(self):
        """Collect ads from mspai-nova-native iframes."""
        ads_found = []
        
        try:
            # Look for mspai-nova-native iframes
            mspai_iframes = self.driver.find_elements(By.CSS_SELECTOR, "iframe.mspai-nova-native")
            print(f"    Found {len(mspai_iframes)} mspai-nova-native iframes")
            
            for i, iframe in enumerate(mspai_iframes):
                try:
                    print(f"    Processing mspai iframe {i+1}...")
                    self.driver.switch_to.frame(iframe)
                    
                    # Wait for iframe content
                    time.sleep(2)
                    
                    # Look for click-through links
                    click_through_links = self.driver.find_elements(By.CSS_SELECTOR, "a[class*='click-through']")
                    print(f"      Found {len(click_through_links)} click-through links")
                    
                    for j, link in enumerate(click_through_links):
                        try:
                            ad_data = self._extract_ad_data_from_link(link, f"mspai_iframe_{i+1}")
                            if ad_data:
                                ads_found.append(ad_data)
                        except Exception as e:
                            print(f"      Error processing link {j+1}: {e}")
                    
                    # Look for ad containers
                    ad_containers = self.driver.find_elements(By.CSS_SELECTOR, ".ad-card-container")
                    for j, container in enumerate(ad_containers):
                        try:
                            ad_data = self._extract_ad_data_from_div(container, f"mspai_iframe_{i+1}")
                            if ad_data:
                                ads_found.append(ad_data)
                        except Exception as e:
                            continue
                    
                    self.driver.switch_to.default_content()
                    
                except Exception as e:
                    print(f"    Error processing mspai iframe {i+1}: {e}")
                    try:
                        self.driver.switch_to.default_content()
                    except:
                        pass
                        
        except Exception as e:
            print(f"    Error collecting from mspai iframes: {e}")
            try:
                self.driver.switch_to.default_content()
            except:
                pass
        
        return ads_found
    
    def _collect_ads_from_other_iframes(self):
        """Collect ads from other iframes."""
        ads_found = []
        
        try:
            self.driver.switch_to.default_content()
            all_iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            
            for i, iframe in enumerate(all_iframes):
                try:
                    classes = iframe.get_attribute("class") or ""
                    if "mspai" not in classes.lower():
                        print(f"    Processing other iframe {i+1}...")
                        self.driver.switch_to.frame(iframe)
                        
                        # Look for ad containers
                        ad_containers = self.driver.find_elements(By.CSS_SELECTOR, ".ad-card-container")
                        for j, container in enumerate(ad_containers):
                            try:
                                ad_data = self._extract_ad_data_from_div(container, f"other_iframe_{i+1}")
                                if ad_data:
                                    ads_found.append(ad_data)
                            except Exception as e:
                                continue
                        
                        self.driver.switch_to.default_content()
                        
                except Exception as e:
                    print(f"    Error processing other iframe {i+1}: {e}")
                    try:
                        self.driver.switch_to.default_content()
                    except:
                        pass
                        
        except Exception as e:
            print(f"    Error collecting from other iframes: {e}")
            try:
                self.driver.switch_to.default_content()
            except:
                pass
        
        return ads_found
    
    def _collect_ads_from_main_page(self):
        """Collect ads from main page elements."""
        ads_found = []
        
        try:
            self.driver.switch_to.default_content()
            
            # Look for various ad selectors
            ad_selectors = [
                ".ad-card-container",
                "[class*='ad-card']",
                "[class*='ad-container']",
                "[class*='advertisement']",
                "[class*='sponsored']",
                "[class*='promo']"
            ]
            
            for selector in ad_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        try:
                            ad_data = self._extract_ad_data_from_div(element, "main_page")
                            if ad_data:
                                ads_found.append(ad_data)
                        except Exception as e:
                            continue
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"    Error collecting from main page: {e}")
        
        return ads_found
    
    def _extract_ad_data_from_link(self, link_element, context: str):
        """Extract ad data from a click-through link element."""
        try:
            ad_data = {
                'page_url': self.driver.current_url,
                'advertiser': '',
                'ad_tag': '',
                'headline': '',
                'body': '',
                'image_src': '',
                'destination_url': link_element.get_attribute("href") or "",
                'collected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'context': context
            }
            
            # Look for headline
            try:
                headline_elem = link_element.find_element(By.CSS_SELECTOR, ".ad-headline, h1, h2, h3, h4, h5, h6")
                ad_data['headline'] = headline_elem.text.strip()
            except:
                ad_data['headline'] = link_element.text.strip()
            
            # Look for image
            try:
                img_elem = link_element.find_element(By.CSS_SELECTOR, ".ad-foreground, img")
                ad_data['image_src'] = img_elem.get_attribute("src") or ""
            except:
                pass
            
            # Look for advertiser
            try:
                advertiser_elem = link_element.find_element(By.CSS_SELECTOR, ".ad-advertiser")
                ad_data['advertiser'] = advertiser_elem.text.strip()
            except:
                pass
            
            # Look for ad tag
            try:
                ad_tag_elem = link_element.find_element(By.CSS_SELECTOR, ".ad-tag")
                ad_data['ad_tag'] = ad_tag_elem.text.strip()
            except:
                pass
            
            # Look for body text
            try:
                body_elem = link_element.find_element(By.CSS_SELECTOR, ".ad-body, p")
                ad_data['body'] = body_elem.text.strip()
            except:
                pass
            
            # Check if we got meaningful data
            if not any([ad_data['headline'], ad_data['image_src'], ad_data['destination_url']]):
                return None
            
            return ad_data
            
        except Exception as e:
            return None
    
    def _extract_ad_data_from_div(self, div_element, context: str):
        """Extract ad data from a div element."""
        try:
            ad_data = {
                'page_url': self.driver.current_url,
                'advertiser': '',
                'ad_tag': '',
                'headline': '',
                'body': '',
                'image_src': '',
                'destination_url': '',
                'collected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'context': context
            }
            
            # Extract headline
            try:
                headline_elem = div_element.find_element(By.CSS_SELECTOR, ".ad-headline, h1, h2, h3, h4, h5, h6")
                ad_data['headline'] = headline_elem.text.strip()
            except:
                pass
            
            # Extract image
            try:
                img_elem = div_element.find_element(By.CSS_SELECTOR, ".ad-foreground, img")
                ad_data['image_src'] = img_elem.get_attribute("src") or ""
            except:
                pass
            
            # Extract destination URL
            try:
                link_elem = div_element.find_element(By.CSS_SELECTOR, "a")
                ad_data['destination_url'] = link_elem.get_attribute("href") or ""
            except:
                pass
            
            # Extract advertiser
            try:
                advertiser_elem = div_element.find_element(By.CSS_SELECTOR, ".ad-advertiser")
                ad_data['advertiser'] = advertiser_elem.text.strip()
            except:
                pass
            
            # Extract ad tag
            try:
                ad_tag_elem = div_element.find_element(By.CSS_SELECTOR, ".ad-tag")
                ad_data['ad_tag'] = ad_tag_elem.text.strip()
            except:
                pass
            
            # Extract body
            try:
                body_elem = div_element.find_element(By.CSS_SELECTOR, ".ad-body, p")
                ad_data['body'] = body_elem.text.strip()
            except:
                pass
            
            # Check if we got meaningful data
            if not any([ad_data['headline'], ad_data['image_src'], ad_data['destination_url']]):
                return None
            
            return ad_data
            
        except Exception as e:
            return None
    
    def _remove_duplicates(self, ads_data):
        """Remove duplicate ads based on headline and image source."""
        seen = set()
        unique_ads = []
        
        for ad in ads_data:
            key = (ad.get('headline', ''), ad.get('image_src', ''))
            if key not in seen and key != ('', ''):
                seen.add(key)
                unique_ads.append(ad)
        
        return unique_ads
    
    def save_ads_to_csv(self, ads_data):
        """Save ads data to CSV file (append mode)."""
        if not ads_data:
            return
        
        try:
            with open(self.csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
                writer.writerows(ads_data)
            
            self.total_ads_collected += len(ads_data)
            print(f"  Saved {len(ads_data)} ads to CSV (Total: {self.total_ads_collected})")
            
        except Exception as e:
            print(f"  Error saving to CSV: {e}")
    
    def find_next_page_button(self):
        """Find the next page button or link."""
        try:
            # Common next page selectors
            next_selectors = [
                "a[aria-label*='next']",
                "a[aria-label*='Next']",
                "button[aria-label*='next']",
                "button[aria-label*='Next']",
                "a[class*='next']",
                "button[class*='next']",
                "a[class*='pagination']",
                "button[class*='pagination']",
                "a[href*='page']",
                "a[href*='p=']",
                "button:contains('Next')",
                "button:contains('next')",
                "a:contains('Next')",
                "a:contains('next')",
                "a:contains('More')",
                "a:contains('more')",
                "button:contains('More')",
                "button:contains('more')"
            ]
            
            for selector in next_selectors:
                try:
                    if ":contains(" in selector:
                        # Use XPath for text-based selectors
                        xpath = f"//{selector.split(':')[0]}[contains(text(), '{selector.split('(')[1].split(')')[0]}')]"
                        elements = self.driver.find_elements(By.XPATH, xpath)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    if elements:
                        # Check if the element is visible and clickable
                        for element in elements:
                            try:
                                if element.is_displayed() and element.is_enabled():
                                    return element
                            except:
                                continue
                except:
                    continue
            
            return None
            
        except Exception as e:
            print(f"    Error finding next page button: {e}")
            return None
    
    def go_to_next_page(self):
        """Navigate to the next page."""
        try:
            print(f"  Looking for next page button...")
            next_button = self.find_next_page_button()
            
            if next_button:
                print(f"  Found next page button: {next_button.text or next_button.get_attribute('aria-label') or 'Unknown'}")
                
                # Scroll to the button to make sure it's visible
                self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                time.sleep(1)
                
                # Try to click the button
                try:
                    next_button.click()
                    print(f"  Successfully clicked next page button")
                    return True
                except ElementClickInterceptedException:
                    # Try using JavaScript click
                    self.driver.execute_script("arguments[0].click();", next_button)
                    print(f"  Successfully clicked next page button using JavaScript")
                    return True
                except Exception as e:
                    print(f"  Error clicking next page button: {e}")
                    return False
            else:
                print(f"  No next page button found")
                return False
                
        except Exception as e:
            print(f"  Error navigating to next page: {e}")
            return False
    
    def process_all_pages(self, start_url: str, max_pages: int = None):
        """
        Process all pages starting from the given URL.
        
        Args:
            start_url: URL to start from
            max_pages: Maximum number of pages to process (None = no limit, scrape all pages)
        """
        try:
            print(f"Starting automated ad collection from: {start_url}")
            if max_pages:
                print(f"Maximum pages to process: {max_pages}")
            else:
                print("No page limit - will scrape ALL available pages")
            print("="*60)
            
            # Initialize driver
            self.driver = self.create_driver(headless=self.headless)
            
            # Load the first page
            print(f"Loading page 1: {start_url}")
            # Stealth tweaks before navigation
            try:
                self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": """
                        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                        window.chrome = { runtime: {} };
                        Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
                    """
                })
            except Exception:
                pass

            # Geolocation and timezone overrides
            try:
                self.driver.execute_cdp_cmd("Emulation.setGeolocationOverride", {
                    "latitude": 40.7128,
                    "longitude": -74.0060,
                    "accuracy": 100
                })
                self.driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "America/New_York"})
            except Exception:
                pass

            self.driver.get(start_url)
            
            # Handle any initial popups or notifications
            print("  Handling initial popups and notifications...")
            self.handle_popups_and_notifications()
            time.sleep(3)  # Wait for any popups to appear
            self.handle_popups_and_notifications()
            
            while True:
                print(f"\n--- PROCESSING PAGE {self.current_page} ---")
                
                # Collect ads from current page
                ads_data = self.collect_ads_from_current_page()
                
                if ads_data:
                    self.save_ads_to_csv(ads_data)
                else:
                    print(f"  No ads found on page {self.current_page}")
                
                # Check if we've reached the maximum page limit
                if max_pages and self.current_page >= max_pages:
                    print(f"  Reached maximum page limit ({max_pages})")
                    break
                
                # Try to go to next page
                print(f"  Attempting to go to page {self.current_page + 1}...")
                
                if self.go_to_next_page():
                    # Wait for new page to load
                    time.sleep(5)
                    # Handle any popups on the new page
                    self.handle_popups_and_notifications()
                    self.current_page += 1
                else:
                    print(f"  No more pages available. Stopping at page {self.current_page}")
                    break
            
            print(f"\n" + "="*60)
            print(f"AUTOMATED COLLECTION COMPLETE")
            print(f"Total pages processed: {self.current_page}")
            print(f"Total ads collected: {self.total_ads_collected}")
            print(f"Data saved to: {self.csv_filename}")
            print("="*60)
            
        except Exception as e:
            print(f"Error during automated collection: {e}")
        
        finally:
            if self.driver:
                self.driver.quit()
    
    def close(self):
        """Close the browser driver."""
        if self.driver:
            self.driver.quit()


def main():
    """Main function to demonstrate usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated Ad Collector - Collects ads from multiple pages")
    parser.add_argument("--url", default="https://www.newsbreak.com", help="Starting URL")
    parser.add_argument("--max-pages", type=int, default=None, help="Maximum number of pages to process (default: no limit, scrape all pages)")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--csv-file", default="ad_data_collection.csv", help="CSV filename to save data (default: ad_data_collection.csv)")
    
    args = parser.parse_args()
    
    # Initialize collector
    collector = AutomatedAdCollector(headless=args.headless, csv_filename=args.csv_file)
    
    try:
        # Process all pages
        collector.process_all_pages(args.url, args.max_pages)
        
    finally:
        collector.close()


if __name__ == "__main__":
    main()
