
import fitz  # PyMuPDF
from collections import Counter


def extract_pdf_text_with_styles(pdf_path):
    doc = fitz.open(pdf_path)
    elements = []
    font_sizes = []
    lines_info = []

    # First pass: collect all font sizes and line info, with page number
    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")['blocks']
        for b in blocks:
            if b['type'] != 0:
                continue
            for line in b['lines']:
                line_text = "".join([span['text'] for span in line['spans']]).strip()
                if not line_text:
                    continue
                line_fonts = [span['font'] for span in line['spans']]
                line_sizes = [round(span['size'], 1) for span in line['spans']]
                font_sizes.extend(line_sizes)
                lines_info.append((line_text, line_fonts, line_sizes, line['spans'], page_num))

    if not font_sizes:
        return []
    size_counts = Counter(font_sizes)
    most_common_sizes = [size for size, _ in size_counts.most_common()]
    # Exclude the most common font size from being considered a heading unless bold/italic
    if most_common_sizes:
        body_font_size = most_common_sizes[0]
    else:
        body_font_size = None
    header_sizes = [size for size in sorted(most_common_sizes, reverse=True) if size != body_font_size]
    header_levels = {size: f"h{idx+1}" for idx, size in enumerate(header_sizes)}

    # Second pass: extract text with style info
    merged = []
    prev = None
    for line_text, line_fonts, line_sizes, spans, page_num in lines_info:
        if not line_text:
            continue
        # Heuristic: skip lines that are likely part of tables
        if len(spans) > 3:
            continue
        if max(line_text.count("\t"), line_text.count("  ")) > 2:
            continue
        if line_sizes:
            main_size = Counter(line_sizes).most_common(1)[0][0]
        else:
            main_size = None
        bold = any(span.get('flags', 0) & 2 for span in spans) or any('Bold' in f for f in line_fonts)
        italic = any(span.get('flags', 0) & 1 for span in spans) or any('Italic' in f or 'Oblique' in f for f in line_fonts)
        if main_size != body_font_size:
            header = header_levels.get(main_size)
        elif bold or italic:
            header = 'body-bold-italic'
        else:
            header = None
        if header is None:
            continue
        # Merge consecutive headings with same style and page
        key = (header, main_size, bold, italic, page_num)
        if prev and prev['key'] == key:
            prev['text'] += ' ' + line_text
        else:
            prev = {
                'text': line_text,
                'font_size': main_size,
                'bold': bold,
                'italic': italic,
                'header': header,
                'page': page_num,
                'key': key
            }
            merged.append(prev)
    # Remove the 'key' used for merging
    for el in merged:
        del el['key']
    return merged


if __name__ == "__main__":
    import json
    import os
    input_path = "input/file03.pdf"
    results = extract_pdf_text_with_styles(input_path)
    print(json.dumps(results, indent=2, ensure_ascii=False))
    # Write to output directory with same base filename but .json extension
    base = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join("output", f"{base}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
