# Optional tools

Run `mentor.py doctor`. Required storage, validation and text ingestion use Python stdlib. Reuse available backends; install only within authorization. Missing capability -> explicit limitation.

- PDF: Poppler `pdftotext` for page text and coordinates; `pypdf` fallback. `pdfinfo` checks count.
- Render: Poppler `pdftoppm` or PyMuPDF. Actually view central pages, not just check command success.
- OCR: `mentor.py ocr` requires tesseract/language packs and renderer. Store alternative transcript; never replace the original. Visually check math/numbers.
- Math: `math_tools.py ast` builds a restricted arithmetic AST without execution. Optional `symbolic` uses SymPy through that AST, never string evaluation. No general LaTeX parsing or proof certification.
- Ollama: `ollama_assist.py --model <explicit-model> --input <text-file>` sends that text only to loopback Ollama when explicitly requested. No auto model pull; bounded timeout/size. Response is unverified assistance; Codex is not thereby offline.

HTML full text is extracted through available browsing tools and saved as UTF-8 with its actual URL. Direct URL ingestion accepts public HTTP(S) PDF/plain text/Markdown, checks redirects/content/size, and rejects HTML masquerading as paper text. No authenticated scraping or execution of embedded content.
