"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { apiClient } from "@/lib/api";
import type { HypothesisResult, ExportFormat } from "@/lib/types";
import { Download, FileJson, FileSpreadsheet, FileText } from "lucide-react";

export default function ResultsPage() {
  const searchParams = useSearchParams();
  const jobId = searchParams.get("jobId");

  const [result, setResult] = useState<HypothesisResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exportingFormat, setExportingFormat] = useState<ExportFormat | null>(null);

  useEffect(() => {
    if (jobId) {
      loadResults();
    }
  }, [jobId]);

  const loadResults = async () => {
    if (!jobId) return;

    try {
      const data = await apiClient.getHypothesisResults(jobId);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load results");
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format: ExportFormat) => {
    if (!jobId) return;

    try {
      setExportingFormat(format);
      const exportResponse = await apiClient.createExport({
        job_id: jobId,
        format,
        include_citations: true,
        include_scores: true,
      });

      if (exportResponse.success && exportResponse.download_url) {
        // Trigger download
        window.location.href = apiClient.getDownloadURL(exportResponse.filename);
      }
    } catch (err) {
      console.error("Export failed:", err);
    } finally {
      setExportingFormat(null);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
        <p className="text-muted-foreground">Loading results...</p>
      </div>
    );
  }

  if (error || !result) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Error Loading Results</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">{error || "Results not found"}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-3xl font-bold">Hypothesis Results</h2>
          <p className="text-muted-foreground mt-2">
            Topic: {result.research_topic}
          </p>
          <p className="text-sm text-muted-foreground">
            Generated: {new Date(result.generated_at).toLocaleString()} •{" "}
            {result.total_count} hypotheses
          </p>
        </div>

        {/* Export Buttons */}
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleExport("json")}
            disabled={exportingFormat !== null}
          >
            <FileJson className="h-4 w-4 mr-2" />
            JSON
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleExport("excel")}
            disabled={exportingFormat !== null}
          >
            <FileSpreadsheet className="h-4 w-4 mr-2" />
            Excel
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleExport("csv")}
            disabled={exportingFormat !== null}
          >
            <FileText className="h-4 w-4 mr-2" />
            CSV
          </Button>
        </div>
      </div>

      {/* Hypotheses List */}
      <div className="space-y-4">
        {result.hypotheses.map((hypothesis) => (
          <Card key={hypothesis.id}>
            <CardHeader>
              <div className="flex justify-between items-start">
                <CardTitle className="text-xl">
                  Hypothesis #{hypothesis.id}
                </CardTitle>
                <div className="flex gap-2 text-sm">
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">
                    Novelty: {hypothesis.scores.novelty.toFixed(1)}
                  </span>
                  <span className="px-2 py-1 bg-green-100 text-green-800 rounded">
                    Accuracy: {hypothesis.scores.accuracy.toFixed(1)}
                  </span>
                  <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded">
                    Relevancy: {hypothesis.scores.relevancy.toFixed(1)}
                  </span>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="font-semibold mb-2">Hypothesis</h4>
                <p className="text-sm">{hypothesis.hypothesis_text}</p>
              </div>

              <div>
                <h4 className="font-semibold mb-2">Rationale</h4>
                <p className="text-sm text-muted-foreground">
                  {hypothesis.rationale}
                </p>
              </div>

              {hypothesis.experimental_approach && (
                <div>
                  <h4 className="font-semibold mb-2">Experimental Approach</h4>
                  <p className="text-sm text-muted-foreground">
                    {hypothesis.experimental_approach}
                  </p>
                </div>
              )}

              <div>
                <h4 className="font-semibold mb-2">Key Concepts</h4>
                <div className="flex flex-wrap gap-2">
                  {hypothesis.key_concepts.map((concept, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-1 bg-secondary text-secondary-foreground rounded-md text-xs"
                    >
                      {concept}
                    </span>
                  ))}
                </div>
              </div>

              {hypothesis.citations.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-2">
                    Citations ({hypothesis.citations.length})
                  </h4>
                  <div className="space-y-2">
                    {hypothesis.citations.slice(0, 3).map((citation, idx) => (
                      <div
                        key={idx}
                        className="text-xs text-muted-foreground border-l-2 border-muted pl-3"
                      >
                        <p className="font-medium">{citation.title}</p>
                        <p>
                          {citation.authors.slice(0, 3).join(", ")}
                          {citation.authors.length > 3 && " et al."}
                          {citation.year && ` (${citation.year})`}
                          {citation.journal && ` - ${citation.journal}`}
                        </p>
                      </div>
                    ))}
                    {hypothesis.citations.length > 3 && (
                      <p className="text-xs text-muted-foreground">
                        +{hypothesis.citations.length - 3} more citations
                      </p>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

