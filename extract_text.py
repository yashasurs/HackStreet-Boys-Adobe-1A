import fitz  # PyMuPDF
from collections import Counter
import re


def is_non_meaningful_heading(text):
    """
    Check if a heading text is non-meaningful and should be filtered out.
    Returns True if the text should be excluded.
    """
    if not text or len(text.strip()) <= 3:
        return True
    
    text_clean = text.strip()
    
    # Filter out pure numbers or simple patterns
    if re.match(r'^\d+\.?$', text_clean):  # Just numbers like "1", "2.", etc.
        return True
    
    # Filter out dots/dashes patterns (table of contents formatting)
    if re.match(r'^[.\-•\s]+$', text_clean):  # Just dots, dashes, bullets
        return True
    
    # Filter out very short single words that are likely not headings
    if len(text_clean) <= 5 and text_clean.lower() in ['date', 'name', 'age', 'no', 'ref', 'id', 's.no', 'version']:
        return True
    
    # Filter out table-of-contents style entries with lots of dots and page numbers
    if re.search(r'\.{5,}', text_clean):  # 5 or more consecutive dots
        return True
    
    # Filter out entries that are mostly page numbers and dots
    if re.match(r'^.*\d+\s*\.{3,}.*\d+$', text_clean):  # Pattern like "Chapter 1 .... 5"
        return True
    
    # Filter out signature/form placeholder text
    if any(phrase in text_clean.lower() for phrase in ['signature', 'date signature', 'government servant']):
        return True
    
    return False


def extract_pdf_text_with_styles(pdf_path):

    doc = fitz.open(pdf_path)
    headings = []
    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")['blocks']
        font_sizes = []
        all_lines_data = []  # Store all line data with positions
        page_height = page.rect.height
        header_threshold = page_height * 0.1  # Top 10% is header
        footer_threshold = page_height * 0.9  # Bottom 10% is footer
        
        # First pass: Check for potential document titles in header/footer regions (only on first page)
        potential_title_blocks = []
        if page_num == 0:  # Only check first page for titles
            for b in blocks:
                if b['type'] != 0:
                    continue
                block_y = b['bbox'][1]  # Top y-coordinate of block
                
                # Check if this block is in header/footer region
                if block_y < header_threshold or block_y > footer_threshold:
                    # Analyze this block to see if it could be a document title
                    block_spans = []
                    block_font_sizes = []
                    block_text = ""
                    
                    for line in b['lines']:
                        for span in line['spans']:
                            block_spans.append(span)
                            block_font_sizes.append(round(span['size'], 1))
                            block_text += span['text']
                    
                    if block_spans and block_font_sizes and block_text.strip():
                        # Check if this looks like a document title
                        avg_font_size = sum(block_font_sizes) / len(block_font_sizes)
                        text_length = len(block_text.strip())
                        
                        # Criteria for document title: larger font, reasonable length, meaningful text
                        if (avg_font_size >= 14.0 and  # Larger font size
                            text_length >= 10 and  # Reasonable length
                            text_length <= 100 and  # Not too long
                            not block_text.strip().isdigit() and  # Not just numbers
                            not is_non_meaningful_heading(block_text.strip())):  # Meaningful text
                            
                            potential_title_blocks.append({
                                'block': b,
                                'text': block_text.strip(),
                                'font_size': avg_font_size,
                                'y_pos': block_y
                            })
        
        # Second pass: Process regular content blocks (excluding header/footer)
        for b in blocks:
            if b['type'] != 0:
                continue
            # Skip blocks in header/footer regions (unless they're potential titles)
            block_y = b['bbox'][1]  # Top y-coordinate of block
            is_potential_title = any(pt['block'] is b for pt in potential_title_blocks)
            
            if (block_y < header_threshold or block_y > footer_threshold) and not is_potential_title:
                continue
                
            for line in b['lines']:
                spans = line['spans']
                line_sizes = [round(span['size'], 1) for span in spans]
                font_sizes.extend(line_sizes)
                # Store line data with y-position for ordering
                all_lines_data.append({
                    'spans': spans,
                    'sizes': line_sizes,
                    'y_pos': line['bbox'][1],  # Top y-coordinate of line
                    'block': b  # Store reference to block for heading detection
                })
        
        if not font_sizes:
            continue
        
        # Calculate most common size for the page
        size_counts = Counter(font_sizes)
        most_common_size = size_counts.most_common(1)[0][0]
        
        # If the most common size is very large (likely titles), use second most common as body text
        if most_common_size >= 20.0 and len(size_counts) > 1:
            body_text_size = size_counts.most_common(2)[1][0]  # Second most common
        else:
            body_text_size = most_common_size
        
        # Now check for heading blocks (blocks with large uniform font)
        processed_blocks = set()
        for line_data in all_lines_data:
            block = line_data['block']
            block_id = id(block)  # Use object id as unique identifier
            
            if block_id in processed_blocks:
                continue
                
            # Collect all spans from this block
            block_spans = []
            block_font_sizes = []
            for line in block['lines']:
                for span in line['spans']:
                    block_spans.append(span)
                    block_font_sizes.append(round(span['size'], 1))
            
            if block_spans and block_font_sizes:
                # Get the most common font size in this block
                block_size_counts = Counter(block_font_sizes)
                block_main_size = block_size_counts.most_common(1)[0][0]
                
                # Check if this block is primarily one large font size
                if (len(block_size_counts) <= 2 and  # Not too many different sizes
                    block_main_size > body_text_size and  # Larger than document body text
                    sum(1 for size in block_font_sizes if size == block_main_size) / len(block_font_sizes) > 0.7):  # 70%+ same size
                    
                    # This looks like a heading block - combine all text
                    block_text_parts = []
                    for span in block_spans:
                        if round(span['size'], 1) == block_main_size:
                            block_text_parts.append(span['text'])
                    
                    # Smart reconstruction for overlapping/fragmented text
                    block_text_parts = []
                    for span in block_spans:
                        if round(span['size'], 1) == block_main_size:
                            block_text_parts.append(span['text'])
                    
                    # Remove duplicates while preserving order
                    unique_texts = []
                    seen = set()
                    for text in block_text_parts:
                        if text not in seen:
                            unique_texts.append(text)
                            seen.add(text)
                    
                    # Find overlapping fragments and reconstruct
                    # Look for the pattern where each text extends the previous one
                    sorted_texts = sorted(unique_texts, key=len, reverse=True)
                    
                    if len(sorted_texts) >= 3:
                        # Try to find parts that complement each other
                        # Look for: beginning + middle + end
                        potential_parts = []
                        for text in sorted_texts:
                            if len(text) > 8:  # Only consider substantial parts
                                potential_parts.append(text)
                        
                        if len(potential_parts) >= 2:
                            # Try to combine overlapping parts intelligently
                            reconstructed = potential_parts[0]  # Start with longest
                            
                            for next_part in potential_parts[1:]:
                                # Check if this part extends our current text
                                # Find overlap and extend
                                max_overlap = 0
                                best_extension = ""
                                
                                # Check if next_part extends reconstructed
                                for i in range(1, min(len(reconstructed), len(next_part)) + 1):
                                    if reconstructed[-i:].lower() == next_part[:i].lower():
                                        extension = next_part[i:]
                                        if len(extension) > len(best_extension):
                                            best_extension = extension
                                            max_overlap = i
                                
                                # Also check if next_part is contained within reconstructed
                                if next_part.lower() in reconstructed.lower():
                                    continue  # Skip this part as it's already included
                                
                                if max_overlap > 0 and best_extension:
                                    reconstructed += best_extension
                                elif next_part not in reconstructed:
                                    # If no overlap but new content, append with space
                                    if not reconstructed.endswith(' ') and not next_part.startswith(' '):
                                        reconstructed += " " + next_part
                                    else:
                                        reconstructed += next_part
                            
                            heading_text = reconstructed.strip()
                            
                            # Post-process to fix common issues
                            heading_text = heading_text.replace("Pr Proposal", "Proposal")
                            heading_text = heading_text.replace("  ", " ")  # Remove double spaces
                        else:
                            # Fallback to longest text
                            heading_text = sorted_texts[0].strip()
                    else:
                        # Simple case - just use the longest
                        heading_text = sorted_texts[0].strip() if sorted_texts else ""
                    
                    # Filter out non-meaningful headings
                    if (heading_text and len(heading_text) > 3 and  # Minimum length check
                        not is_non_meaningful_heading(heading_text)):  # Filter meaningless headings
                        headings.append({
                            'text': heading_text,
                            'font_size': block_main_size,
                            'bold': any((s.get('flags', 0) & 2) or ('Bold' in s.get('font', '')) for s in block_spans if round(s['size'], 1) == block_main_size),
                            'italic': any((s.get('flags', 0) & 1) or ('Italic' in s.get('font', '') or 'Oblique' in s.get('font', '')) for s in block_spans if round(s['size'], 1) == block_main_size),
                            'page': page_num
                        })
                        processed_blocks.add(block_id)
                        continue  # Skip line-by-line processing for this block
        
        # Process potential title blocks from header/footer regions
        for potential_title in potential_title_blocks:
            block = potential_title['block']
            block_id = id(block)
            
            if block_id in processed_blocks:
                continue  # Already processed
                
            # Extract text from the potential title block
            block_spans = []
            block_font_sizes = []
            for line in block['lines']:
                for span in line['spans']:
                    block_spans.append(span)
                    block_font_sizes.append(round(span['size'], 1))
            
            if block_spans and block_font_sizes:
                # Get the most common font size in this block
                block_size_counts = Counter(block_font_sizes)
                block_main_size = block_size_counts.most_common(1)[0][0]
                
                # Reconstruct the text
                block_text_parts = []
                for span in block_spans:
                    if round(span['size'], 1) == block_main_size:
                        block_text_parts.append(span['text'])
                
                # Remove duplicates while preserving order
                unique_texts = []
                seen = set()
                for text in block_text_parts:
                    if text not in seen:
                        unique_texts.append(text)
                        seen.add(text)
                
                # Combine the text
                heading_text = ' '.join(unique_texts).strip()
                
                # Clean up the text
                heading_text = heading_text.replace("  ", " ")  # Remove double spaces
                
                # Add as heading if meaningful
                if (heading_text and len(heading_text) > 3 and  
                    not is_non_meaningful_heading(heading_text)):
                    headings.append({
                        'text': heading_text,
                        'font_size': block_main_size,
                        'bold': any((s.get('flags', 0) & 2) or ('Bold' in s.get('font', '')) for s in block_spans if round(s['size'], 1) == block_main_size),
                        'italic': any((s.get('flags', 0) & 1) or ('Italic' in s.get('font', '') or 'Oblique' in s.get('font', '')) for s in block_spans if round(s['size'], 1) == block_main_size),
                        'page': page_num
                    })
                    processed_blocks.add(block_id)
        
        # Process remaining lines for regular headings
        page_headings = []
        # Sort lines by y-position to process in reading order
        all_lines_data.sort(key=lambda x: x['y_pos'])
        
        # Process remaining lines for regular headings (skip already processed blocks)
        for line_data in all_lines_data:
            if id(line_data['block']) in processed_blocks:
                continue  # Skip lines from blocks already processed as headings
                
            spans = line_data['spans']
            line_sizes = line_data['sizes']
            
            # Check if first span at start of line is a heading
            if not spans:
                continue
            
            first_span = spans[0]
            first_size = round(first_span['size'], 1)
            first_bold = (first_span.get('flags', 0) & 2) or ('Bold' in first_span.get('font', ''))
            first_italic = (first_span.get('flags', 0) & 1) or ('Italic' in first_span.get('font', '') or 'Oblique' in first_span.get('font', ''))
            
            # Check if this is a heading: either larger font OR bold/italic at start
            is_heading = False
            if first_size > body_text_size:
                is_heading = True  # Larger font size
            elif (first_bold or first_italic) and first_size >= body_text_size:
                is_heading = True  # Bold/italic at start (same or larger size)
            
            if is_heading:
                # Collect ALL spans from the line for fragmented text (like overlapping titles)
                heading_spans = []
                line_text_parts = []
                
                # Collect all text from this line to handle fragmented/overlapping spans
                for span in spans:
                    span_size = round(span['size'], 1)
                    span_bold = (span.get('flags', 0) & 2) or ('Bold' in span.get('font', ''))
                    span_italic = (span.get('flags', 0) & 1) or ('Italic' in span.get('font', '') or 'Oblique' in span.get('font', ''))
                    
                    # Include span if it matches the heading characteristics
                    if span_size == first_size and ((first_size > body_text_size) or (span_bold or span_italic)):
                        heading_spans.append(span)
                        line_text_parts.append(span['text'])
                
                # Try to reconstruct the full text from all collected spans
                if heading_spans:
                    # Use the longest text piece or combine unique parts
                    full_text = ' '.join(line_text_parts).strip()
                    # Remove duplicate words that might occur due to overlapping spans
                    words = full_text.split()
                    unique_words = []
                    for word in words:
                        if not unique_words or word != unique_words[-1]:
                            unique_words.append(word)
                    heading_text = ' '.join(unique_words)
                    
                    if heading_text and not is_non_meaningful_heading(heading_text):
                        page_headings.append({
                            'text': heading_text,
                            'font_size': first_size,
                            'bold': any((s.get('flags', 0) & 2) or ('Bold' in s.get('font', '')) for s in heading_spans),
                            'italic': any((s.get('flags', 0) & 1) or ('Italic' in s.get('font', '') or 'Oblique' in s.get('font', '')) for s in heading_spans),
                            'page': page_num,
                            'y_pos': line_data['y_pos']
                        })
            else:
                # This is not a heading, so it breaks any potential multi-line heading sequence
                page_headings.append(None)
        
        # Now merge consecutive headings (only those that are truly adjacent)
        merged_page_headings = []
        i = 0
        while i < len(page_headings):
            if page_headings[i] is None:
                i += 1
                continue
                
            current_heading = page_headings[i]
            # Look ahead for consecutive headings with same formatting
            j = i + 1
            while (j < len(page_headings) and 
                   page_headings[j] is not None and
                   page_headings[j]['font_size'] == current_heading['font_size'] and
                   page_headings[j]['bold'] == current_heading['bold'] and
                   page_headings[j]['italic'] == current_heading['italic'] and
                   not current_heading['text'].endswith('.') and
                   not current_heading['text'].endswith('?') and
                   not current_heading['text'].endswith('!')):
                current_heading['text'] += ' ' + page_headings[j]['text']
                j += 1
            
            # Remove y_pos before adding to final list
            final_heading = {k: v for k, v in current_heading.items() if k != 'y_pos'}
            merged_page_headings.append(final_heading)
            i = j
        
        headings.extend(merged_page_headings)
    
    return headings


# if __name__ == "__main__":
#     import json
#     import os
#     input_dir = "input"
#     output_dir = "output"
    
#     # Ensure output directory exists
#     os.makedirs(output_dir, exist_ok=True)
    
#     for filename in os.listdir(input_dir):
#         if not filename.lower().endswith(".pdf"):
#             continue
#         input_path = os.path.join(input_dir, filename)
#         results = extract_pdf_text_with_styles(input_path)
#         base = os.path.splitext(filename)[0]
#         output_path = os.path.join(output_dir, f"{base}.json")
#         with open(output_path, "w", encoding="utf-8") as f:
#             json.dump(results, f, indent=2, ensure_ascii=False)