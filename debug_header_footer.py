import fitz  # PyMuPDF

def debug_header_footer_filtering(pdf_path):
    """Debug function to check header/footer filtering"""
    doc = fitz.open(pdf_path)
    
    if len(doc) == 0:
        print("No pages in document")
        return
        
    page = doc[0]  # First page
    page_height = page.rect.height
    header_threshold = page_height * 0.1  # Top 10% is header
    footer_threshold = page_height * 0.9  # Bottom 10% is footer
    
    print(f"=== HEADER/FOOTER DEBUG: Page 0 of {pdf_path} ===")
    print(f"Page height: {page_height}")
    print(f"Header threshold (top 10%): {header_threshold}")
    print(f"Footer threshold (bottom 10%): {footer_threshold}")
    
    blocks = page.get_text("dict")['blocks']
    
    for i, block in enumerate(blocks):
        if block['type'] != 0:  # Skip non-text blocks
            continue
            
        block_y = block['bbox'][1]  # Top y-coordinate of block
        print(f"\nBlock {i}: Y-position: {block_y}")
        print(f"  BBox: {block['bbox']}")
        
        if block_y < header_threshold:
            print(f"  -> FILTERED OUT as HEADER (y={block_y} < {header_threshold})")
        elif block_y > footer_threshold:
            print(f"  -> FILTERED OUT as FOOTER (y={block_y} > {footer_threshold})")
        else:
            print(f"  -> KEPT (y={block_y} is between {header_threshold} and {footer_threshold})")
            
        # Show first line of text for reference
        if block['lines']:
            first_line_text = ""
            for span in block['lines'][0]['spans']:
                first_line_text += span['text']
            print(f"  Content preview: '{first_line_text[:50]}...'")

# Test on file04.pdf
debug_header_footer_filtering("input/file04.pdf")
