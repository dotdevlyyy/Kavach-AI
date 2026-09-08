import os
import sys

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from app.rag.parser import parse_document
from app.rag.chunker import chunk_text

samples_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'samples'))

files_to_test = [
    "refinery_sop.txt",
    "inspection_report.pdf"
]

print("Starting Ingestion Verification...\n")

for filename in files_to_test:
    file_path = os.path.join(samples_dir, filename)
    print(f"--- Testing {filename} ---")
    
    try:
        # Test 1: Parser
        extracted_text = parse_document(file_path)
        print(f"[PASS] Extraction successful: Extracted {len(extracted_text)} characters.")
        print(f"   Preview: {extracted_text[:100].replace(chr(10), ' ')}...")
        
        # Test 2: Chunker (Using smaller sizes for visual verification)
        chunks = chunk_text(extracted_text, chunk_size=30, overlap_size=5) 
        print(f"[PASS] Chunking successful: Created {len(chunks)} chunks.")
        
        for i, chunk in enumerate(chunks[:2]): # Print first two
            print(f"   Chunk {i+1} ({len(chunk.split())} words): {chunk}")
            
    except Exception as e:
        print(f"[FAIL] Error processing {filename}: {e}")
    print()
