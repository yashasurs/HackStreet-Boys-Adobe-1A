import os
import json
import re
import numpy as np
import pandas as pd
from extract_text import extract_font_data

INPUT_DIR = "input"
OUTPUT_DIR = "output"

def is_likely_heading(text, is_bold, font_size, avg_font_size):
    """
    Determine if a text line is likely to be a heading based on various criteria.
    
    Args:
        text (str): The text content
        is_bold (bool): Whether the text is bold
        font_size (float): Font size of the text
        avg_font_size (float): Average font size in the document
        
    Returns:
        bool: True if likely a heading, False otherwise
    """
    # Filter out very short text (likely not headings)
    if len(text.strip()) < 3:
        return False
    
    # Filter out single numbers or page numbers
    if re.match(r'^\d{1,3}$', text.strip()):
        return False
    
    # Filter out dates in various formats
    if re.match(r'^\w+\s+\d{1,2}(,\s+\d{4})?$', text.strip()):  # "March 2003", "April 11, 2003"
        return False
    
    # Filter out standalone ordinal numbers
    if re.match(r'^\d+(st|nd|rd|th)$', text.strip()):
        return False
    
    # Filter out single punctuation marks
    if re.match(r'^[^\w\s]*$', text.strip()):
        return False
    
    # Filter out common footer/header patterns
    if re.match(r'^(RFP:|Page \d+|Copyright|©)', text.strip()):
        return False
    
    # Must be either bold OR significantly larger than average font size
    is_large_font = font_size > avg_font_size * 1.1
    
    # Additional criteria for headings
    is_title_case = text.strip().istitle() or text.strip().isupper()
    starts_with_number = bool(re.match(r'^\d+\.', text.strip()))  # "1. Introduction"
    
    # Consider it a heading if it meets multiple criteria
    criteria_score = sum([
        is_bold,
        is_large_font,
        is_title_case,
        starts_with_number,
        len(text.strip()) > 10 and len(text.strip()) < 100  # Reasonable heading length
    ])
    
    return criteria_score >= 2

def extract_title_and_headings(font_data):
    """
    Extract the main title and organize headings hierarchically.
    
    Args:
        font_data (list): List of font data dictionaries
        
    Returns:
        tuple: (title_text, headings_list)
    """
    if not font_data:
        return None, []
    
    df = pd.DataFrame(font_data)
    
    # Calculate average font size for filtering
    avg_font_size = df["size"].mean()
    
    # Get unique font sizes and sort them
    unique_sizes = sorted(df["size"].unique(), reverse=True)
    
    # Create a more granular level mapping based on font sizes
    size_to_level = {}
    current_level = 1
    
    for size in unique_sizes:
        if current_level <= 6:  # Limit to H1-H6
            size_to_level[size] = f"H{current_level}"
            current_level += 1
        else:
            size_to_level[size] = "H6"  # Cap at H6
    
    df["level"] = df["size"].map(size_to_level)
    
    # Filter for likely headings using improved heuristics
    heading_mask = df.apply(
        lambda row: is_likely_heading(
            row["text"], 
            row["bold"], 
            row["size"], 
            avg_font_size
        ), 
        axis=1
    )
    
    df_headings = df[heading_mask].copy()
    
    # Remove duplicates (same text appearing multiple times)
    df_headings = df_headings.drop_duplicates(subset=['text'], keep='first')
    
    # Sort by page and then by position (using bbox if available)
    df_headings = df_headings.sort_values(['page', 'size'], ascending=[True, False])
    
    # Extract title (first/largest heading on first page)
    title_text = None
    if not df_headings.empty:
        # Find the largest text on the first page as title
        first_page_headings = df_headings[df_headings['page'] == 1]
        if not first_page_headings.empty:
            title_candidate = first_page_headings.iloc[0]
            title_text = title_candidate['text'].strip()
            # Remove the title from headings list
            df_headings = df_headings[df_headings['text'] != title_text]
    
    # Build headings list
    headings = []
    for _, row in df_headings.iterrows():
        headings.append({
            "level": row["level"],
            "text": row["text"].strip(),
            "page": row["page"]
        })

    return title_text, headings

def process_pdf(file_path):
    """
    Process a PDF file to extract headings and create an outline.
    
    Args:
        file_path (str): Path to the PDF file
        
    Returns:
        dict: Dictionary containing title and outline, or None if no data found
    """
    font_data = extract_font_data(file_path)
    if not font_data:
        return None

    title, headings = extract_title_and_headings(font_data)
    
    # Use filename as fallback if no title found
    if not title:
        title = os.path.basename(file_path).replace('.pdf', '')

    return {
        "title": title,
        "outline": headings
    }

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for filename in os.listdir(INPUT_DIR):
        if filename.lower().endswith(".pdf"):
            input_path = os.path.join(INPUT_DIR, filename)
            print(f"Processing {filename}...")

            result = process_pdf(input_path)
            if result:
                output_path = os.path.join(OUTPUT_DIR, filename.replace(".pdf", ".json"))
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=4)
                print(f"Saved to {output_path}")
            else:
                print(f"No extractable data found in {filename}")

if __name__ == "__main__":
    main()
