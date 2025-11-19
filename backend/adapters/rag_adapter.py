"""
Adapter for the Enhanced RAG System to work with async web API.
Wraps the existing enhanced_rag_with_chromadb.py for session-isolated hypothesis generation.
"""
import sys
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.hypothesis import (
    HypothesisItem,
    HypothesisScores,
    HypothesisCitation
)

logger = logging.getLogger(__name__)


class RAGAdapter:
    """
    Adapter for integrating the existing RAG system with the web API.
    Handles async execution and progress callbacks.
    """
    
    def __init__(self, session_id: str, output_dir: str):
        """
        Initialize RAG adapter.
        
        Args:
            session_id: User session ID for isolation
            output_dir: Directory for output files
        """
        self.session_id = session_id
        self.output_dir = output_dir
        self.executor = ThreadPoolExecutor(max_workers=1)
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
    
    async def generate_hypotheses(
        self,
        research_topic: str,
        num_hypotheses: int = 10,
        progress_callback: Optional[Callable[[float, str, int], None]] = None
    ) -> List[HypothesisItem]:
        """
        Generate hypotheses using the RAG system.
        
        Args:
            research_topic: The research topic to generate hypotheses for
            num_hypotheses: Number of hypotheses to generate
            progress_callback: Callback function(progress, step, count) for updates
        
        Returns:
            List of generated hypotheses
        """
        logger.info(f"🔬 Starting hypothesis generation for: {research_topic}")
        
        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            hypotheses = await loop.run_in_executor(
                self.executor,
                self._generate_sync,
                research_topic,
                num_hypotheses,
                progress_callback
            )
            
            logger.info(f"✅ Generated {len(hypotheses)} hypotheses")
            return hypotheses
            
        except Exception as e:
            logger.error(f"❌ Hypothesis generation failed: {e}", exc_info=True)
            raise
    
    def _generate_sync(
        self,
        research_topic: str,
        num_hypotheses: int,
        progress_callback: Optional[Callable[[float, str, int], None]]
    ) -> List[HypothesisItem]:
        """
        Synchronous hypothesis generation (runs in thread executor).
        This is where we integrate with the actual RAG system.
        """
        try:
            # Import the RAG system (heavy import done in thread)
            from src.core.chromadb_manager import ChromaDBManager
            from src.core.llm_client import LLMClient
            from src.ai.hypothesis_tools import HypothesisGenerator, HypothesisCritic
            
            if progress_callback:
                progress_callback(5.0, "Initializing ChromaDB connection...", 0)
            
            # Initialize components
            chroma_manager = ChromaDBManager()
            llm_client = LLMClient()
            hypothesis_generator = HypothesisGenerator(llm_client)
            hypothesis_critic = HypothesisCritic(llm_client)
            
            if progress_callback:
                progress_callback(15.0, "Searching literature database...", 0)
            
            # Search for relevant papers
            query = research_topic
            results = chroma_manager.similarity_search(
                query=query,
                n_results=50  # Get top 50 relevant papers
            )
            
            if not results or not results.get("documents"):
                raise ValueError("No relevant papers found in database")
            
            if progress_callback:
                progress_callback(25.0, "Analyzing literature...", 0)
            
            # Extract papers
            papers = []
            for i in range(len(results["documents"])):
                paper = {
                    "text": results["documents"][i],
                    "metadata": results["metadatas"][i] if "metadatas" in results else {},
                    "distance": results["distances"][i] if "distances" in results else None
                }
                papers.append(paper)
            
            if progress_callback:
                progress_callback(30.0, f"Generating hypotheses (0/{num_hypotheses})...", 0)
            
            # Generate hypotheses
            hypotheses = []
            for i in range(num_hypotheses):
                try:
                    # Update progress
                    progress = 30.0 + (i / num_hypotheses) * 60.0
                    if progress_callback:
                        progress_callback(progress, f"Generating hypothesis {i+1}/{num_hypotheses}...", i)
                    
                    # Generate hypothesis using the actual generator
                    hypothesis_text = hypothesis_generator.generate_hypothesis(
                        topic=research_topic,
                        papers=papers[:20],  # Use top 20 papers
                        existing_hypotheses=[h.hypothesis_text for h in hypotheses]
                    )
                    
                    # Critique the hypothesis
                    critique = hypothesis_critic.critique_hypothesis(
                        hypothesis=hypothesis_text,
                        papers=papers[:10]
                    )
                    
                    # Parse scores from critique
                    scores = self._parse_scores(critique)
                    
                    # Extract citations from papers
                    citations = self._extract_citations(papers[:5])
                    
                    # Extract key concepts
                    key_concepts = self._extract_key_concepts(hypothesis_text)
                    
                    # Create hypothesis item
                    hypothesis_item = HypothesisItem(
                        id=i + 1,
                        hypothesis_text=hypothesis_text,
                        rationale=self._extract_rationale(hypothesis_text),
                        scores=scores,
                        citations=citations,
                        key_concepts=key_concepts,
                        experimental_approach=self._extract_experimental_design(hypothesis_text)
                    )
                    
                    hypotheses.append(hypothesis_item)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to generate hypothesis {i+1}: {e}")
                    # Continue with next hypothesis
                    continue
            
            if progress_callback:
                progress_callback(95.0, "Finalizing results...", len(hypotheses))
            
            # Save results
            self._save_results(hypotheses, research_topic)
            
            if progress_callback:
                progress_callback(100.0, "Complete!", len(hypotheses))
            
            return hypotheses
            
        except Exception as e:
            logger.error(f"❌ Error in sync generation: {e}", exc_info=True)
            raise
    
    def _parse_scores(self, critique: str) -> HypothesisScores:
        """Parse scores from critique text."""
        # Default scores
        scores = {
            "novelty": 3.0,
            "accuracy": 3.0,
            "relevancy": 3.0,
            "feasibility": 3.0
        }
        
        # Try to extract scores from critique
        import re
        score_patterns = [
            (r"novelty[:\s]+(\d+\.?\d*)", "novelty"),
            (r"accuracy[:\s]+(\d+\.?\d*)", "accuracy"),
            (r"relevancy[:\s]+(\d+\.?\d*)", "relevancy"),
            (r"relevance[:\s]+(\d+\.?\d*)", "relevancy"),
            (r"feasibility[:\s]+(\d+\.?\d*)", "feasibility"),
        ]
        
        for pattern, key in score_patterns:
            match = re.search(pattern, critique.lower())
            if match:
                try:
                    score = float(match.group(1))
                    if 0 <= score <= 5:
                        scores[key] = score
                except ValueError:
                    pass
        
        overall = sum(scores.values()) / len(scores)
        
        return HypothesisScores(
            novelty=scores["novelty"],
            accuracy=scores["accuracy"],
            relevancy=scores["relevancy"],
            feasibility=scores["feasibility"],
            overall=round(overall, 2)
        )
    
    def _extract_citations(self, papers: List[Dict]) -> List[HypothesisCitation]:
        """Extract citations from papers."""
        citations = []
        
        for paper in papers[:5]:  # Limit to 5 citations
            metadata = paper.get("metadata", {})
            
            citation = HypothesisCitation(
                title=metadata.get("title", "Unknown Title"),
                authors=metadata.get("authors", "").split(", ") if metadata.get("authors") else ["Unknown"],
                journal=metadata.get("journal"),
                year=metadata.get("year"),
                doi=metadata.get("doi"),
                pmid=metadata.get("pmid"),
                url=metadata.get("url")
            )
            citations.append(citation)
        
        return citations
    
    def _extract_key_concepts(self, hypothesis_text: str) -> List[str]:
        """Extract key concepts from hypothesis text."""
        # Simple extraction - could be improved with NLP
        import re
        
        # Extract capitalized phrases and technical terms
        concepts = set()
        
        # Find capitalized words and abbreviations
        capitalized = re.findall(r'\b[A-Z][A-Z0-9-]+\b', hypothesis_text)
        concepts.update(capitalized[:10])
        
        # Common biological/medical terms
        technical_terms = [
            "ubiquitination", "degradation", "protein", "pathway",
            "expression", "regulation", "signaling", "cancer",
            "immune", "therapy", "checkpoint", "receptor"
        ]
        
        for term in technical_terms:
            if term.lower() in hypothesis_text.lower():
                concepts.add(term)
        
        return list(concepts)[:8]  # Limit to 8 concepts
    
    def _extract_rationale(self, hypothesis_text: str) -> str:
        """Extract rationale section from hypothesis."""
        # Look for rationale section
        import re
        
        # Try to find rationale section
        patterns = [
            r"rationale[:\s]+(.*?)(?=\n\n|\Z)",
            r"3\.\s*rationale[:\s]+(.*?)(?=\n\n|\Z)",
            r"reasoning[:\s]+(.*?)(?=\n\n|\Z)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, hypothesis_text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        # If no specific section found, return first part of text
        lines = hypothesis_text.split('\n')
        return '\n'.join(lines[:3]).strip() if lines else hypothesis_text[:200]
    
    def _extract_experimental_design(self, hypothesis_text: str) -> Optional[str]:
        """Extract experimental design section from hypothesis."""
        import re
        
        patterns = [
            r"experimental design[:\s]+(.*?)(?=\n\n|\Z)",
            r"2\.\s*experimental design[:\s]+(.*?)(?=\n\n|\Z)",
            r"methods[:\s]+(.*?)(?=\n\n|\Z)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, hypothesis_text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _save_results(self, hypotheses: List[HypothesisItem], research_topic: str):
        """Save results to output directory."""
        output_file = os.path.join(self.output_dir, f"hypotheses_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json")
        
        data = {
            "research_topic": research_topic,
            "generated_at": datetime.utcnow().isoformat(),
            "total_count": len(hypotheses),
            "hypotheses": [h.model_dump() for h in hypotheses]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"💾 Results saved to: {output_file}")

