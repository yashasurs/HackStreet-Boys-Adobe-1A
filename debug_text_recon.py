import fitz  # PyMuPDF

def debug_text_reconstruction():
    """Debug the text reconstruction for Block 1"""
    doc = fitz.open("input/file03.pdf")
    page = doc[0]
    blocks = page.get_text("dict")['blocks']
    
    # Get Block 1 (the RFP block)
    block = blocks[1]
    
    print("=== TEXT RECONSTRUCTION DEBUG ===")
    print("All spans from Block 1:")
    
    all_texts = []
    for i, line in enumerate(block['lines']):
        for j, span in enumerate(line['spans']):
            text = span['text']
            all_texts.append(text)
            print(f"Line {i}, Span {j}: '{text}' (length: {len(text)})")
    
    print(f"\nAll texts: {all_texts}")
    
    # Try different reconstruction strategies
    print("\n--- Strategy 1: Longest text ---")
    longest = max(all_texts, key=len)
    print(f"Longest: '{longest}'")
    
    print("\n--- Strategy 2: Look for complete words ---")
    complete_words = [t for t in all_texts if ' ' in t or len(t) > 8]
    print(f"Complete word candidates: {complete_words}")
    
    print("\n--- Strategy 3: Reconstruct by combining unique parts ---")
    # Try to find the pattern
    seen_parts = set()
    unique_parts = []
    for text in all_texts:
        if text not in seen_parts and len(text) > 2:
            unique_parts.append(text)
            seen_parts.add(text)
    print(f"Unique parts: {unique_parts}")
    
    # Look for the longest texts that seem to build upon each other
    print("\n--- Strategy 4: Find progressive build-up ---")
    sorted_by_length = sorted(set(all_texts), key=len)
    print(f"Sorted by length: {sorted_by_length}")
    
debug_text_reconstruction()
