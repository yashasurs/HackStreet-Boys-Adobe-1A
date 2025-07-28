# PDF Structure Extraction Tool

This is a comprehensive PDF text extraction and analysis tool that identifies document titles and hierarchical heading structures from PDF files. It uses PyMuPDF to process documents and generates standardized JSON output with document titles and structured outlines following a predefined schema.

## Project Overview

The tool analyzes PDF documents to:
- Extract document titles from the largest font sizes on the first page
- Identify hierarchical headings (H1-H4) based on font size, styling, and positioning
- Generate structured JSON output following a standardized schema
- Process multiple PDFs in batch mode
- Run completely offline with no network dependencies

## Key Features

- **Intelligent Title Detection**: Identifies document titles from header regions and largest fonts
- **Hierarchical Heading Analysis**: Assigns H1-H4 levels based on font size and formatting hierarchy  
- **Schema-Compliant Output**: Generates JSON following the defined output schema
- **Batch Processing**: Processes multiple PDF files automatically
- **Dockerized Deployment**: Cross-platform compatibility with AMD64 architecture
- **Offline Operation**: No network calls or external dependencies required
- **Fragment Reconstruction**: Handles overlapping/fragmented text spans intelligently

## Project Structure

```
HackStreet-Boys-Adobe-1A/
├── Dockerfile                  # Container configuration
├── requirements.txt            # Python dependencies
├── main.py                     # Entry point script
├── extract_text.py             # PDF text extraction logic
├── format.py                   # JSON formatting and hierarchy logic
├── temp.py                     # Development utility
├── sample_dataset/             # Example files and schema
│   ├── schema/output_schema.json
│   ├── outputs/sample_report.json
│   └── pdfs/                   # Sample PDF files
├── input/                      # Place your PDF files here
└── output/                     # Generated JSON files appear here
```

## How It Works

1. **PDF Analysis**: The `extract_text.py` module uses PyMuPDF to extract text with detailed font metadata
2. **Heading Detection**: Identifies potential headings based on font size, bold/italic styling, and positioning
3. **Title Extraction**: Finds document titles from header regions and largest fonts on the first page
4. **Hierarchy Assignment**: The `format.py` module assigns H1-H4 levels based on font size relationships
5. **JSON Generation**: Creates structured output following the schema in `sample_dataset/schema/output_schema.json`
6. **Batch Processing**: The `main.py` entry point processes all PDFs in the input directory

## Docker Usage

### Build the image
```bash
# Linux/macOS
docker build --platform linux/amd64 -t pdf-extractor:latest .

# Windows PowerShell
docker build --platform linux/amd64 -t pdf-extractor:latest .
```

### Run the container
```bash
# Linux/macOS
mkdir -p input output
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none pdf-extractor:latest

# Windows PowerShell
New-Item -ItemType Directory -Force -Path input, output
docker run --rm -v "${PWD}/input:/app/input" -v "${PWD}/output:/app/output" --network none pdf-extractor:latest
```

### Usage Steps
1. Build the Docker image using the command above
2. Create `input` and `output` directories
3. Place your PDF files in the `input` directory
4. Run the container
5. Check the `output` directory for generated JSON files

## Architecture Requirements

- **CPU Architecture**: AMD64 (x86_64) 
- **No GPU dependencies**
- **Model size**: ≤ 200MB
- **Offline operation**: No network/internet calls required
- **Platform**: linux/amd64 compatible

## Output Format

The application generates JSON files with the following structure:

```json
{
  "title": "Document Title",
  "outline": [
    {
      "level": "H1",
      "text": "Chapter 1: Introduction",
      "page": 0
    },
    {
      "level": "H2", 
      "text": "1.1 Overview",
      "page": 1
    }
  ]
}
```

## Usage Instructions

1. **Prerequisites**: Ensure Docker is installed on your system
2. **Build**: Use the build commands above to create the Docker image
3. **Prepare**: Create `input` and `output` directories in your project folder
4. **Add Files**: Place your PDF files in the `input` directory
5. **Run**: Execute the run command for your operating system
6. **Results**: Check the `output` directory for generated JSON files

Each PDF file will be processed and a corresponding JSON file will be created with the same name but `.json` extension.

## Core Components

### main.py
Entry point script that:
- Scans the `/app/input` directory for PDF files
- Processes each PDF using the extraction pipeline
- Saves structured JSON output to `/app/output` directory
- Provides progress feedback and error handling

### extract_text.py
Core extraction engine that:
- Uses PyMuPDF to parse PDF documents
- Identifies potential headings based on font size and styling
- Handles fragmented/overlapping text reconstruction
- Filters out non-meaningful content (page numbers, artifacts)

### format.py
Formatting and structuring module that:
- Assigns hierarchical heading levels (H1-H4)
- Extracts document titles from first page content
- Creates schema-compliant JSON output
- Implements intelligent heading level assignment based on font hierarchy


## Architecture Requirements

- **CPU Architecture**: AMD64 (x86_64) 
- **No GPU dependencies**
- **Model size**: ≤ 200MB
- **Offline operation**: No network/internet calls required
- **Platform**: linux/amd64 compatible
