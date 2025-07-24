import fitz  # PyMuPDF
from collections import Counter

def debug_pdf_page_0(pdf_path):
    """Debug function to see all text on page 0"""
    doc = fitz.open(pdf_path)
    
    if len(doc) == 0:
        print("No pages in document")
        return
        
    page = doc[0]  # First page
    blocks = page.get_text("dict")['blocks']
    
    print(f"=== DEBUG: Page 0 of {pdf_path} ===")
    print(f"Total blocks: {len(blocks)}")
    
    for i, block in enumerate(blocks):
        if block['type'] != 0:  # Skip non-text blocks
            print(f"Block {i}: Non-text block (type {block['type']})")
            continue
            
        print(f"\nBlock {i}: Text block")
        print(f"  BBox: {block['bbox']}")
        
        for j, line in enumerate(block['lines']):
            print(f"  Line {j}: BBox: {line['bbox']}")
            for k, span in enumerate(line['spans']):
                print(f"    Span {k}: '{span['text']}' | Size: {span['size']:.1f} | Font: {span.get('font', 'Unknown')} | Flags: {span.get('flags', 0)}")

# Test on file03.pdf
debug_pdf_page_0("input/file03.pdf")
