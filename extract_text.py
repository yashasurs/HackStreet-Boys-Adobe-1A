import fitz  # PyMuPDF

def extract_font_data(pdf_path):
    """
    Extract font and text data from a PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        list: List of dictionaries containing text data with font information
    """
    doc = fitz.open(pdf_path)
    font_data = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            for line in block.get("lines", []):
                line_text = ""
                line_spans = []
                
                # Combine spans in the same line to get complete text
                for span in line["spans"]:
                    text = span["text"].strip()
                    if text:
                        line_text += text + " "
                        line_spans.append(span)
                
                line_text = line_text.strip()
                if not line_text:
                    continue
                
                # Use the first span's properties for the line
                if line_spans:
                    first_span = line_spans[0]
                    font_data.append({
                        "text": line_text,
                        "size": first_span["size"],
                        "font": first_span["font"],
                        "bold": "Bold" in first_span["font"] or "bold" in first_span["font"].lower(),
                        "page": page_num + 1,
                        "bbox": line["bbox"]  # Bounding box for position info
                    })
    
    doc.close()
    print(font_data)
    return font_data
