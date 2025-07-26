#!/usr/bin/env python3
"""
Main entry point for the PDF text extraction application.
This script processes all PDF files in the input directory and generates
structured JSON files with headings and titles in the output directory.

Designed for offline operation with no network dependencies.
"""

import os
import sys
import json

# Add current directory to Python path for imports
sys.path.insert(0, '/app')

try:
    from format import process_pdf_to_structured_format
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please ensure all required Python files are present.")
    sys.exit(1)


def main():
    """Main function to process all PDFs in the input directory."""
    input_dir = "/app/input"
    output_dir = "/app/output"
    
    # Check if input directory exists and has PDF files
    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist.")
        print("Please ensure the input directory is mounted to /app/input")
        sys.exit(1)
    
    # Get list of PDF files
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDF files found in '{input_dir}' directory.")
        print("Please place your PDF files in the input directory.")
        return 0  # Don't exit with error, just finish gracefully
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Found {len(pdf_files)} PDF file(s) to process:")
    for pdf_file in pdf_files:
        print(f"  - {pdf_file}")
    print()
    
    # Process each PDF file
    processed_count = 0
    failed_count = 0
    
    for filename in pdf_files:
        input_path = os.path.join(input_dir, filename)
        print(f"Processing: {filename}...")
        
        try:
            # Process the PDF
            structured_data = process_pdf_to_structured_format(input_path)
            
            # Save to file
            base = os.path.splitext(filename)[0]
            output_path = os.path.join(output_dir, f"{base}.json")
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(structured_data, f, indent=2, ensure_ascii=False)
            
            print(f"  ✓ Successfully processed: {output_path}")
            processed_count += 1
            
        except Exception as e:
            print(f"  ✗ Failed to process {filename}: {str(e)}")
            failed_count += 1
    
    print(f"\nProcessing complete!")
    print(f"Successfully processed: {processed_count} files")
    if failed_count > 0:
        print(f"Failed to process: {failed_count} files")
    
    if processed_count > 0:
        print(f"Output files saved to '{output_dir}' directory.")
    else:
        print("No files were processed successfully.")
    
    # Always exit successfully to avoid Docker errors
    return 0


if __name__ == "__main__":
    sys.exit(main())
