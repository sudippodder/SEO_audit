import os
import time
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core import run_audit
from utils.storage import _report_to_dict
from utils.pdf_export import generate_pdf

# Ensure static/pdfs directory exists
PDF_DIR = os.path.join(os.path.dirname(__file__), "static", "pdfs")
os.makedirs(PDF_DIR, exist_ok=True)

app = FastAPI(
    title="GEO Audit API",
    description="API service for the AI GEO Audit Tool.",
    version="1.0.0"
)

# Mount the static directory to serve generated PDFs
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")


class AuditRequest(BaseModel):
    url: str
    email: str = "api-user@example.com"
    keyword: str = ""
    full_site: bool = False
    check_broken_links: bool = False
    openai_api_key: str = ""


@app.post("/api/audit", summary="Run a GEO/SEO audit")
async def perform_audit(req: AuditRequest, request: Request):
    """
    Run a full or single-page GEO audit on the provided URL.
    Returns the JSON report and a link to the generated PDF.
    """
    try:
        # Run the core audit
        report = run_audit(
            url=req.url,
            email=req.email,
            keyword=req.keyword,
            check_broken_links=req.check_broken_links,
            full_site=req.full_site,
            openai_api_key=req.openai_api_key
        )

        if report.error:
            raise HTTPException(status_code=400, detail=f"Audit failed: {report.error}")

        # Convert report to dict
        data = _report_to_dict(report)

        # Generate PDF
        pdf_bytes = generate_pdf(data)
        
        pdf_url = None
        if pdf_bytes:
            domain = urlparse(req.url).netloc.replace("www.", "")
            timestamp = int(time.time())
            filename = f"geo_audit_{domain}_{timestamp}.pdf"
            filepath = os.path.join(PDF_DIR, filename)
            
            # Save PDF to disk
            with open(filepath, "wb") as f:
                f.write(pdf_bytes)
            
            # Construct the full URL to the PDF
            base_url = str(request.base_url).rstrip("/")
            pdf_url = f"{base_url}/static/pdfs/{filename}"

        return JSONResponse({
            "status": "success",
            "pdf_url": pdf_url,
            "audit_report": data
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def read_root():
    return {"message": "Welcome to the GEO Audit API. Send a POST request to /api/audit to start an audit."}
