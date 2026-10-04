---
name: paged-pdf
description: Generate publication-grade, pixel-perfect A4 PDFs (reports, government forms, official submissions) using CSS Paged Media and WeasyPrint instead of naive markdown/pandoc converters.
---

# Pixel-Perfect CSS Paged Media PDF Generation

Use this skill when you need to generate professional, multi-page PDF documents, statutory forms, or technical reports that require precise pagination, running headers/footers, and clean table formatting.

## Why CSS Paged Media?
Generic converters (e.g. `pandoc file.docx/odt -o out.pdf` or naive Markdown-to-PDF) often fail on complex documents:
- Headings and outline levels turn into nested bullet lists (`• ◦ ▪`).
- Table rows break across arbitrary pages, splitting data and labels.
- Images scale poorly or overflow page boundaries.
- Cover pages and headers/footers lose alignment and typography.

Using semantic HTML + CSS Paged Media (rendered via WeasyPrint) guarantees:
- Exact A4 sizing (`size: A4 portrait; margin: ...`).
- Running headers and footers with dynamic page counts (`counter(page)` of `counter(pages)`).
- Control over page breaks (`page-break-before: always;`, `page-break-inside: avoid;`).
- Clean table and cell padding that never straddles page boundaries.

---

## Standard CSS Template

```css
@page {
    size: A4 portrait;
    margin: 15mm 15mm 18mm 15mm;
    @top-left {
        content: "Document / Agency Title";
        font-family: "Noto Sans CJK TC", "Microsoft JhengHei", sans-serif;
        font-size: 8pt;
        color: #64748B;
    }
    @top-right {
        content: "Document Version / ID";
        font-family: "Noto Sans CJK TC", "Microsoft JhengHei", sans-serif;
        font-size: 8pt;
        color: #64748B;
    }
    @bottom-center {
        content: "第 " counter(page) " 頁 / 共 " counter(pages) " 頁";
        font-family: "Noto Sans CJK TC", "Microsoft JhengHei", sans-serif;
        font-size: 8.5pt;
        color: #64748B;
    }
}

/* Suppress headers and footers on the cover page */
@page:first {
    margin: 0;
    @top-left { content: none; }
    @top-right { content: none; }
    @bottom-center { content: none; }
}

body {
    font-family: "Noto Sans CJK TC", "Microsoft JhengHei", sans-serif;
    color: #1E293B;
    font-size: 8.5pt;
    line-height: 1.45;
    margin: 0;
    padding: 0;
}

/* Table rules to prevent broken pagination */
table {
    width: 100%;
    border-collapse: collapse;
    page-break-inside: auto;
}
tr {
    page-break-inside: avoid;
}
th, td {
    border: 1px solid #94A3B8;
    padding: 4px 6px;
    vertical-align: top;
}
th {
    background-color: #F1F5F9;
    font-weight: bold;
    text-align: center;
}

/* Page break helpers */
.page-break {
    page-break-before: always;
}

/* Full-width proof screenshot styling */
.proof-img {
    max-width: 95%;
    max-height: 80mm;
    object-fit: contain;
    display: block;
    margin: 6px auto;
    border: 1px solid #CBD5E1;
    border-radius: 4px;
}
```

---

## Python Build Script Pattern

```python
import subprocess
import weasyprint

def build_pdf(html_path, out_pdf_path):
    subprocess.run(["weasyprint", html_path, out_pdf_path], check=True)
```
