#!/usr/bin/env python3
"""
Run Persistent Ad Collection
Demonstrates how to use the persistent CSV file for continuous ad collection.
"""

from automated_ad_collector import AutomatedAdCollector


def run_persistent_collection():
    """Run ad collection with persistent CSV file."""
    
    print("Starting persistent ad collection...")
    print("All data will be saved to: ad_data_collection.csv")
    print("This file will be created if it doesn't exist, or data will be appended if it does.")
    print("="*70)
    
    # Initialize collector with persistent CSV file
    collector = AutomatedAdCollector(
        headless=False,  # Set to True for headless mode
        csv_filename="ad_data_collection.csv"
    )
    
    try:
        # Process multiple pages - data will be appended to the same CSV file
        collector.process_all_pages("https://www.newsbreak.com", max_pages=5)
        
        print("\n" + "="*70)
        print("Collection completed! Check ad_data_collection.csv for all collected data.")
        print("You can run this script again to add more data to the same file.")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\nCollection stopped by user.")
        print("Data collected so far has been saved to ad_data_collection.csv")
    except Exception as e:
        print(f"Error during collection: {e}")
    finally:
        collector.close()


if __name__ == "__main__":
    run_persistent_collection()
