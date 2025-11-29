from __future__ import annotations

import json
from html import escape
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from ...vectorstore.chroma_store import ChromaVectorStore
from ..dependencies import get_app_settings
from ..services.highlight import build_search_phrase


router = APIRouter()


def _get_vector_store() -> ChromaVectorStore:
    settings = get_app_settings()
    return ChromaVectorStore(persist_directory=str(settings.chroma_persist_dir))


def _load_chunk(doc_id: str, chunk_id: str, store: ChromaVectorStore):
    chunk = store.get_chunk(chunk_id)
    if chunk is None:
        raise HTTPException(status_code=404, detail="Chunk not found.")
    chunk_doc_id = str(chunk.metadata.get("doc_id") or "")
    if chunk_doc_id and chunk_doc_id != doc_id:
        raise HTTPException(status_code=404, detail="Chunk does not belong to the requested document.")
    return chunk


def _normalize_local_path(path_value: str) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


def _format_snippet(text: str, phrase: str) -> str:
    snippet = text.strip()
    if not snippet:
        return ""
    if not phrase:
        return escape(snippet)
    lowered = snippet.lower()
    lowered_phrase = phrase.lower()
    idx = lowered.find(lowered_phrase)
    if idx == -1:
        return escape(snippet)
    before = escape(snippet[:idx])
    match = escape(snippet[idx : idx + len(phrase)])
    after = escape(snippet[idx + len(phrase) :])
    return f"{before}<mark>{match}</mark>{after}"


@router.get("/documents/{doc_id}/chunks/{chunk_id}/file")
def get_document_file(doc_id: str, chunk_id: str, store: ChromaVectorStore = Depends(_get_vector_store)):
    chunk = _load_chunk(doc_id, chunk_id, store)
    local_path_value = str(chunk.metadata.get("local_path") or "")
    if not local_path_value:
        raise HTTPException(status_code=404, detail="Local file path is not available for this chunk.")
    file_path = _normalize_local_path(local_path_value)
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Document file not found on server.")
    media_type = "application/pdf"
    suffix = file_path.suffix.lower()
    if suffix == ".html":
        media_type = "text/html"
    return FileResponse(file_path, media_type=media_type, filename=file_path.name)


@router.get(
    "/documents/{doc_id}/chunks/{chunk_id}/viewer",
    response_class=HTMLResponse,
)
def view_document_chunk(doc_id: str, chunk_id: str, store: ChromaVectorStore = Depends(_get_vector_store)):
    chunk = _load_chunk(doc_id, chunk_id, store)
    local_path_value = str(chunk.metadata.get("local_path") or "")
    if not local_path_value:
        raise HTTPException(status_code=404, detail="Local file path is not available for this chunk.")
    page = chunk.metadata.get("page_start") or 1
    phrase = build_search_phrase(chunk.text)
    pdf_src = f"/documents/{doc_id}/chunks/{chunk_id}/file"
    snippet_source = chunk.text
    snippet_html = _format_snippet(snippet_source, phrase)
    page_label = escape(str(page))
    pdf_url_js = json.dumps(pdf_src)
    phrase_js = json.dumps(phrase)
    page_js = json.dumps(page)
    cdn_base = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.2.67"
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8" />
        <title>Document Viewer</title>
        <link rel="stylesheet" href="{cdn_base}/pdf_viewer.min.css" integrity="" crossorigin="anonymous" />
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f5f5f5;
            }}
            header {{
                padding: 1rem;
                background-color: #111827;
                color: white;
            }}
            .content {{
                padding: 1rem;
            }}
            .meta {{
                font-size: 0.95rem;
                color: #1f2937;
                margin-bottom: 0.5rem;
            }}
            .snippet {{
                font-size: 0.95rem;
                color: #4b5563;
                margin-bottom: 1rem;
                background: #fefce8;
                padding: 0.5rem;
                border-radius: 0.375rem;
                border: 1px solid #fcd34d;
            }}
            .snippet mark {{
                background-color: #facc15;
                color: #1f2937;
                padding: 0 0.1rem;
            }}
            .viewer-wrapper {{
                border: 1px solid #d1d5db;
                border-radius: 0.5rem;
                overflow: hidden;
                background: white;
            }}
            #viewerContainer {{
                height: calc(100vh - 220px);
                overflow: auto;
            }}
            .pdfViewer .textLayer .highlight {{
                background: rgba(250, 204, 21, 0.55);
                border-radius: 2px;
            }}
            .pdfViewer .page {{
                border-bottom: 1px solid #e5e7eb;
            }}
        </style>
    </head>
    <body>
        <header>
            <strong>Highlighted citation</strong>
        </header>
        <div class="content">
            <div class="meta">Page {page_label}</div>
            <div class="snippet">{snippet_html or "No preview available."}</div>
            <div class="viewer-wrapper">
                <div id="viewerContainer" class="viewerContainer">
                    <div id="viewer" class="pdfViewer"></div>
                </div>
            </div>
        </div>
        <script src="{cdn_base}/pdf.min.js" integrity="" crossorigin="anonymous"></script>
        <script>
            if (window.pdfjsLib) {{
                window.pdfjsLib.GlobalWorkerOptions.workerSrc = "{cdn_base}/pdf.worker.min.js";
            }}
        </script>
        <script src="{cdn_base}/pdf_viewer.min.js" integrity="" crossorigin="anonymous"></script>
        <script>
            (function() {{
                const pdfUrl = {pdf_url_js};
                const targetPage = {page_js} || 1;
                const searchPhrase = {phrase_js};
                const eventBus = new pdfjsViewer.EventBus();
                const linkService = new pdfjsViewer.PDFLinkService({{ eventBus }});
                const findController = new pdfjsViewer.PDFFindController({{ eventBus, linkService }});
                const pdfViewer = new pdfjsViewer.PDFViewer({{
                    container: document.getElementById("viewerContainer"),
                    eventBus,
                    linkService,
                    findController,
                    textLayerMode: 2
                }});
                linkService.setViewer(pdfViewer);
                eventBus.on("pagesinit", function () {{
                    if (targetPage) {{
                        pdfViewer.currentPageNumber = targetPage;
                    }}
                    if (searchPhrase) {{
                        findController.executeCommand("find", {{
                            query: searchPhrase,
                            highlightAll: true,
                            phraseSearch: true,
                        }});
                    }}
                }});
                pdfjsLib.getDocument(pdfUrl).promise.then(function (pdfDocument) {{
                    pdfViewer.setDocument(pdfDocument);
                    linkService.setDocument(pdfDocument, null);
                }}).catch(function (err) {{
                    console.error("Unable to load PDF", err);
                }});
            }})();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)
