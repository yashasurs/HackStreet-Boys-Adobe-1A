import fitz  # PyMuPDF
from collections import Counter
import re


def is_non_meaningful_heading(text):
    """
    Check if a heading text is meaningful and should be filtered out.
    Returns True if the text should be excluded.
    """
    if not text or len(text.strip()) <= 3:
        return True
    
    text_clean = text.strip()
    
    # Filter out common non-heading patterns
    non_heading_patterns = [
        r'^page\s+\d+$',  # Page numbers
        r'^\d+\s*[\/\-]\s*\d+$',  # Fractions or ratios
        r'^[a-z]$',  # Single lowercase letters
        r'^\([a-z]\)$',  # Single letters in parentheses
        r'^fig\.?\s*\d*$',  # Figure references
        r'^table\.?\s*\d*$',  # Table references
        r'^appendix\s*[a-z]?$',  # Appendix references alone
        r'^www\..*\.com.*$',  # Website URLs
        r'^.*\.com\s*$',  # Domain names
    ]
    
    for pattern in non_heading_patterns:
        if re.match(pattern, text_clean.lower()):
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
    
    # Filter out tabular data patterns
    if is_tabular_data(text_clean):
        return True
    
    # Filter out form field labels and similar patterns
    if is_form_field_or_label(text_clean):
        return True
    
    return False


def is_tabular_data(text):
    """
    Check if text appears to be from a table or tabular structure.
    Returns True if text should be excluded as tabular data.
    """
    text_clean = text.strip()
    
    # Pattern 1: Multiple numbers separated by spaces/tabs (like table cells)
    if re.search(r'\d+\s+\d+\s+\d+', text_clean):
        return True
    
    # Pattern 2: Currency or percentage values in sequence
    if re.search(r'[\$₹€£¥]\s*\d+.*[\$₹€£¥]\s*\d+|%.*%|\d+%.*\d+%', text_clean):
        return True
    
    # Pattern 3: Column header patterns (short words with consistent formatting)
    column_patterns = [
        r'^(sl\.?\s*no\.?|s\.?\s*no\.?|sr\.?\s*no\.?)$',  # Serial number columns
        r'^(amount|qty|quantity|rate|price|total|subtotal)$',  # Common table headers
        r'^(date|time|duration|period)$',  # Date/time columns
        r'^(yes|no|y|n)$',  # Boolean columns
        r'^(name|description|item|product|service)$'  # Text columns
    ]
    
    for pattern in column_patterns:
        if re.match(pattern, text_clean.lower()):
            return True
    
    # Pattern 4: Repetitive formatting patterns (like table borders)
    if re.match(r'^[-=_|+\s]{4,}$', text_clean):  # Table border patterns
        return True
    
    # Pattern 5: Data that looks like table cells (short, structured data)
    words = text_clean.split()
    if len(words) <= 3:
        # Check if all words are short and look like data entries
        if all(len(word) <= 10 and (word.isdigit() or 
                                   re.match(r'^\d+[.,]\d+$', word) or  # Decimal numbers
                                   re.match(r'^[A-Z]{1,5}$', word) or  # Short codes
                                   word.lower() in ['yes', 'no', 'na', 'nil', 'null', 'none']) 
               for word in words):
            return True
    
    # Pattern 6: Pathway table column headers - detect when these appear as isolated table headers
    # rather than as part of a larger descriptive heading
    text_lower = text_clean.lower()
    pathway_table_patterns = [
        r'^regular\s+pathway$',
        r'^distinction\s+pathway$',
        r'^honors?\s+pathway$',
        r'^advanced\s+pathway$',
    ]
    
    for pattern in pathway_table_patterns:
        if re.match(pattern, text_lower):
            return True
    
    # Pattern 7: Combined pathway text that suggests table structure
    if re.match(r'^(regular\s+pathway\s+distinction\s+pathway|distinction\s+pathway\s+regular\s+pathway)$', text_lower):
        return True
    
    return False


def is_form_field_or_label(text):
    """
    Check if text appears to be a form field label or similar non-heading content.
    Returns True if text should be excluded as form field.
    """
    text_clean = text.strip().lower()
    
    # Allow document titles that contain form-related words but are descriptive
    if len(text_clean) > 20 and any(word in text_clean for word in ['application', 'form', 'request', 'proposal']):
        # This looks like a document title, not a form field
        return False
    
    # Common form field patterns
    form_patterns = [
        r'.*:$',  # Text ending with colon (field labels)
        r'^\d+\.\s*$',  # Just numbered points without content
        r'^(name|address|phone|email|date|time).*:?$',  # Common form fields
        r'^(enter|select|choose|tick|mark|fill).*',  # Instructions
        r'.*\(.*\)$',  # Text with parentheses (often explanatory)
        r'.*\[.*\]$',  # Text with square brackets
        r'^(note|remark|comment|instruction).*:?',  # Instructional text
        r'amount.*rs\.?|rs\.?.*amount',  # Currency related short text
        r'^relationship$',  # Relationship field
        r'^\d+\.\s*(amount|advance|required|grant|ltc).*',  # Numbered form fields about amount/advance/grant
        r'.*advance.*required.*',  # Form fields about advance requirements
        r'.*grant.*ltc.*',  # Form fields about LTC grants
    ]
    
    for pattern in form_patterns:
        if re.match(pattern, text_clean):
            return True
    
    return False


def is_likely_heading(text):
    """
    Check if text is likely to be a proper heading based on content patterns.
    Returns True if text appears to be a valid heading.
    """
    text_clean = text.strip()
    
    # Basic checks
    if len(text_clean) < 3 or len(text_clean) > 200:
        return False
    
    # Headings should not be entirely numeric
    if text_clean.replace('.', '').replace(' ', '').isdigit():
        return False
    
    # Check for proper heading characteristics
    words = text_clean.split()
    
    # Single character or very short text is unlikely to be a heading
    if len(words) == 1 and len(text_clean) <= 2:
        return False
    
    # Filter out common non-heading patterns
    non_heading_patterns = [
        r'^page\s+\d+$',  # Page numbers
        r'^\d+\s*[\/\-]\s*\d+$',  # Fractions or ratios
        r'^[a-z]$',  # Single lowercase letters
        r'^\([a-z]\)$',  # Single letters in parentheses
        r'^fig\.?\s*\d*$',  # Figure references
        r'^table\.?\s*\d*$',  # Table references
        r'^appendix\s*[a-z]?$',  # Appendix references alone
    ]
    
    for pattern in non_heading_patterns:
        if re.match(pattern, text_clean.lower()):
            return False
    
    # Positive indicators for headings
    # Headings often start with capital letters
    if text_clean[0].isupper():
        return True
    
    # Headings can be numbered sections
    if re.match(r'^\d+\.?\s+[A-Z]', text_clean):
        return True
    
    # Allow most other text that passed the negative filters
    return True


def is_text_from_image_region(bbox, page):
    """
    Check if the text is likely from an image region by detecting nearby images.
    Returns True if text should be excluded as it's from an image.
    """
    try:
        # Get image list from the page
        images = page.get_images()
        if not images:
            return False
        
        text_x1, text_y1, text_x2, text_y2 = bbox
        text_center_x = (text_x1 + text_x2) / 2
        text_center_y = (text_y1 + text_y2) / 2
        
        # Check each image on the page
        for img_index, img in enumerate(images):
            try:
                # Get image bbox
                img_rect = page.get_image_bbox(img)
                if img_rect:
                    img_x1, img_y1, img_x2, img_y2 = img_rect
                    
                    # Add a small buffer around the image
                    buffer = 10
                    img_x1 -= buffer
                    img_y1 -= buffer
                    img_x2 += buffer
                    img_y2 += buffer
                    
                    # Check if text is within or very close to the image bounds
                    if (img_x1 <= text_center_x <= img_x2 and 
                        img_y1 <= text_center_y <= img_y2):
                        return True
                        
                    # Also check if text bbox overlaps significantly with image
                    overlap_x = max(0, min(text_x2, img_x2) - max(text_x1, img_x1))
                    overlap_y = max(0, min(text_y2, img_y2) - max(text_y1, img_y1))
                    
                    if overlap_x > 0 and overlap_y > 0:
                        text_area = (text_x2 - text_x1) * (text_y2 - text_y1)
                        overlap_area = overlap_x * overlap_y
                        
                        # If more than 30% of text area overlaps with image, consider it part of image
                        if text_area > 0 and (overlap_area / text_area) > 0.3:
                            return True
            except:
                # If there's any error getting image bbox, skip this image
                continue
                
        return False
    except:
        # If there's any error in image detection, don't filter out the text
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
                        if (avg_font_size >= 10.0 and  # Further reduced font size requirement
                            text_length >= 5 and  # Further reduced minimum length
                            text_length <= 200 and  # Increased max length
                            not block_text.strip().isdigit()):  # Only exclude pure numbers
                            
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
                
                # Check if this block is primarily one large font size or could be a title
                block_is_heading = False
                
                # Calculate average font size for this block
                avg_font_size = sum(block_font_sizes) / len(block_font_sizes)
                
                # Check if this is a heading block - more generous criteria for better coverage
                if (len(block_size_counts) <= 3 and  # Allow more font size variation
                    avg_font_size > body_text_size * 1.5 and  # Reduced threshold for average size  
                    block_main_size >= body_text_size * 1.5):  # Reduced threshold for main size
                    block_is_heading = True
                
                # Special case for potential document titles on first page with very large, consistent fonts
                elif (page_num == 0 and 
                      avg_font_size > body_text_size * 2.0 and  # Reduced threshold for title detection
                      len(block_size_counts) <= 3):  # Allow slightly more variation
                    block_is_heading = True
                
                if block_is_heading:
                    # Collect all text from spans in this block, focusing on larger/bold spans
                    block_text_parts = []
                    significant_font_sizes = [size for size in block_font_sizes if size >= body_text_size]
                    min_significant_size = min(significant_font_sizes) if significant_font_sizes else block_main_size
                    
                    for span in block_spans:
                        span_size = round(span['size'], 1)
                        span_bold = (span.get('flags', 0) & 2) or ('Bold' in span.get('font', ''))
                        
                    # Include span if it's large enough or bold
                    if span_size >= min_significant_size * 0.8 or span_bold:  # More inclusive for span inclusion
                        block_text_parts.append(span['text'])                    # Combine all text parts
                    heading_text = ''.join(block_text_parts).strip()
                    
                    # Clean up the text
                    heading_text = heading_text.replace("  ", " ")  # Remove double spaces
                    heading_text = re.sub(r'\s+', ' ', heading_text)  # Normalize whitespace
                    
                    # Filter out non-meaningful headings and text from images/tables
                    if (heading_text and len(heading_text) > 3 and  # Minimum length check
                        not is_non_meaningful_heading(heading_text) and  # Filter meaningless headings
                        not is_text_from_image_region(block['bbox'], page)):  # Filter image text
                        
                        # Additional check: ensure it looks like a proper heading
                        if is_likely_heading(heading_text):
                            headings.append({
                                'text': heading_text,
                                'font_size': block_main_size,
                                'bold': any((s.get('flags', 0) & 2) or ('Bold' in s.get('font', '')) for s in block_spans if round(s['size'], 1) == block_main_size),
                                'italic': any((s.get('flags', 0) & 1) or ('Italic' in s.get('font', '') or 'Oblique' in s.get('font', '')) for s in block_spans if round(s['size'], 1) == block_main_size),
                                'page': page_num
                            })
                            processed_blocks.add(block_id)
                            continue  # Skip line-by-line processing for this block
        
        # Handle mixed content blocks - check individual lines for large bold text
        processed_lines = set()
        for line_data in all_lines_data:
            block = line_data['block']
            block_id = id(block)
            
            # Skip blocks already processed as pure heading blocks
            if block_id in processed_blocks:
                continue
                
            # Check each line in this block for large bold text
            for line in block['lines']:
                line_id = id(line)
                if line_id in processed_lines:
                    continue
                    
                # Check if this line contains large bold text that should be a heading
                line_spans = line['spans']
                
                # Handle mixed content blocks - check individual lines for large bold text
                large_bold_spans = []
                for span in line_spans:
                    span_size = round(span['size'], 1)
                    span_bold = (span.get('flags', 0) & 2) or ('Bold' in span.get('font', ''))
                    
                    # Include if it's large (>= 15pt) and bold, or very large (>= 18pt)
                    if (span_size >= 15.0 and span_bold) or span_size >= 18.0:
                        large_bold_spans.append(span)
                
                if large_bold_spans:
                    # Extract text from large bold spans
                    heading_text = ''.join(span['text'] for span in large_bold_spans).strip()
                    heading_text = re.sub(r'\s+', ' ', heading_text)  # Normalize whitespace
                    
                    if (heading_text and len(heading_text) > 3 and
                        not is_non_meaningful_heading(heading_text) and
                        is_likely_heading(heading_text)):
                        
                        avg_span_size = sum(round(span['size'], 1) for span in large_bold_spans) / len(large_bold_spans)
                        
                        headings.append({
                            'text': heading_text,
                            'font_size': avg_span_size,
                            'bold': True,  # We know these are bold
                            'italic': any((s.get('flags', 0) & 1) or ('Italic' in s.get('font', '') or 'Oblique' in s.get('font', '')) for s in large_bold_spans),
                            'page': page_num
                        })
                        processed_lines.add(line_id)
        
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
                
                # Add as heading if meaningful - special handling for potential titles
                if (heading_text and len(heading_text) > 3):
                    
                    # Check if this could be a document title (first page, substantial text)
                    is_potential_title = (page_num == 0 and 
                                        block_main_size >= 10.0 and  # Lowered threshold
                                        len(heading_text) > 10 and    # Lowered threshold
                                        not re.match(r'^\d+\.', heading_text) and
                                        ('application' in heading_text.lower() or 'form' in heading_text.lower()))
                    
                    # Apply normal filtering for non-title headings
                    is_normal_heading = (not is_non_meaningful_heading(heading_text) and
                                       not is_text_from_image_region(block['bbox'], page) and
                                       is_likely_heading(heading_text))
                    
                    if is_potential_title or is_normal_heading:
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
            
            # Check if this is a heading: require much larger font, large+bold, or document-related text
            is_heading = False
            if first_size > body_text_size * 1.4:  # Sensitive threshold for good detection
                is_heading = True  
            elif (first_bold or first_italic) and first_size >= body_text_size * 1.2:  # Bold/italic with moderate size increase
                is_heading = True
            elif first_size >= body_text_size * 1.1:  # Sensitive to size increases
                # Check if this looks like a document title or structured content
                line_text = ' '.join(span['text'] for span in spans).strip()
                if (any(word in line_text.lower() for word in ['application', 'form', 'report', 'document', 'manual', 'guide', 'proposal', 'rfp', 'request', 'plan', 'business', 'library', 'digital', 'ontario', 'summary', 'background', 'approach', 'evaluation', 'appendix', 'phase', 'milestone', 'timeline', 'access', 'guidance', 'training', 'support', 'funding', 'overview', 'foundation', 'extension', 'equitable', 'shared', 'governance', 'purchasing', 'licensing', 'technological', 'preamble', 'membership', 'appointment', 'accountability', 'communication', 'financial', 'administrative', 'policies']) or
                    re.match(r'^\d+\.?\s+[A-Z]', line_text) or  # Numbered sections like "1. Introduction"
                    re.match(r'^\d+\.\d+\.?\s+[A-Z]', line_text) or  # Sub-sections like "2.1 Overview"
                    line_text.lower() in ['revision history', 'table of contents', 'acknowledgements', 'introduction', 'overview', 'references', 'summary', 'background', 'timeline', 'milestones', 'approach', 'evaluation', 'appendix'] or
                    re.match(r'^(revision|table|acknowledgement|introduction|overview|reference|summary|background|timeline|milestone|approach|evaluation|appendix)', line_text.lower()) or
                    line_text.endswith(':') and len(line_text) > 3 or  # Section headers ending with colon
                    re.match(r'^(for each|what could|phase [IVX]+)', line_text.lower()) or  # Specific patterns from RFP
                    len(line_text.split()) >= 2 and any(c.isupper() for c in line_text)):  # Multi-word with some capitals
                    is_heading = True
            # Special case for bold text regardless of size (but with length check)
            elif first_bold and len(' '.join(span['text'] for span in spans).strip()) > 5:  # Reduced minimum length for bold text
                line_text = ' '.join(span['text'] for span in spans).strip()
                # If it's bold and looks like a meaningful heading
                if (not line_text.isdigit() and 
                    not re.match(r'^(page|pg|p\.)\s*\d+', line_text.lower()) and
                    not re.match(r'^(fig|figure|table|tab)\s*\d+', line_text.lower()) and
                    len(line_text.split()) <= 10 and  # Not too long for a heading
                    (line_text.endswith(':') or  # Headers with colons
                     any(word in line_text.lower() for word in ['timeline', 'access', 'guidance', 'training', 'support', 'funding', 'equitable', 'shared', 'local', 'provincial', 'technological', 'preamble', 'terms', 'membership', 'appointment', 'chair', 'meetings', 'accountability', 'financial']))):  # Keywords from expected headings
                    is_heading = True
            
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
                    
                    if heading_text and not is_non_meaningful_heading(heading_text) and is_likely_heading(heading_text):
                        # Check if text is from image region using line bbox
                        line_bbox = line_data['spans'][0]['bbox'] if line_data['spans'] else None
                        if line_bbox and not is_text_from_image_region(line_bbox, page):
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
                   not current_heading['text'].endswith('!') and
                   len(current_heading['text'] + ' ' + page_headings[j]['text']) <= 100):  # Prevent overly long merged headings
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
