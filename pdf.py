import shutil
from pathlib import Path

# Define source and destination
source_dir = Path(r'C:\Users\kamalesh\Desktop\pdf\Exported Items')
dest_dir = source_dir.parent / 'all_pdf'

# Create destination folder if it doesn't exist
dest_dir.mkdir(exist_ok=True)

# Find and copy all PDF files
pdf_count = 0
for pdf_file in source_dir.rglob('*.pdf'):
    try:
        # Copy PDF to destination folder (keeps original filename)
        shutil.copy2(pdf_file, dest_dir / pdf_file.name)
        pdf_count += 1
        print(f"Copied: {pdf_file.name}")
    except Exception as e:
        print(f"Error copying {pdf_file.name}: {e}")

print(f"\nTotal PDFs copied: {pdf_count}")
print(f"All PDFs are now in: {dest_dir}")
