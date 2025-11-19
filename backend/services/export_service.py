"""
Export service for generating downloadable files from hypothesis results.
"""
import os
import json
import pandas as pd
from typing import Optional
from datetime import datetime
import logging

from models.export import ExportResponse, ExportFormat
from models.hypothesis import HypothesisResult
from services.session_service import SessionService
from services.hypothesis_service import HypothesisService

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting hypothesis results."""
    
    def __init__(self):
        self.session_service = SessionService()
        self.hypothesis_service = HypothesisService()
    
    async def create_export(
        self,
        session_id: str,
        job_id: str,
        format: ExportFormat,
        include_citations: bool = True,
        include_scores: bool = True
    ) -> ExportResponse:
        """Create an export file."""
        try:
            # Get results
            result = await self.hypothesis_service.get_results(session_id, job_id)
            
            if not result:
                raise ValueError("Results not found for this job")
            
            # Generate filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            base_filename = f"hypotheses_{timestamp}"
            
            # Get export directory
            session_path = self.session_service.get_session_path(session_id)
            export_dir = os.path.join(session_path, "exports")
            os.makedirs(export_dir, exist_ok=True)
            
            # Generate export based on format
            if format == ExportFormat.JSON:
                filename = f"{base_filename}.json"
                file_path = os.path.join(export_dir, filename)
                await self._export_json(result, file_path, include_citations, include_scores)
                
            elif format == ExportFormat.EXCEL:
                filename = f"{base_filename}.xlsx"
                file_path = os.path.join(export_dir, filename)
                await self._export_excel(result, file_path, include_citations, include_scores)
                
            elif format == ExportFormat.CSV:
                filename = f"{base_filename}.csv"
                file_path = os.path.join(export_dir, filename)
                await self._export_csv(result, file_path, include_citations, include_scores)
                
            elif format == ExportFormat.PDF:
                filename = f"{base_filename}.pdf"
                file_path = os.path.join(export_dir, filename)
                await self._export_pdf(result, file_path, include_citations, include_scores)
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            return ExportResponse(
                success=True,
                download_url=f"/api/export/download/{filename}",
                filename=filename,
                format=format,
                file_size_bytes=file_size
            )
            
        except Exception as e:
            logger.error(f"❌ Export creation failed: {e}", exc_info=True)
            return ExportResponse(
                success=False,
                download_url=None,
                filename="",
                format=format,
                error_message=str(e)
            )
    
    async def _export_json(
        self,
        result: HypothesisResult,
        file_path: str,
        include_citations: bool,
        include_scores: bool
    ):
        """Export as JSON."""
        data = result.model_dump()
        
        # Filter based on options
        if not include_citations:
            for hyp in data.get("hypotheses", []):
                hyp["citations"] = []
        
        if not include_scores:
            for hyp in data.get("hypotheses", []):
                hyp.pop("scores", None)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
    
    async def _export_excel(
        self,
        result: HypothesisResult,
        file_path: str,
        include_citations: bool,
        include_scores: bool
    ):
        """Export as Excel."""
        # Convert to DataFrame
        rows = []
        for hyp in result.hypotheses:
            row = {
                "ID": hyp.id,
                "Hypothesis": hyp.hypothesis_text,
                "Rationale": hyp.rationale,
                "Key Concepts": ", ".join(hyp.key_concepts)
            }
            
            if include_scores:
                row.update({
                    "Novelty Score": hyp.scores.novelty,
                    "Accuracy Score": hyp.scores.accuracy,
                    "Relevancy Score": hyp.scores.relevancy,
                    "Overall Score": hyp.scores.overall
                })
            
            if include_citations:
                citation_texts = [
                    f"{c.authors[0] if c.authors else 'Unknown'} et al. ({c.year or 'N/A'})"
                    for c in hyp.citations
                ]
                row["Citations"] = "; ".join(citation_texts) if citation_texts else "None"
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
        
        # Write to Excel
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Hypotheses', index=False)
            
            # Add metadata sheet
            metadata_df = pd.DataFrame([{
                "Research Topic": result.research_topic,
                "Total Hypotheses": result.total_count,
                "Generated At": result.generated_at.isoformat(),
                "Job ID": result.job_id
            }])
            metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
    
    async def _export_csv(
        self,
        result: HypothesisResult,
        file_path: str,
        include_citations: bool,
        include_scores: bool
    ):
        """Export as CSV."""
        rows = []
        for hyp in result.hypotheses:
            row = {
                "ID": hyp.id,
                "Hypothesis": hyp.hypothesis_text,
                "Rationale": hyp.rationale,
                "Key Concepts": ", ".join(hyp.key_concepts)
            }
            
            if include_scores:
                row.update({
                    "Novelty Score": hyp.scores.novelty,
                    "Accuracy Score": hyp.scores.accuracy,
                    "Relevancy Score": hyp.scores.relevancy,
                    "Overall Score": hyp.scores.overall
                })
            
            if include_citations:
                citation_count = len(hyp.citations)
                row["Citation Count"] = citation_count
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
        df.to_csv(file_path, index=False, encoding='utf-8')
    
    async def _export_pdf(
        self,
        result: HypothesisResult,
        file_path: str,
        include_citations: bool,
        include_scores: bool
    ):
        """Export as PDF (placeholder - requires additional PDF library)."""
        # For now, create a text file
        # TODO: Implement actual PDF generation with reportlab or similar
        text_content = f"""
AI Research Processor - Hypothesis Generation Results
{'=' * 60}

Research Topic: {result.research_topic}
Generated: {result.generated_at.strftime("%Y-%m-%d %H:%M:%S")}
Total Hypotheses: {result.total_count}

"""
        
        for hyp in result.hypotheses:
            text_content += f"\n{'=' * 60}\n"
            text_content += f"Hypothesis #{hyp.id}\n"
            text_content += f"{'=' * 60}\n\n"
            text_content += f"{hyp.hypothesis_text}\n\n"
            text_content += f"Rationale:\n{hyp.rationale}\n\n"
            text_content += f"Key Concepts: {', '.join(hyp.key_concepts)}\n\n"
            
            if include_scores:
                text_content += f"Scores:\n"
                text_content += f"  Novelty: {hyp.scores.novelty}/5.0\n"
                text_content += f"  Accuracy: {hyp.scores.accuracy}/5.0\n"
                text_content += f"  Relevancy: {hyp.scores.relevancy}/5.0\n"
                text_content += f"  Overall: {hyp.scores.overall}/5.0\n\n"
            
            if include_citations and hyp.citations:
                text_content += f"Citations ({len(hyp.citations)}):\n"
                for i, cit in enumerate(hyp.citations, 1):
                    authors = ", ".join(cit.authors[:3]) if cit.authors else "Unknown"
                    text_content += f"  {i}. {authors} - {cit.title} ({cit.year or 'N/A'})\n"
        
        # Write as text file with .pdf extension (placeholder)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
    
    async def get_export_file(self, session_id: str, filename: str) -> Optional[str]:
        """Get path to export file if it exists and belongs to session."""
        session_path = self.session_service.get_session_path(session_id)
        file_path = os.path.join(session_path, "exports", filename)
        
        if os.path.exists(file_path):
            return file_path
        
        return None

