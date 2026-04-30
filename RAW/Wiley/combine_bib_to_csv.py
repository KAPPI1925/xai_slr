import os
import csv
import re
from pathlib import Path
from collections import defaultdict

def parse_bib_entry(entry_text):
    """Parse a single BibTeX entry and extract fields."""
    entry = {}
    
    # Extract entry type and key
    match = re.match(r'@(\w+)\s*\{([^,\n]+)', entry_text)
    if match:
        entry['entry_type'] = match.group(1)
        entry['key'] = match.group(2).strip()
    
    # Define fields to extract
    fields = ['author', 'title', 'journal', 'volume', 'number', 'pages', 
              'keywords', 'doi', 'url', 'eprint', 'abstract', 'year', 'note']
    
    for field in fields:
        # Pattern to match field = {...} or field = "..." or field = value
        pattern = rf'{field}\s*=\s*\{{([^}}]*)\}}|{field}\s*=\s*"([^"]*)"|{field}\s*=\s*([^,\n}}]*)'
        match = re.search(pattern, entry_text, re.IGNORECASE)
        if match:
            # Get the first non-None group
            value = next((g for g in match.groups() if g is not None), '').strip()
            entry[field] = value
    
    return entry

def read_all_bib_files(directory):
    """Read all .bib files from the directory and return list of entries."""
    all_entries = []
    bib_files = sorted(Path(directory).glob('*.bib'))
    
    print(f"Found {len(bib_files)} .bib files")
    
    for bib_file in bib_files:
        print(f"Reading: {bib_file.name}")
        try:
            with open(bib_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split by @article, @book, @inproceedings, etc.
            entries = re.split(r'(?=@\w+)', content)
            
            for entry_text in entries:
                if entry_text.strip() and entry_text.strip().startswith('@'):
                    entry = parse_bib_entry(entry_text)
                    if entry:
                        all_entries.append(entry)
        except Exception as e:
            print(f"Error reading {bib_file.name}: {e}")
    
    return all_entries

def save_to_csv(entries, output_file):
    """Save entries to CSV file."""
    if not entries:
        print("No entries to save!")
        return
    
    # Define fieldnames
    fieldnames = ['entry_type', 'key', 'author', 'title', 'journal', 'volume', 
                  'number', 'pages', 'keywords', 'doi', 'url', 'eprint', 'abstract', 'year', 'note']
    
    print(f"\nWriting {len(entries)} entries to {output_file}")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        
        for entry in entries:
            # Ensure all fields exist in the entry
            for field in fieldnames:
                if field not in entry:
                    entry[field] = ''
            writer.writerow(entry)
    
    print(f"Successfully created: {output_file}")

def main():
    directory = r'c:\Users\kamalesh\Downloads\Wiley'
    output_file = os.path.join(directory, 'combined_citations.csv')
    
    # Read all .bib files
    entries = read_all_bib_files(directory)
    
    if entries:
        print(f"\nTotal entries found: {len(entries)}")
        # Save to CSV
        save_to_csv(entries, output_file)
    else:
        print("No entries found in any .bib files!")

if __name__ == '__main__':
    main()
