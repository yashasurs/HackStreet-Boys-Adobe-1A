
import fitz  # PyMuPDF
from collections import Counter


def extract_pdf_text_with_styles(pdf_path):
    doc = fitz.open(pdf_path)

    # First pass: collect all font sizes and line info, with page number, and per-page font size stats
    page_font_sizes = {}
    page_lines_info = {}
    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")['blocks']
        font_sizes = []
        lines = []
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
                lines.append((line_text, line_fonts, line_sizes, line['spans'], page_num))
        page_font_sizes[page_num] = font_sizes
        page_lines_info[page_num] = lines

    merged = []
    prev = None
    for page_num in range(len(doc)):
        font_sizes = page_font_sizes[page_num]
        lines_info = page_lines_info[page_num]
        if not font_sizes:
            continue
        size_counts = Counter(font_sizes)
        most_common_sizes = [size for size, _ in size_counts.most_common()]
        if most_common_sizes:
            body_font_size = most_common_sizes[0]
        else:
            body_font_size = None
        header_sizes = [size for size in sorted(most_common_sizes, reverse=True) if size != body_font_size]
        header_levels = {size: f"h{idx+1}" for idx, size in enumerate(header_sizes)}

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
            else:
                # Only treat as heading if ALL spans are bold or ALL are italic
                all_bold = all((span.get('flags', 0) & 2) or ('Bold' in span.get('font', '')) for span in spans)
                all_italic = all((span.get('flags', 0) & 1) or ('Italic' in span.get('font', '') or 'Oblique' in span.get('font', '')) for span in spans)
                if all_bold or all_italic:
                    header = 'body-bold-italic'
                else:
                    header = None
            if header is None:
                prev = None  # Reset prev so headings separated by body are not merged
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
    input_dir = "input"
    output_dir = "output"
    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(".pdf"):
            continue
        input_path = os.path.join(input_dir, filename)
        results = extract_pdf_text_with_styles(input_path)
        print(f"Results for {filename}:")
        print(json.dumps(results, indent=2, ensure_ascii=False))
        base = os.path.splitext(filename)[0]
        output_path = os.path.join(output_dir, f"{base}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
