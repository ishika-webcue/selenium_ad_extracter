#!/usr/bin/env python3
"""
Scrape All Pages - Complete Ad Collection
Scrapes ALL available pages until no more pages are found.
"""

from automated_ad_collector import AutomatedAdCollector


def scrape_all_pages():
    """Scrape all available pages for ads."""
    
    print("="*70)
    print("COMPLETE AD COLLECTION - ALL PAGES")
    print("="*70)
    print("This script will scrape ALL available pages until no more pages are found.")
    print("Data will be saved to: ad_data_collection.csv")
    print("The script will continue until it can't find any more 'Next Page' buttons.")
    print("="*70)
    
    # Ask for confirmation
    response = input("Do you want to continue? This may take a long time. (y/n): ")
    if response.lower() != 'y':
        print("Collection cancelled.")
        return
    
    # Initialize collector with persistent CSV file
    collector = AutomatedAdCollector(
        headless=False,  # Set to True for headless mode
        csv_filename="ad_data_collection.csv"
    )
    
    try:
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
    scrape_all_pages()
