
import os
import json
import csv
import re
import html
import importlib
import shutil
import subprocess
import tempfile
from email import policy
from email.parser import BytesParser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from html.parser import HTMLParser


# --------------------------------------------------
# Standard Document Format
# --------------------------------------------------

@dataclass
class Document:
    page_content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


# --------------------------------------------------
# HTML Text Extractor
# --------------------------------------------------

class HTMLTextExtractor(HTMLParser):

    _SKIP_TAGS = {"script", "style", "noscript", "head"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in self._SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._skip_depth:
            return
        value = data.strip()
        if value:
            self.text.append(value)

    def get_text(self):
        return "\n".join(self.text)


# --------------------------------------------------
# Main Document Loader
# --------------------------------------------------

class document_loader:

    SUPPORTED_FORMATS = {

        # Text documents
        ".txt", ".md", ".markdown", ".rst",

        # PDF and office documents
        ".pdf", ".docx", ".doc",
        ".pptx", ".ppt",
        ".xlsx", ".xls",

        # Structured data
        ".csv", ".tsv", ".json",
        ".xml", ".yaml", ".yml",

        # Web documents
        ".html", ".htm",

        # Other documents
        ".rtf", ".epub", ".eml",

        # Images
        ".png", ".jpg", ".jpeg",
        ".bmp", ".tiff", ".tif", ".webp",

        # Audio
        ".mp3", ".wav", ".m4a",
        ".ogg", ".flac",

        # Video
        ".mp4", ".avi", ".mov", ".mkv",

        # Source code
        ".py", ".java", ".js", ".ts",
        ".cpp", ".c", ".h", ".cs",
        ".go", ".rs", ".php", ".sql",
        ".sh", ".css"
    }

    @classmethod
    def load(cls, file_path: str) -> List[Document]:

        path = Path(file_path)

        # Check file existence
        if not path.exists():
            raise FileNotFoundError(
                f"File not found: {file_path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Expected a file, got: {file_path}"
            )

        extension = path.suffix.lower()

        # Check supported format
        if extension not in cls.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported file format: {extension}"
            )

        # Automatically select the loader
        loaders = {

            # Text
            ".txt": cls._load_text,
            ".md": cls._load_text,
            ".markdown": cls._load_text,
            ".rst": cls._load_text,

            # PDF
            ".pdf": cls._load_pdf,

            # Word
            ".docx": cls._load_docx,
            ".doc": cls._load_doc,

            # PowerPoint
            ".pptx": cls._load_pptx,
            ".ppt": cls._load_ppt,

            # Excel
            ".xlsx": cls._load_excel,
            ".xls": cls._load_xls,

            # CSV
            ".csv": cls._load_csv,
            ".tsv": cls._load_csv,

            # JSON
            ".json": cls._load_json,

            # XML
            ".xml": cls._load_xml,

            # YAML
            ".yaml": cls._load_yaml,
            ".yml": cls._load_yaml,

            # HTML
            ".html": cls._load_html,
            ".htm": cls._load_html,

            # RTF
            ".rtf": cls._load_rtf,

            # Email
            ".eml": cls._load_eml,

            # EPUB
            ".epub": cls._load_epub,

            # Images
            ".png": cls._load_image,
            ".jpg": cls._load_image,
            ".jpeg": cls._load_image,
            ".bmp": cls._load_image,
            ".tiff": cls._load_image,
            ".tif": cls._load_image,
            ".webp": cls._load_image,

            # Audio
            ".mp3": cls._load_audio,
            ".wav": cls._load_audio,
            ".m4a": cls._load_audio,
            ".ogg": cls._load_audio,
            ".flac": cls._load_audio,

            # Video
            ".mp4": cls._load_video,
            ".avi": cls._load_video,
            ".mov": cls._load_video,
            ".mkv": cls._load_video,

            # Source code
        }

        # Source-code files are plain text
        if extension not in loaders:
            loader = cls._load_text
        else:
            loader = loaders[extension]

        try:
            documents = loader(path)
        except (ImportError, FileNotFoundError):
            raise
        except Exception as exc:
            raise ValueError(
                f"Could not read '{path.name}' as {extension}: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        # Add common metadata
        for doc in documents:
            doc.metadata.update({
                "source": str(path.resolve()),
                "file_name": path.name,
                "file_type": extension
            })

        return documents

    @classmethod
    def load_many(
        cls,
        file_paths: Iterable[str],
        ignore_errors: bool = False
    ) -> List[Document]:
        """Load several files and return all documents in one list."""

        documents: List[Document] = []

        for file_path in file_paths:
            try:
                documents.extend(cls.load(file_path))
            except Exception:
                if not ignore_errors:
                    raise

        return documents

    @classmethod
    def load_directory(
        cls,
        directory: str,
        recursive: bool = True,
        extensions: Optional[Iterable[str]] = None,
        ignore_errors: bool = False
    ) -> List[Document]:
        """Load every supported file in a directory.

        Unsupported files and hidden files are skipped. Set
        ``ignore_errors=True`` to also skip files that fail to parse.
        """

        root = Path(directory)

        if not root.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        if not root.is_dir():
            raise ValueError(f"Expected a directory, got: {directory}")

        wanted = None
        if extensions is not None:
            wanted = {
                e.lower() if e.startswith(".") else "." + e.lower()
                for e in extensions
            }

        pattern = root.rglob("*") if recursive else root.glob("*")

        files = sorted(
            f for f in pattern
            if f.is_file()
            and not any(
                part.startswith(".")
                for part in f.relative_to(root).parts
            )
            and f.suffix.lower() in cls.SUPPORTED_FORMATS
            and (wanted is None or f.suffix.lower() in wanted)
        )

        return cls.load_many(files, ignore_errors=ignore_errors)

    @classmethod
    def supported_formats(cls) -> List[str]:
        """Return the sorted list of supported file extensions."""

        return sorted(cls.SUPPORTED_FORMATS)

    # --------------------------------------------------
    # Helper Functions
    # --------------------------------------------------

    _EXTRAS = {
        "pypdf": "pdf", "docx": "word", "openpyxl": "excel",
        "pandas": "excel", "xlrd": "excel", "pptx": "powerpoint",
        "ebooklib": "epub", "ebooklib.epub": "epub",
        "striprtf.striprtf": "rtf", "yaml": "yaml",
        "pytesseract": "image", "PIL.Image": "image",
        "faster_whisper": "audio", "cv2": "video",
    }

    @classmethod
    def _require(cls, package, feature):

        try:
            return importlib.import_module(package)

        except ImportError as exc:
            extra = cls._EXTRAS.get(package)
            hint = (
                f" Run: pip install \"mylsh[{extra}]\""
                if extra else ""
            )
            raise ImportError(
                f"Install '{package}' to load {feature}.{hint}"
            ) from exc

    @staticmethod
    def _convert_with_libreoffice(path, target_ext):
        """Convert a legacy Office file using LibreOffice; returns a temp dir
        and the converted file path."""

        office = shutil.which("soffice") or shutil.which("libreoffice")

        if office is None:
            raise ImportError(
                f"LibreOffice ('soffice') is required to load "
                f"'{path.suffix}' files. Install LibreOffice or convert "
                f"the file to .{target_ext} first."
            )

        tmp = tempfile.mkdtemp(prefix="mylsh_")

        subprocess.run(
            [office, "--headless", "--convert-to", target_ext,
             "--outdir", tmp, str(path)],
            check=True,
            capture_output=True,
            timeout=120
        )

        converted = Path(tmp) / (path.stem + "." + target_ext)

        if not converted.exists():
            raise ValueError(f"LibreOffice could not convert {path.name}")

        return tmp, converted

    @staticmethod
    def _read(path):

        return path.read_text(
            encoding="utf-8",
            errors="replace"
        )

    @staticmethod
    def _make_document(text, metadata=None):

        if not text.strip():
            return []

        return [
            Document(
                page_content=text,
                metadata=metadata or {}
            )
        ]

    # --------------------------------------------------
    # TXT / MD / SOURCE CODE
    # --------------------------------------------------

    @classmethod
    def _load_text(cls, path):

        return cls._make_document(
            cls._read(path)
        )

    # --------------------------------------------------
    # PDF
    # --------------------------------------------------

    @classmethod
    def _load_pdf(cls, path):

        try:
            pypdf = cls._require("pypdf", "PDF")

            reader = pypdf.PdfReader(str(path))

            documents = []

            for index, page in enumerate(reader.pages):

                text = page.extract_text() or ""

                documents.extend(
                    cls._make_document(
                        text,
                        {"page": index + 1}
                    )
                )

            return documents

        except ImportError:
            raise

    # --------------------------------------------------
    # DOCX
    # --------------------------------------------------

    @classmethod
    def _load_docx(cls, path):

        docx = cls._require("docx", "DOCX")

        document = docx.Document(str(path))

        content = []

        for paragraph in document.paragraphs:
            if paragraph.text.strip():
                content.append(paragraph.text)

        for table in document.tables:
            for row in table.rows:
                content.append(
                    " | ".join(cell.text for cell in row.cells)
                )

        return cls._make_document(
            "\n".join(content)
        )

    # --------------------------------------------------
    # Legacy DOC
    # --------------------------------------------------

    @classmethod
    def _load_doc(cls, path):

        antiword = shutil.which("antiword")

        if antiword:
            result = subprocess.run(
                [antiword, str(path)],
                capture_output=True,
                check=True,
                timeout=120
            )
            return cls._make_document(
                result.stdout.decode("utf-8", errors="replace")
            )

        tmp, converted = cls._convert_with_libreoffice(path, "docx")

        try:
            return cls._load_docx(converted)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # --------------------------------------------------
    # PPTX
    # --------------------------------------------------

    @classmethod
    def _load_pptx(cls, path):

        pptx = cls._require("pptx", "PPTX")

        presentation = pptx.Presentation(str(path))

        documents = []

        for index, slide in enumerate(presentation.slides):

            content = []

            for shape in slide.shapes:

                if shape.has_text_frame:
                    content.append(shape.text)

                if shape.has_table:
                    for row in shape.table.rows:
                        content.append(
                            " | ".join(
                                cell.text for cell in row.cells
                            )
                        )

            documents.extend(
                cls._make_document(
                    "\n".join(content),
                    {"slide": index + 1}
                )
            )

        return documents

    # --------------------------------------------------
    # Legacy PPT
    # --------------------------------------------------

    @classmethod
    def _load_ppt(cls, path):

        tmp, converted = cls._convert_with_libreoffice(path, "pptx")

        try:
            return cls._load_pptx(converted)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # --------------------------------------------------
    # EXCEL
    # --------------------------------------------------

    @classmethod
    def _load_excel(cls, path):

        openpyxl = cls._require("openpyxl", "Excel")

        workbook = openpyxl.load_workbook(
            str(path),
            read_only=True,
            data_only=True
        )

        documents = []

        for sheet in workbook.worksheets:

            rows = []

            for row in sheet.iter_rows(values_only=True):

                if all(value is None for value in row):
                    continue

                rows.append(
                    " | ".join(
                        "" if value is None else str(value)
                        for value in row
                    )
                )

            documents.extend(
                cls._make_document(
                    "\n".join(rows),
                    {"sheet": sheet.title}
                )
            )

        workbook.close()
        return documents

    # --------------------------------------------------
    # Legacy XLS
    # --------------------------------------------------

    @classmethod
    def _load_xls(cls, path):

        pandas = cls._require("pandas", "XLS")

        cls._require("xlrd", "XLS")

        workbook = pandas.ExcelFile(str(path), engine="xlrd")

        documents = []

        for sheet in workbook.sheet_names:

            frame = pandas.read_excel(
                workbook,
                sheet_name=sheet,
                dtype=str
            )

            documents.extend(
                cls._make_document(
                    frame.fillna("").to_string(index=False),
                    {"sheet": sheet}
                )
            )

        return documents

    # --------------------------------------------------
    # CSV / TSV
    # --------------------------------------------------

    @classmethod
    def _load_csv(cls, path):

        delimiter = "\t" if path.suffix.lower() == ".tsv" else ","

        documents = []

        with open(
            path,
            "r",
            encoding="utf-8-sig",
            errors="replace",
            newline=""
        ) as file:

            reader = csv.reader(
                file,
                delimiter=delimiter
            )

            rows = list(reader)

        if not rows:
            return []

        headers = rows[0]

        for index, row in enumerate(rows[1:], start=1):

            content = "\n".join(
                f"{headers[i]}: {value}"
                for i, value in enumerate(row)
                if i < len(headers) and value
            )

            documents.extend(
                cls._make_document(
                    content,
                    {"row": index + 1}
                )
            )

        return documents

    # --------------------------------------------------
    # JSON
    # --------------------------------------------------

    @classmethod
    def _load_json(cls, path):

        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        return cls._make_document(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False
            )
        )

    # --------------------------------------------------
    # XML
    # --------------------------------------------------

    @classmethod
    def _load_xml(cls, path):

        from xml.etree import ElementTree

        root = ElementTree.parse(path).getroot()

        return cls._make_document(
            "\n".join(
                line.strip()
                for line in ElementTree.tostring(
                    root,
                    encoding="unicode"
                ).splitlines()
                if line.strip()
            )
        )

    # --------------------------------------------------
    # YAML
    # --------------------------------------------------

    @classmethod
    def _load_yaml(cls, path):

        yaml = cls._require("yaml", "YAML")

        with open(path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        if data is None:
            return []

        return cls._make_document(
            json.dumps(data, indent=2, ensure_ascii=False, default=str)
        )

    # --------------------------------------------------
    # HTML
    # --------------------------------------------------

    @classmethod
    def _load_html(cls, path):

        parser = HTMLTextExtractor()

        parser.feed(cls._read(path))

        return cls._make_document(
            html.unescape(parser.get_text())
        )

    # --------------------------------------------------
    # RTF
    # --------------------------------------------------

    @classmethod
    def _load_rtf(cls, path):

        striprtf = cls._require("striprtf.striprtf", "RTF")

        content = striprtf.rtf_to_text(cls._read(path))

        return cls._make_document(content)

    # --------------------------------------------------
    # EPUB
    # --------------------------------------------------

    @classmethod
    def _load_epub(cls, path):

        ebooklib = cls._require("ebooklib", "EPUB")
        epub = cls._require("ebooklib.epub", "EPUB")

        book = epub.read_epub(str(path))

        documents = []

        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):

            parser = HTMLTextExtractor()
            parser.feed(item.get_content().decode(
                "utf-8", errors="replace"
            ))

            documents.extend(
                cls._make_document(
                    parser.get_text(),
                    {"chapter": item.get_name()}
                )
            )

        return documents

    # --------------------------------------------------
    # EML (email)
    # --------------------------------------------------

    @classmethod
    def _load_eml(cls, path):

        with open(path, "rb") as file:
            message = BytesParser(policy=policy.default).parse(file)

        body = message.get_body(preferencelist=("plain", "html"))
        text = ""

        if body is not None:
            text = body.get_content()
            if body.get_content_type() == "text/html":
                parser = HTMLTextExtractor()
                parser.feed(text)
                text = parser.get_text()

        metadata = {
            "subject": str(message.get("subject", "")),
            "from": str(message.get("from", "")),
            "to": str(message.get("to", "")),
            "date": str(message.get("date", "")),
        }

        return cls._make_document(text, metadata)

    # --------------------------------------------------
    # IMAGE / OCR
    # --------------------------------------------------

    @classmethod
    def _load_image(cls, path):

        pytesseract = cls._require(
            "pytesseract", "Image OCR"
        )

        pillow = cls._require("PIL.Image", "Image OCR")

        with pillow.open(path) as image:
            content = pytesseract.image_to_string(image)

        return cls._make_document(content)

    # --------------------------------------------------
    # AUDIO
    # --------------------------------------------------

    @classmethod
    def _load_audio(cls, path):

        whisper = cls._require(
            "faster_whisper", "Audio transcription"
        )

        model = whisper.WhisperModel(
            "base",
            device="cpu",
            compute_type="int8"
        )

        segments, info = model.transcribe(str(path))

        documents = []

        for segment in segments:

            documents.extend(
                cls._make_document(
                    segment.text,
                    {
                        "start": segment.start,
                        "end": segment.end
                    }
                )
            )

        return documents

    # --------------------------------------------------
    # VIDEO / FRAME OCR
    # --------------------------------------------------

    @classmethod
    def _load_video(cls, path):

        cv2 = cls._require("cv2", "Video frame extraction")
        pytesseract = cls._require("pytesseract", "Video frame OCR")
        pillow = cls._require("PIL.Image", "Video frame OCR")

        documents = []

        capture = cv2.VideoCapture(str(path))

        if not capture.isOpened():
            raise ValueError(f"Cannot open video: {path}")

        fps = capture.get(cv2.CAP_PROP_FPS) or 1
        frame_interval = max(1, int(fps * 5))

        frame_number = 0

        try:
            while True:

                success, frame = capture.read()

                if not success:
                    break

                if frame_number % frame_interval == 0:

                    seconds = frame_number / fps
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    text = pytesseract.image_to_string(
                        pillow.fromarray(rgb)
                    )

                    documents.extend(
                        cls._make_document(
                            text,
                            {"timestamp": round(seconds, 2)}
                        )
                    )

                frame_number += 1
        finally:
            capture.release()

        return documents
