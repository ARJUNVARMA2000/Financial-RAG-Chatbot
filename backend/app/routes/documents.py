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
def get_document_file(
    doc_id: str, 
    chunk_id: str, 
    store: ChromaVectorStore = Depends(_get_vector_store)
):
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
    
    # Create response with proper headers for PDF.js
    file_response = FileResponse(
        file_path, 
        media_type=media_type, 
        filename=file_path.name,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Content-Disposition": f'inline; filename="{file_path.name}"',  # inline instead of attachment
        }
    )
    return file_response


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
    # Use jsDelivr CDN which is more reliable
    cdn_base = "https://cdn.jsdelivr.net/npm/pdfjs-dist@4.2.67"
    doc_title = escape(str(chunk.metadata.get('title', 'Document')))
    ticker = escape(str(chunk.metadata.get('ticker', 'N/A')).upper())
    period = escape(str(chunk.metadata.get('period', 'N/A')))
    filing_type = escape(str(chunk.metadata.get('filing_type', 'N/A')))
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Citation Viewer - {doc_title}</title>
        <link rel="stylesheet" href="{cdn_base}/pdf_viewer.min.css" integrity="" crossorigin="anonymous" />
        <style>
            * {{
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }}
            .header {{
                background: rgba(17, 24, 39, 0.95);
                backdrop-filter: blur(10px);
                color: white;
                padding: 1rem 1.5rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 1rem;
            }}
            .header h1 {{
                margin: 0;
                font-size: 1.25rem;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }}
            .header-actions {{
                display: flex;
                gap: 0.75rem;
                align-items: center;
            }}
            .btn {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 0.5rem;
                cursor: pointer;
                text-decoration: none;
                font-size: 0.875rem;
                transition: all 0.2s;
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
            }}
            .btn:hover {{
                background: rgba(255, 255, 255, 0.2);
                transform: translateY(-1px);
            }}
            .btn-primary {{
                background: #3b82f6;
                border-color: #3b82f6;
            }}
            .btn-primary:hover {{
                background: #2563eb;
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                padding: 1.5rem;
            }}
            .citation-info {{
                background: white;
                border-radius: 0.75rem;
                padding: 1.5rem;
                margin-bottom: 1rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .citation-meta {{
                display: flex;
                flex-wrap: wrap;
                gap: 1rem;
                margin-bottom: 1rem;
                padding-bottom: 1rem;
                border-bottom: 1px solid #e5e7eb;
            }}
            .meta-item {{
                display: flex;
                align-items: center;
                gap: 0.5rem;
                font-size: 0.875rem;
                color: #6b7280;
            }}
            .meta-item strong {{
                color: #111827;
                font-weight: 600;
            }}
            .badge {{
                display: inline-flex;
                align-items: center;
                padding: 0.25rem 0.75rem;
                border-radius: 9999px;
                font-size: 0.75rem;
                font-weight: 600;
                background: #dbeafe;
                color: #1e40af;
            }}
            .snippet {{
                background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
                border-left: 4px solid #f59e0b;
                padding: 1rem;
                border-radius: 0.5rem;
                margin-top: 1rem;
                font-size: 0.95rem;
                line-height: 1.6;
                color: #78350f;
            }}
            .snippet mark {{
                background-color: #fbbf24;
                color: #78350f;
                padding: 0.125rem 0.25rem;
                border-radius: 0.25rem;
                font-weight: 600;
            }}
            .viewer-wrapper {{
                background: white;
                border-radius: 0.75rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }}
            .viewer-toolbar {{
                background: #f9fafb;
                border-bottom: 1px solid #e5e7eb;
                padding: 0.75rem 1rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 0.75rem;
            }}
            .toolbar-info {{
                font-size: 0.875rem;
                color: #6b7280;
                font-weight: 500;
            }}
            .zoom-controls {{
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }}
            .zoom-btn {{
                background: white;
                border: 1px solid #d1d5db;
                color: #374151;
                padding: 0.375rem 0.75rem;
                border-radius: 0.375rem;
                cursor: pointer;
                font-size: 0.875rem;
                font-weight: 500;
                transition: all 0.2s;
            }}
            .zoom-btn:hover {{
                background: #f3f4f6;
                border-color: #9ca3af;
            }}
            .zoom-level {{
                font-size: 0.875rem;
                color: #6b7280;
                min-width: 60px;
                text-align: center;
            }}
            #viewerContainer {{
                height: calc(100vh - 400px);
                min-height: 600px;
                overflow: auto;
                background: #525252;
            }}
            .pdfViewer .textLayer .highlight {{
                background: rgba(250, 204, 21, 0.6);
                border-radius: 3px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            }}
            .pdfViewer .page {{
                border-bottom: 1px solid #e5e7eb;
                margin: 0 auto;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }}
            .loading {{
                display: flex;
                justify-content: center;
                align-items: center;
                height: 400px;
                color: #6b7280;
                font-size: 1rem;
            }}
            @media (max-width: 768px) {{
                .container {{
                    padding: 1rem;
                }}
                .header {{
                    padding: 1rem;
                }}
                .header h1 {{
                    font-size: 1rem;
                }}
                #viewerContainer {{
                    height: calc(100vh - 350px);
                    min-height: 400px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>
                <span>📄</span>
                <span>Citation Viewer</span>
            </h1>
            <div class="header-actions">
                <a href="javascript:window.close()" class="btn">← Close</a>
                <a href="{pdf_src}" download class="btn btn-primary">⬇ Download PDF</a>
            </div>
        </div>
        <div class="container">
            <div class="citation-info">
                <div class="citation-meta">
                    <div class="meta-item">
                        <strong>Document:</strong>
                        <span>{doc_title}</span>
                    </div>
                    <div class="meta-item">
                        <strong>Ticker:</strong>
                        <span class="badge">{ticker}</span>
                    </div>
                    <div class="meta-item">
                        <strong>Period:</strong>
                        <span>{period}</span>
                    </div>
                    <div class="meta-item">
                        <strong>Type:</strong>
                        <span>{filing_type}</span>
                    </div>
                    <div class="meta-item">
                        <strong>Page:</strong>
                        <span class="badge">{page_label}</span>
                    </div>
                </div>
                <div class="snippet">
                    <strong>📌 Relevant Excerpt:</strong><br/>
                    {snippet_html or "No preview available."}
                </div>
            </div>
            <div class="viewer-wrapper">
                <div class="viewer-toolbar">
                    <div class="toolbar-info">
                        📖 Navigating to page {page_label} with highlighted text
                    </div>
                    <div class="zoom-controls">
                        <button class="zoom-btn" onclick="zoomOut()" title="Zoom Out">−</button>
                        <span class="zoom-level" id="zoomLevel">100%</span>
                        <button class="zoom-btn" onclick="zoomIn()" title="Zoom In">+</button>
                        <button class="zoom-btn" onclick="resetZoom()" title="Reset Zoom">Reset</button>
                    </div>
                </div>
                <div id="viewerContainer" class="viewerContainer">
                    <div class="loading">Loading PDF viewer...</div>
                    <div id="viewer" class="pdfViewer"></div>
                    <!-- Fallback iframe viewer -->
                    <iframe id="fallbackViewer" src="{pdf_src}#page={page}" style="display: none; width: 100%; height: 100%; border: none;"></iframe>
                </div>
            </div>
        </div>
        <script>
            // Define zoom functions early so they're available when buttons are clicked
            window.pdfViewerInstance = null;
            
            window.zoomIn = function() {{
                if (!window.pdfViewerInstance) {{
                    console.warn('PDF viewer not ready yet');
                    return;
                }}
                const currentScale = window.pdfViewerInstance.currentScale;
                window.pdfViewerInstance.currentScale = Math.min(currentScale * 1.25, 5.0);
                updateZoomDisplay();
            }};
            
            window.zoomOut = function() {{
                if (!window.pdfViewerInstance) {{
                    console.warn('PDF viewer not ready yet');
                    return;
                }}
                const currentScale = window.pdfViewerInstance.currentScale;
                window.pdfViewerInstance.currentScale = Math.max(currentScale / 1.25, 0.25);
                updateZoomDisplay();
            }};
            
            window.resetZoom = function() {{
                if (!window.pdfViewerInstance) {{
                    console.warn('PDF viewer not ready yet');
                    return;
                }}
                // Use a larger default scale (1.5x = 150%)
                window.pdfViewerInstance.currentScale = 1.5;
                updateZoomDisplay();
            }};
            
            function updateZoomDisplay() {{
                const zoomLevelEl = document.getElementById('zoomLevel');
                if (zoomLevelEl && window.pdfViewerInstance) {{
                    const percent = Math.round(window.pdfViewerInstance.currentScale * 100);
                    zoomLevelEl.textContent = percent + '%';
                }}
            }}
            
            // Try to load PDF.js with fallback to native viewer
            let useFallback = false;
            
            function loadScript(src, onError) {{
                return new Promise((resolve, reject) => {{
                    const script = document.createElement('script');
                    script.src = src;
                    script.onload = resolve;
                    script.onerror = () => {{
                        console.warn('Failed to load:', src);
                        if (onError) onError();
                        reject(new Error('Failed to load ' + src));
                    }};
                    document.head.appendChild(script);
                }});
            }}
            
            function showFallbackViewer() {{
                const loadingEl = document.querySelector('.loading');
                const viewerEl = document.getElementById('viewer');
                const fallbackEl = document.getElementById('fallbackViewer');
                const container = document.getElementById('viewerContainer');
                
                if (loadingEl) loadingEl.style.display = 'none';
                if (viewerEl) viewerEl.style.display = 'none';
                if (fallbackEl) {{
                    fallbackEl.style.display = 'block';
                    container.style.height = 'calc(100vh - 400px)';
                }}
            }}
            
            // Try loading PDF.js
            Promise.all([
                loadScript('{cdn_base}/build/pdf.min.js').catch(() => {{
                    return loadScript('https://unpkg.com/pdfjs-dist@4.2.67/build/pdf.min.js');
                }}).catch(() => {{
                    return loadScript('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.2.67/pdf.min.js');
                }}).catch(() => {{
                    useFallback = true;
                    throw new Error('All CDNs failed');
                }}),
                loadScript('{cdn_base}/build/pdf_viewer.min.js').catch(() => {{
                    return loadScript('https://unpkg.com/pdfjs-dist@4.2.67/build/pdf_viewer.min.js');
                }}).catch(() => {{
                    return loadScript('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.2.67/pdf_viewer.min.js');
                }}).catch(() => {{
                    useFallback = true;
                    throw new Error('Viewer CDN failed');
                }})
            ]).then(() => {{
                // Set worker source
                if (typeof pdfjsLib !== 'undefined') {{
                    pdfjsLib.GlobalWorkerOptions.workerSrc = '{cdn_base}/build/pdf.worker.min.js';
                    // Try fallback workers if primary fails
                    const originalWorkerSrc = pdfjsLib.GlobalWorkerOptions.workerSrc;
                    pdfjsLib.GlobalWorkerOptions.workerSrc = originalWorkerSrc;
                }}
            }}).catch(() => {{
                console.warn('PDF.js failed to load, using fallback viewer');
                useFallback = true;
                showFallbackViewer();
            }});
        </script>
        <script>
            
            (function() {{
                const pdfUrl = {pdf_url_js};
                const targetPage = {page_js} || 1;
                const searchPhrase = {phrase_js};
                const loadingEl = document.querySelector('.loading');
                let initAttempts = 0;
                const maxAttempts = 30; // 3 seconds max wait
                
                // Wait for libraries to load
                function initViewer() {{
                    initAttempts++;
                    
                    // Check if we should use fallback
                    if (useFallback || initAttempts > maxAttempts) {{
                        showFallbackViewer();
                        return;
                    }}
                    
                    if (typeof pdfjsLib === 'undefined' || typeof pdfjsViewer === 'undefined') {{
                        setTimeout(initViewer, 100);
                        return;
                    }}
                    
                    // Libraries loaded, initialize viewer
                    try {{
                        // Ensure worker is set
                        if (!pdfjsLib.GlobalWorkerOptions.workerSrc) {{
                            pdfjsLib.GlobalWorkerOptions.workerSrc = "{cdn_base}/pdf.worker.min.js";
                        }}
                        
                        const eventBus = new pdfjsViewer.EventBus();
                        const linkService = new pdfjsViewer.PDFLinkService({{ eventBus }});
                        const findController = new pdfjsViewer.PDFFindController({{ eventBus, linkService }});
                        const container = document.getElementById("viewerContainer");
                        const viewerDiv = document.getElementById("viewer");
                        
                        if (!container || !viewerDiv) {{
                            throw new Error("Viewer container not found");
                        }}
                        
                        const pdfViewer = new pdfjsViewer.PDFViewer({{
                            container: container,
                            eventBus: eventBus,
                            linkService: linkService,
                            findController: findController,
                            textLayerMode: 2,
                            annotationMode: 2
                        }});
                        linkService.setViewer(pdfViewer);
                        
                        // Store viewer reference globally for zoom functions
                        window.pdfViewerInstance = pdfViewer;
                        
                        // Update zoom display when scale changes
                        eventBus.on('scalechanging', updateZoomDisplay);
                        eventBus.on('scalechange', updateZoomDisplay);
                        
                        // Update loading message
                        if (loadingEl) {{
                            loadingEl.textContent = "Loading PDF document...";
                        }}
                        
                        // Hide loading when pages are initialized
                        eventBus.on("pagesinit", function () {{
                            if (loadingEl) {{
                                loadingEl.style.display = 'none';
                            }}
                            // Set a larger default scale (1.5x = 150%) for better readability
                            pdfViewer.currentScale = 1.5;
                            updateZoomDisplay();
                            
                            // Navigate to target page
                            if (targetPage && targetPage > 0) {{
                                pdfViewer.currentPageNumber = targetPage;
                            }}
                            // Search for phrase after a short delay
                            if (searchPhrase && searchPhrase.trim()) {{
                                setTimeout(() => {{
                                    try {{
                                        findController.executeCommand("find", {{
                                            query: searchPhrase,
                                            highlightAll: true,
                                            phraseSearch: true,
                                        }});
                                    }} catch (e) {{
                                        console.warn("Search failed:", e);
                                    }}
                                }}, 1000);
                            }}
                        }});
                        
                        // Handle PDF loading errors
                        eventBus.on("pagesloaded", function() {{
                            if (loadingEl) {{
                                loadingEl.style.display = 'none';
                            }}
                        }});
                        
                        // Load the PDF document with proper error handling
                        const loadingTask = pdfjsLib.getDocument({{
                            url: pdfUrl,
                            httpHeaders: {{}},
                            withCredentials: false,
                            cMapUrl: "{cdn_base}/web/cmaps/",
                            cMapPacked: true,
                            standardFontDataUrl: "{cdn_base}/web/standard_fonts/"
                        }});
                        
                        loadingTask.promise.then(function (pdfDocument) {{
                            console.log("PDF loaded successfully, pages:", pdfDocument.numPages);
                            pdfViewer.setDocument(pdfDocument);
                            linkService.setDocument(pdfDocument, null);
                        }}, function (error) {{
                            console.error("Error loading PDF:", error);
                            // Fallback to native viewer on error
                            showFallbackViewer();
                        }});
                        
                    }} catch (err) {{
                        console.error("Error initializing PDF viewer:", err);
                        if (loadingEl) {{
                            loadingEl.innerHTML = 
                                '<div style="text-align: center; color: #ef4444; padding: 2rem;">' +
                                '<strong>Error initializing viewer</strong><br/>' +
                                '<div style="margin: 1rem 0; font-size: 0.9rem;">' + 
                                (err.message || 'Unknown error') + '</div>' +
                                '<a href="' + pdfUrl + '" download style="' +
                                'display: inline-block; margin-top: 1rem; padding: 0.5rem 1rem; ' +
                                'background: #3b82f6; color: white; text-decoration: none; ' +
                                'border-radius: 0.5rem;">Download PDF</a></div>';
                        }}
                    }}
                }}
                
                // Start initialization when DOM is ready
                if (document.readyState === 'loading') {{
                    document.addEventListener('DOMContentLoaded', initViewer);
                }} else {{
                    // DOM already loaded, start immediately
                    setTimeout(initViewer, 100);
                }}
            }})();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)
