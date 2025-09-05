#!/usr/bin/env python3
"""
Scrape All Pages Headless - Complete Ad Collection (Background)
Scrapes ALL available pages in headless mode until no more pages are found.
"""

from automated_ad_collector import AutomatedAdCollector


def scrape_all_pages_headless():
    """Scrape all available pages for ads in headless mode."""
    
    print("="*70)
    print("COMPLETE AD COLLECTION - ALL PAGES (HEADLESS MODE)")
    print("="*70)
    print("This script will scrape ALL available pages in headless mode.")
    print("Data will be saved to: ad_data_collection.csv")
    print("The script will run in the background without visible browser.")
    print("="*70)
    
    # Initialize collector with persistent CSV file in headless mode
    collector = AutomatedAdCollector(
        headless=True,  # Headless mode
        csv_filename="ad_data_collection.csv"
    )
    
    try:
        print("Starting headless collection...")
        print("This will run in the background. Check ad_data_collection.csv for progress.")
        print("="*70)
        
        # Process ALL pages - no limit
        collector.process_all_pages("https://www.newsbreak.com", max_pages=None)
        
        print("\n" + "="*70)
        print("COMPLETE COLLECTION FINISHED!")
        print("="*70)
        print("All available pages have been processed.")
        print("Check ad_data_collection.csv for all collected data.")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n" + "="*70)
        print("Collection stopped by user.")
        print(f"Data collected so far has been saved to ad_data_collection.csv")
        print(f"Total pages processed: {collector.current_page}")
        print(f"Total ads collected: {collector.total_ads_collected}")
        print("="*70)
    except Exception as e:
        print(f"Error during collection: {e}")
    finally:
        collector.close()


if __name__ == "__main__":
    scrape_all_pages_headless()
