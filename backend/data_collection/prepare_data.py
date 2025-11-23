"""
Prepare and merge all data sources for the knowledge base.
"""

import json
from pathlib import Path

def merge_data():
    """Merge scraped data with custom data."""
    base_path = Path(__file__).parent.parent / "knowledge_base"
    
    # Load scraped data
    scraped_file = base_path / "collected_data.json"
    custom_file = base_path / "custom_data.json"
    output_file = base_path / "collected_data.json"
    
    all_data = []
    
    # Load scraped data if exists
    if scraped_file.exists():
        with open(scraped_file, 'r', encoding='utf-8') as f:
            all_data = json.load(f)
    
    # Load and merge custom data
    if custom_file.exists():
        with open(custom_file, 'r', encoding='utf-8') as f:
            custom_data = json.load(f)
            all_data.extend(custom_data)
    
    # Save merged data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print(f"Merged {len(all_data)} documents")
    return all_data

if __name__ == "__main__":
    merge_data()

