import fitz  # PyMuPDF
from collections import Counter

def debug_heading_detection(pdf_path):
    """Debug function to see what's happening in heading detection"""
    doc = fitz.open(pdf_path)
    
    if len(doc) == 0:
        print("No pages in document")
        return
        
    page = doc[0]  # First page
    blocks = page.get_text("dict")['blocks']
    font_sizes = []
    all_lines_data = []
    page_height = page.rect.height
    header_threshold = page_height * 0.1
    footer_threshold = page_height * 0.9
    
    print(f"=== HEADING DETECTION DEBUG: Page 0 of {pdf_path} ===")
    
    # Collect all font sizes first
    for b in blocks:
        if b['type'] != 0:
            continue
        block_y = b['bbox'][1]
        if block_y < header_threshold or block_y > footer_threshold:
            continue
            
        for line in b['lines']:
            spans = line['spans']
            line_sizes = [round(span['size'], 1) for span in spans]
            font_sizes.extend(line_sizes)
            all_lines_data.append({
                'spans': spans,
                'sizes': line_sizes,
                'y_pos': line['bbox'][1],
                'block': b
            })
    
    size_counts = Counter(font_sizes)
    most_common_size = size_counts.most_common(1)[0][0]
    print(f"Most common font size: {most_common_size}")
    print(f"All font sizes: {sorted(set(font_sizes), reverse=True)}")
    
    # Check each block for heading potential
    processed_blocks = set()
    for line_data in all_lines_data:
        block = line_data['block']
        block_id = id(block)
        
        if block_id in processed_blocks:
            continue
            
        # Collect all spans from this block
        block_spans = []
        block_font_sizes = []
        for line in block['lines']:
            for span in line['spans']:
                block_spans.append(span)
                block_font_sizes.append(round(span['size'], 1))
        
        print(f"\n--- Checking block at y={block['bbox'][1]:.1f} ---")
        print(f"Block font sizes: {block_font_sizes}")
        
        if block_spans and block_font_sizes:
            block_size_counts = Counter(block_font_sizes)
            block_main_size = block_size_counts.most_common(1)[0][0]
            
            print(f"Block main size: {block_main_size}")
            print(f"Block size counts: {dict(block_size_counts)}")
            print(f"Number of different sizes: {len(block_size_counts)}")
            print(f"Main size > most_common_size? {block_main_size} > {most_common_size} = {block_main_size > most_common_size}")
            
            # Calculate percentage of main size
            main_size_percent = sum(1 for size in block_font_sizes if size == block_main_size) / len(block_font_sizes)
            print(f"Main size percentage: {main_size_percent:.2%}")
            
            # Check conditions
            condition1 = len(block_size_counts) <= 2
            condition2 = block_main_size > most_common_size
            condition3 = main_size_percent > 0.7
            
            print(f"Condition 1 (<=2 different sizes): {condition1}")
            print(f"Condition 2 (larger than body text): {condition2}")
            print(f"Condition 3 (>=70% same size): {condition3}")
            print(f"ALL CONDITIONS MET: {condition1 and condition2 and condition3}")
            
            if condition1 and condition2 and condition3:
                print("*** THIS WOULD BE DETECTED AS A HEADING BLOCK ***")
                # Show reconstructed text
                block_text_parts = []
                for span in block_spans:
                    if round(span['size'], 1) == block_main_size:
                        block_text_parts.append(span['text'])
                
                full_text = ' '.join(block_text_parts).strip()
                words = full_text.split()
                unique_words = []
                for word in words:
                    if not unique_words or word != unique_words[-1]:
                        unique_words.append(word)
                heading_text = ' '.join(unique_words)
                print(f"Reconstructed text: '{heading_text}'")
            
            processed_blocks.add(block_id)

# Test on file03.pdf
debug_heading_detection("input/file03.pdf")
