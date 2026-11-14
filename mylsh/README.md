# mylsh

### A Lightweight Python Toolkit for AI Engineers

**Build. Experiment. Integrate. Innovate.**

`mylsh` is a Python toolkit specially designed for AI engineers and developers. Its goal is to simplify the development of AI applications by providing reusable, lightweight, and easy-to-integrate components.

Rather than focusing on a single AI task, `mylsh` aims to bring essential AI engineering utilities together in one ecosystem.

Whether you are developing Retrieval-Augmented Generation (RAG) applications, working with LLMs, processing data, building intelligent workflows, or experimenting with AI systems, `mylsh` aims to make your development process simpler.

---

## Vision

To create a unified Python ecosystem that helps AI engineers build, manage, and scale AI applications with less complexity and minimal configuration.

## Why mylsh?

AI application development often requires multiple libraries, tools, and configurations.

`mylsh` aims to reduce this complexity by providing:

- Simple and developer-friendly APIs.
- Lightweight and reusable components.
- Minimal configuration.
- Modular architecture.
- Easy integration with existing AI frameworks.
- Tools designed specifically for AI engineering workflows.
- Flexibility to build custom AI applications.

## Core Areas

`mylsh` is designed to grow across multiple areas of AI engineering.

| Area | Purpose |
|---|---|
| Document Processing | Load and process different document formats |
| RAG Engineering | Build retrieval-augmented generation pipelines |
| Text Processing | Clean, transform, and prepare text data |
| Chunking | Split documents into meaningful chunks |
| Embeddings | Convert text into vector representations |
| Vector Database Integration | Store and retrieve vector embeddings |
| LLM Utilities | Simplify common LLM operations |
| Prompt Engineering | Manage and organize prompts |
| AI Workflows | Build reusable AI processing workflows |
| Data Processing | Prepare data for AI applications |
| Multimodal AI | Work with text, images, audio, and other data types |

*These are the intended development areas of the project, not a claim that every module is already implemented.*

---

## Current Features

### Document Loader

The first component of `mylsh` is its universal document loader.

It automatically detects file formats and extracts their content using a unified interface.

**Supported formats:**

| Document Type | Extensions | Extra needed |
|---|---|---|
| Text / Markdown | `.txt`, `.md`, `.markdown`, `.rst` | none |
| Source code | `.py`, `.java`, `.js`, `.ts`, `.cpp`, `.c`, `.h`, `.cs`, `.go`, `.rs`, `.php`, `.sql`, `.sh`, `.css` | none |
| CSV / TSV | `.csv`, `.tsv` | none |
| JSON / XML | `.json`, `.xml` | none |
| HTML | `.html`, `.htm` | none |
| Email | `.eml` | none |
| PDF | `.pdf` | `pdf` |
| Word | `.docx` | `word` |
| Legacy Word | `.doc` | LibreOffice or Antiword (system) |
| Excel | `.xlsx` | `excel` |
| Legacy Excel | `.xls` | `excel` |
| PowerPoint | `.pptx` | `powerpoint` |
| Legacy PowerPoint | `.ppt` | LibreOffice (system) |
| YAML | `.yaml`, `.yml` | `yaml` |
| RTF | `.rtf` | `rtf` |
| EPUB | `.epub` | `epub` |
| Images (OCR) | `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tiff`, `.tif`, `.webp` | `image` + Tesseract (system) |
| Audio (transcription) | `.mp3`, `.wav`, `.m4a`, `.ogg`, `.flac` | `audio` |
| Video (frame OCR) | `.mp4`, `.avi`, `.mov`, `.mkv` | `video` + Tesseract (system) |

### Document Loader Highlights

- Automatic file type detection.
- Unified document output.
- Metadata extraction.
- Multiple file loading.
- Directory-based document loading.
- Lazy dependency imports: install only what you need.
- Clear errors for missing dependencies and corrupt files.
- No LangChain dependency.

---

## Installation

```bash
pip install mylsh                 # core (text, CSV, JSON, XML, HTML, EML, code)
pip install "mylsh[pdf]"          # add PDF support
pip install "mylsh[pdf,word]"     # combine extras
pip install "mylsh[all]"          # PDF, Office, YAML, RTF, EPUB, image OCR
pip install "mylsh[audio]"        # audio transcription (not part of "all")
pip install "mylsh[video]"        # video frame OCR (not part of "all")
```

Available extras: `pdf`, `word`, `excel`, `powerpoint`, `epub`, `rtf`, `yaml`, `image`, `audio`, `video`, `all`.

Some formats need a system program as well (see **Dependencies** below).

For local development:

```bash
pip install -e ".[all,dev]"
pytest
```

---

## Quick Start

### Load a Document

```python
from mylsh import document_loader

documents = document_loader.load("report.pdf")

for document in documents:
    print(document.page_content)
    print(document.metadata)
```

### Load Multiple Documents

```python
from mylsh import document_loader

documents = document_loader.load_many([
    "report.pdf",
    "notes.txt",
    "data.csv",
    "document.docx"
])
```

### Load an Entire Directory

```python
documents = document_loader.load_directory(
    "documents/",
    recursive=True,            # default
    extensions=[".pdf", "md"], # optional filter
    ignore_errors=True         # skip files that fail to parse
)
```

Hidden files and unsupported file types are skipped automatically.

### Get Supported Formats

```python
formats = document_loader.supported_formats()

print(formats)
```

---

## Example: RAG Development Workflow

`mylsh` aims to provide reusable components for building RAG applications.

A typical RAG workflow looks like this:

1. Document ingestion.
2. Text extraction.
3. Text cleaning and preprocessing.
4. Document chunking.
5. Embedding generation.
6. Vector database storage.
7. Similarity search and retrieval.
8. LLM-based answer generation.

The document loader provides the initial ingestion layer for this workflow.

---

## Development Roadmap

The following modules represent the planned evolution of `mylsh`.

| Module | Planned functionality |
|---|---|
| `document_loader` | Universal document ingestion |
| `text_processor` | Text cleaning and preprocessing |
| `text_splitter` | Intelligent document chunking |
| `embeddings` | Embedding generation utilities |
| `vector_store` | Vector database integrations |
| `retriever` | Information retrieval utilities |
| `prompt_manager` | Prompt creation and management |
| `llm` | LLM integration utilities |
| `rag` | RAG pipeline components |
| `multimodal` | Multimodal data processing |
| `ai_workflow` | Reusable AI workflows |

The roadmap may evolve as the project develops.

---

## Design Philosophy

`mylsh` follows a few important principles:

**1. Simplicity**

Easy-to-understand APIs that reduce unnecessary configuration.

**2. Modularity**

Each component should work independently and integrate with other components.

**3. Lightweight**

Avoid unnecessary dependencies and keep the core package minimal.

**4. Flexibility**

Give AI engineers the freedom to customize and extend components.

**5. Developer Experience**

Focus on readable code, useful documentation, and predictable behavior.

---

## Dependencies

The core package aims to remain lightweight.

Optional dependencies are installed according to the functionality required.

Some formats also require external system programs:

| Program | Needed for |
|---|---|
| Tesseract OCR | images and video (`sudo apt install tesseract-ocr`) |
| LibreOffice | legacy `.doc` and `.ppt` |
| Antiword (optional) | faster legacy `.doc` loading |

## Output and Errors

Every loader returns a `list` of `Document` objects, each with `page_content` and `metadata`. Metadata always contains `source`, `file_name` and `file_type`, plus format-specific keys: `page` (PDF), `slide` (PowerPoint), `sheet` (Excel), `row` (CSV/TSV), `chapter` (EPUB), `subject`/`from`/`to`/`date` (EML), `start`/`end` (audio) and `timestamp` (video). Empty files return an empty list.

| Exception | When |
|---|---|
| `FileNotFoundError` | the file or directory does not exist |
| `ValueError` | unsupported extension, wrong path type, or a corrupt file |
| `ImportError` | an optional package or system program is missing |

## Documentation

A full PDF user guide is included in the source distribution and in the project repository as `docs/mylsh-user-guide.pdf`.

---

## Creator

**Parasuraman E**

AI Engineering | Python Development | RAG | Generative AI

### Contact

- **Email:** g63909731@gmail.com

---

## Source Code

https://github.com/Parasuraman24/mylsh

---

## Contributing

Contributions, suggestions, bug reports, and feature requests are welcome.

If you are interested in improving AI engineering tools, feel free to contribute to `mylsh`.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

**Developed by Parasuraman E**

*Empowering AI engineers with simple, lightweight, and reusable Python tools.*

**mylsh — Your toolkit for AI engineering.**