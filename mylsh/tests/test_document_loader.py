import csv
import json

import pytest

from mylsh import Document, document_loader as dl


def write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_text_and_metadata(tmp_path):
    p = write(tmp_path, "a.txt", "hello")
    docs = dl.load(p)
    assert isinstance(docs[0], Document)
    assert docs[0].page_content == "hello"
    assert docs[0].metadata["file_name"] == "a.txt"
    assert docs[0].metadata["file_type"] == ".txt"
    assert docs[0].metadata["source"] == str(p.resolve())


def test_empty_file_returns_no_documents(tmp_path):
    assert dl.load(write(tmp_path, "e.txt", "   \n")) == []


def test_source_code_loaded_as_text(tmp_path):
    assert dl.load(write(tmp_path, "x.py", "print(1)"))[0].page_content == "print(1)"


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        dl.load("/does/not/exist.txt")


def test_directory_passed_to_load(tmp_path):
    with pytest.raises(ValueError):
        dl.load(tmp_path)


def test_unsupported_extension(tmp_path):
    with pytest.raises(ValueError, match="Unsupported"):
        dl.load(write(tmp_path, "a.xyz", "x"))


def test_csv_rows(tmp_path):
    p = tmp_path / "a.csv"
    with open(p, "w", newline="") as f:
        w = csv.writer(f)
        w.writerows([["n", "v"], ["a", "1"], ["b", "2"]])
    docs = dl.load(p)
    assert len(docs) == 2
    assert docs[0].page_content == "n: a\nv: 1"
    assert docs[0].metadata["row"] == 2


def test_tsv(tmp_path):
    assert dl.load(write(tmp_path, "a.tsv", "n\tv\na\t1\n"))[0].page_content == "n: a\nv: 1"


def test_json_and_invalid_json(tmp_path):
    assert json.loads(dl.load(write(tmp_path, "a.json", '{"k": 1}'))[0].page_content) == {"k": 1}
    with pytest.raises(ValueError, match="Could not read"):
        dl.load(write(tmp_path, "bad.json", "{oops"))


def test_xml(tmp_path):
    assert "<a>1</a>" in dl.load(write(tmp_path, "a.xml", "<r><a>1</a></r>"))[0].page_content


def test_yaml(tmp_path):
    pytest.importorskip("yaml")
    assert json.loads(dl.load(write(tmp_path, "a.yml", "a: 1"))[0].page_content) == {"a": 1}
    assert dl.load(write(tmp_path, "empty.yaml", "")) == []


def test_html_skips_script_and_style(tmp_path):
    html = "<html><head><title>T</title><style>p{}</style></head><body><script>var x=1;</script><p>Hi &amp; bye</p></body></html>"
    text = dl.load(write(tmp_path, "a.html", html))[0].page_content
    assert text == "Hi & bye"


def test_rtf(tmp_path):
    pytest.importorskip("striprtf")
    assert "Hello RTF" in dl.load(write(tmp_path, "a.rtf", r"{\rtf1\ansi Hello RTF}"))[0].page_content


def test_eml(tmp_path):
    eml = "From: a@x.com\nTo: b@x.com\nSubject: Hi\nContent-Type: text/plain\n\nBody text\n"
    doc = dl.load(write(tmp_path, "a.eml", eml))[0]
    assert "Body text" in doc.page_content
    assert doc.metadata["subject"] == "Hi"
    assert doc.metadata["from"] == "a@x.com"


def test_pdf_pages(tmp_path):
    pytest.importorskip("pypdf")
    canvas = pytest.importorskip("reportlab.pdfgen.canvas")
    p = tmp_path / "a.pdf"
    c = canvas.Canvas(str(p))
    c.drawString(100, 750, "page one")
    c.showPage()
    c.drawString(100, 750, "page two")
    c.save()
    docs = dl.load(p)
    assert [d.metadata["page"] for d in docs] == [1, 2]
    assert "page two" in docs[1].page_content


def test_docx(tmp_path):
    docx = pytest.importorskip("docx")
    x = docx.Document()
    x.add_paragraph("Para")
    t = x.add_table(rows=1, cols=2)
    t.rows[0].cells[0].text, t.rows[0].cells[1].text = "c1", "c2"
    x.save(tmp_path / "a.docx")
    assert dl.load(tmp_path / "a.docx")[0].page_content == "Para\nc1 | c2"


def test_xlsx_keeps_column_alignment(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    wb = openpyxl.Workbook()
    wb.active.append(["h1", "h2"])
    wb.active.append([1, None])
    wb.save(tmp_path / "a.xlsx")
    doc = dl.load(tmp_path / "a.xlsx")[0]
    assert doc.page_content == "h1 | h2\n1 | "
    assert doc.metadata["sheet"] == "Sheet"


def test_pptx(tmp_path):
    pptx = pytest.importorskip("pptx")
    p = pptx.Presentation()
    s = p.slides.add_slide(p.slide_layouts[1])
    s.shapes.title.text = "Slide title"
    p.save(tmp_path / "a.pptx")
    doc = dl.load(tmp_path / "a.pptx")[0]
    assert "Slide title" in doc.page_content and doc.metadata["slide"] == 1


def test_corrupt_office_file_gives_clear_error(tmp_path):
    pytest.importorskip("docx")
    (tmp_path / "bad.docx").write_bytes(b"junk")
    with pytest.raises(ValueError, match="Could not read"):
        dl.load(tmp_path / "bad.docx")


def test_missing_optional_dependency(tmp_path, monkeypatch):
    real = dl._require
    def fake(package, feature):
        if package == "pypdf":
            raise ImportError("Install 'pypdf' to load PDF.")
        return real(package, feature)
    monkeypatch.setattr(dl, "_require", fake)
    (tmp_path / "a.pdf").write_bytes(b"%PDF-1.4")
    with pytest.raises(ImportError, match="pypdf"):
        dl.load(tmp_path / "a.pdf")


def test_image_ocr(tmp_path):
    pytest.importorskip("pytesseract")
    Image = pytest.importorskip("PIL.Image")
    ImageDraw = pytest.importorskip("PIL.ImageDraw")
    import shutil
    if not shutil.which("tesseract"):
        pytest.skip("tesseract not installed")
    im = Image.new("RGB", (400, 100), "white")
    ImageDraw.Draw(im).text((10, 40), "HELLO", fill="black")
    im.save(tmp_path / "a.png")
    assert isinstance(dl.load(tmp_path / "a.png"), list)


def test_load_many_and_ignore_errors(tmp_path):
    a = write(tmp_path, "a.txt", "one")
    b = write(tmp_path, "b.md", "two")
    bad = write(tmp_path, "bad.json", "{")
    assert [d.page_content for d in dl.load_many([a, b])] == ["one", "two"]
    with pytest.raises(ValueError):
        dl.load_many([a, bad])
    assert len(dl.load_many([a, bad], ignore_errors=True)) == 1


def test_load_directory(tmp_path):
    write(tmp_path, "a.txt", "one")
    write(tmp_path, "ignore.xyz", "no")
    write(tmp_path, ".hidden.txt", "hidden")
    sub = tmp_path / "sub"
    sub.mkdir()
    write(sub, "b.md", "two")
    names = sorted(d.metadata["file_name"] for d in dl.load_directory(tmp_path))
    assert names == ["a.txt", "b.md"]
    assert [d.metadata["file_name"] for d in dl.load_directory(tmp_path, recursive=False)] == ["a.txt"]
    only_md = dl.load_directory(tmp_path, extensions=["md"])
    assert [d.metadata["file_name"] for d in only_md] == ["b.md"]


def test_load_directory_errors(tmp_path):
    with pytest.raises(FileNotFoundError):
        dl.load_directory(tmp_path / "nope")
    with pytest.raises(ValueError):
        dl.load_directory(write(tmp_path, "f.txt", "x"))


def test_supported_formats():
    fmts = dl.supported_formats()
    assert fmts == sorted(set(fmts))
    for ext in (".pdf", ".docx", ".eml", ".csv", ".py"):
        assert ext in fmts
