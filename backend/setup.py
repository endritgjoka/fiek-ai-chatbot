"""
Setup script to initialize the chatbot system.
Run this after installing dependencies to set up the knowledge base.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from data_collection.scrape_data import collect_all_data
from data_collection.prepare_data import merge_data

def setup():
    """Run complete setup process."""
    print("=" * 60)
    print("FIEK Chatbot Setup")
    print("=" * 60)
    print("\nStep 1: Collecting data from web sources...")
    print("This may take several minutes...\n")
    
    try:
        # Collect data
        collect_all_data()
        
        print("\nStep 2: Merging with custom data...")
        merge_data()
        
        print("\n" + "=" * 60)
        print("Setup completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Review the collected data in: backend/knowledge_base/collected_data.json")
        print("2. Run the Flask app: python backend/app.py")
        print("3. Open frontend/index.html in your browser")
        print("\n")
        
    except Exception as e:
        print(f"\nError during setup: {e}")
        print("\nYou can manually:")
        print("1. Run: python backend/data_collection/scrape_data.py")
        print("2. Run: python backend/data_collection/prepare_data.py")
        sys.exit(1)

if __name__ == "__main__":
    setup()

