import json
import os
from extract_text import extract_pdf_text_with_styles
from collections import Counter


def assign_heading_levels(headings):
    """
    Assign heading levels (H1, H2, H3, H4) based on font sizes and formatting.
    All headings are included in the outline with proper hierarchical levels.
    """
    if not headings:
        return {"title": "", "outline": []}
    
    # Debug: Print all headings with their font sizes
    print("DEBUG: All headings found:")
    for i, h in enumerate(headings):
        print(f"  {i}: '{h['text'][:50]}...' - Size: {h['font_size']}, Bold: {h['bold']}, Page: {h['page']}")
    
    # Group headings by their characteristics (font_size, bold, italic)
    heading_styles = {}
    for heading in headings:
        style_key = (heading['font_size'], heading['bold'], heading['italic'])
        if style_key not in heading_styles:
            heading_styles[style_key] = []
        heading_styles[style_key].append(heading)
    
    # Sort styles by font size (descending), then by bold/italic priority
    sorted_styles = sorted(heading_styles.keys(), key=lambda x: (x[0], x[1], x[2]), reverse=True)
    
    print(f"DEBUG: Found {len(sorted_styles)} different heading styles:")
    for style in sorted_styles:
        count = len(heading_styles[style])
        print(f"  Font {style[0]}, Bold: {style[1]}, Italic: {style[2]} - {count} headings")
    
    # Find the document title - look for a clear document title on the first page
    title = ""
    title_candidates = []
    
    # Look for headings on the first page that could be document titles
    first_page_headings = [h for h in headings if h['page'] == 0]
    if first_page_headings:
        # Sort by font size (largest first)
        first_page_headings.sort(key=lambda x: x['font_size'], reverse=True)
        
        # Get the largest font size on the first page
        largest_font_size = first_page_headings[0]['font_size']
        
        # Find ALL headings with the largest font size on the first page
        largest_headings = [h for h in first_page_headings if h['font_size'] == largest_font_size]
        
        # Check if these headings can be combined into a title
        valid_title_parts = []
        for heading in largest_headings:
            # Check if this heading looks like a document title component
            if (len(heading['text']) > 5 and  # Reasonable minimum length
                not heading['text'].isdigit() and  # Not just a number
                not heading['text'].endswith(':') and  # Not a section label
                '.' not in heading['text'][:5] and  # Not a numbered section
                not heading['text'].startswith(('1.', '2.', '3.', '4.', '5.'))):  # Not numbered heading
                valid_title_parts.append(heading['text'])
        
        # Combine valid title parts
        if valid_title_parts:
            if len(valid_title_parts) == 1:
                title = valid_title_parts[0]
            else:
                # Join multiple parts with appropriate separator
                title = ' - '.join(valid_title_parts)
    
    print(f"DEBUG: Selected title: '{title}'")
    
    # Filter out all title components from headings for level assignment
    title_parts = title.split(' - ') if title else []
    non_title_headings = []
    for heading in headings:
        if heading['text'] not in title_parts:
            non_title_headings.append(heading)
    
    print(f"DEBUG: Remaining headings after excluding title: {len(non_title_headings)}")
    
    # Re-group the remaining headings by their characteristics  
    remaining_heading_styles = {}
    for heading in non_title_headings:
        style_key = (heading['font_size'], heading['bold'], heading['italic'])
        if style_key not in remaining_heading_styles:
            remaining_heading_styles[style_key] = []
        remaining_heading_styles[style_key].append(heading)
    
    # Sort styles by font size (descending), then by bold/italic priority
    remaining_sorted_styles = sorted(remaining_heading_styles.keys(), key=lambda x: (x[0], x[1], x[2]), reverse=True)
    
    # Assign heading levels based on font size hierarchy of remaining headings
    # Group similar font sizes together to create more logical heading levels
    level_mapping = {}
    available_levels = ['H1', 'H2', 'H3', 'H4']
    
    if not remaining_sorted_styles:
        # No headings to process
        pass
    elif len(remaining_sorted_styles) <= 4:
        # If we have 4 or fewer styles, assign them directly
        for i, style in enumerate(remaining_sorted_styles):
            level_mapping[style] = available_levels[i]
    else:
        # If we have more than 4 styles, group them intelligently
        # Extract just the font sizes for grouping
        font_sizes = [style[0] for style in remaining_sorted_styles]
        unique_font_sizes = sorted(list(set(font_sizes)), reverse=True)
        
        # Create font size ranges for each heading level
        if len(unique_font_sizes) <= 4:
            # If we have 4 or fewer unique font sizes, assign directly
            size_to_level = {}
            for i, size in enumerate(unique_font_sizes):
                if i < len(available_levels):
                    size_to_level[size] = available_levels[i]
                else:
                    size_to_level[size] = 'H4'
        else:
            # Group font sizes into 4 ranges more intelligently
            size_to_level = {}
            
            # If we have many unique font sizes, group them into 4 logical groups
            if len(unique_font_sizes) > 4:
                # Divide into roughly equal groups, but prioritize logical breaks
                group_size = len(unique_font_sizes) // 4
                remainder = len(unique_font_sizes) % 4
                
                # Assign sizes to levels, starting with largest
                level_assignments = ['H1', 'H2', 'H3', 'H4']
                current_index = 0
                
                for level_idx, level in enumerate(level_assignments):
                    # Calculate how many sizes this level should get
                    sizes_for_this_level = group_size + (1 if level_idx < remainder else 0)
                    
                    # Assign the next 'sizes_for_this_level' font sizes to this level
                    for i in range(sizes_for_this_level):
                        if current_index < len(unique_font_sizes):
                            size_to_level[unique_font_sizes[current_index]] = level
                            current_index += 1
            else:
                # If we have 4 or fewer unique sizes, assign them directly
                for i, size in enumerate(unique_font_sizes):
                    if i < len(available_levels):
                        size_to_level[size] = available_levels[i]
                    else:
                        size_to_level[size] = 'H4'
        
        # Now map each style to its level based on font size
        for style in remaining_sorted_styles:
            font_size = style[0]
            level_mapping[style] = size_to_level[font_size]
    
    print(f"DEBUG: Level mapping for remaining headings:")
    for style, level in level_mapping.items():
        print(f"  {style} -> {level}")
    
    # Create the outline - only include non-title headings with their proper levels
    outline = []
    for heading in non_title_headings:
        style_key = (heading['font_size'], heading['bold'], heading['italic'])
        level = level_mapping.get(style_key, 'H4')
        
        outline.append({
            "level": level,
            "text": heading['text'],
            "page": heading['page']  # Keep 0-indexed page numbering
        })
    
    return {
        "title": title,
        "outline": outline
    }


def process_pdf_to_structured_format(pdf_path):
    """
    Process a PDF and return structured format with title and hierarchical outline.
    """
    # Extract headings using the existing function
    headings = extract_pdf_text_with_styles(pdf_path)
    
    # Assign heading levels and extract title
    structured_data = assign_heading_levels(headings)
    
    return structured_data


if __name__ == "__main__":
    input_dir = "input"
    output_dir = "output"
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(".pdf"):
            continue
            
        input_path = os.path.join(input_dir, filename)
        
        print(f"Processing {filename}...")
        
        try:
            # Process the PDF
            structured_data = process_pdf_to_structured_format(input_path)
            
            # Print results
            print(f"Results for {filename}:")
            print(json.dumps(structured_data, indent=2, ensure_ascii=False))
            
            # Save to file
            base = os.path.splitext(filename)[0]
            output_path = os.path.join(output_dir, f"{base}_structured.json")
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(structured_data, f, indent=2, ensure_ascii=False)
                
            print(f"Saved structured output to: {output_path}")
            print("-" * 50)
            
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            continue
