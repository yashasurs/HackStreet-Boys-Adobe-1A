# PDF Text Extraction with Docker

This application extracts text and headings from PDF files and generates structured JSON output with document titles and hierarchical outlines.

## Prerequisites

- Docker installed on your system
- PDF files you want to process
- AMD64 (x86_64) architecture support

## Quick Start

### 1. Build the Docker Image (AMD64 Compatible)

```bash
docker build --platform linux/amd64 -t mysolutionname:somerandomidentifier .
```

### 2. Prepare Your PDF Files

Create an `input` directory and place your PDF files there:

```bash
mkdir input
# Copy your PDF files to the input directory
```

### 3. Run the Container (Offline Mode)

The container runs completely offline with no network access:

```bash
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none mysolutionname:somerandomidentifier
```

### Windows PowerShell Commands

If you're using Windows PowerShell, use these commands instead:

#### Build the image:
```powershell
docker build --platform linux/amd64 -t mysolutionname:somerandomidentifier .
```

#### Run the container:
```powershell
docker run --rm -v "${PWD}/input:/app/input" -v "${PWD}/output:/app/output" --network none mysolutionname:somerandomidentifier
```

## Docker Commands Explained

### Build Commands
- `docker build --platform linux/amd64 -t mysolutionname:somerandomidentifier .` - Build for AMD64 architecture
- `--platform linux/amd64` - Explicitly specify AMD64 platform compatibility

### Run Commands
- `--rm` - Automatically remove container when it exits
- `-v $(pwd)/input:/app/input` - Mount local input directory to container
- `-v $(pwd)/output:/app/output` - Mount local output directory to container
- `--network none` - Run completely offline with no network access
- Container processes all PDFs automatically from `/app/input` to `/app/output`

## Architecture Requirements

- **CPU Architecture**: AMD64 (x86_64) 
- **No GPU dependencies**
- **Model size**: ≤ 200MB
- **Offline operation**: No network/internet calls required
- **Platform**: linux/amd64 compatible

### Management Commands
- `docker ps` - List running containers
- `docker ps -a` - List all containers (including stopped)
- `docker logs pdf-processor` - View logs from named container
- `docker stop pdf-processor` - Stop the background container
- `docker rm pdf-processor` - Remove the container
- `docker images` - List Docker images
- `docker rmi pdf-extractor` - Remove the image

## Directory Structure

```
.
├── Dockerfile
├── .dockerignore
├── requirements.txt
├── main.py
├── extract_text.py
├── format.py
├── input/           # Place your PDF files here
│   ├── document1.pdf
│   └── document2.pdf
└── output/          # JSON results will be saved here
    ├── document1.json
    └── document2.json
```

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

## Troubleshooting

### Container won't start
- Check if Docker is running: `docker version`
- Verify the image was built: `docker images`

### No output files generated
- Ensure PDF files are in the `input` directory
- Check container logs: `docker logs <container-name>`
- Verify volume mounts are correct

### Permission issues (Linux/Mac)
```bash
# Fix ownership of output files
sudo chown -R $USER:$USER output/
```

### Windows path issues
Use forward slashes in paths or escape backslashes:
```powershell
docker run --rm -v "C:/path/to/input:/app/input" -v "C:/path/to/output:/app/output" pdf-extractor
```

## Development

### Running without Docker
```bash
pip install -r requirements.txt
python main.py
```

### Building for production
```bash
docker build --target production -t pdf-extractor:prod .
```
