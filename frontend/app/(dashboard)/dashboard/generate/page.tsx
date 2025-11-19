"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useSession } from "@/hooks/useSession";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useHypothesis } from "@/hooks/useHypothesis";
import { useRouter } from "next/navigation";
import { Sparkles, Loader2, CheckCircle2, XCircle } from "lucide-react";

export default function GeneratePage() {
  const router = useRouter();
  const { session } = useSession();
  const { lastMessage } = useWebSocket(session?.session_id || null);
  const { status, result, error, generate, reset } = useHypothesis(lastMessage);

  const [researchTopic, setResearchTopic] = useState("");
  const [numHypotheses, setNumHypotheses] = useState(10);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerate = async () => {
    if (!researchTopic.trim()) {
      return;
    }

    try {
      setIsGenerating(true);
      await generate({
        research_topic: researchTopic,
        num_hypotheses: numHypotheses,
      });
    } catch (err) {
      console.error("Generation failed:", err);
      setIsGenerating(false);
    }
  };

  const handleViewResults = () => {
    if (result) {
      router.push(`/dashboard/results?jobId=${result.job_id}`);
    }
  };

  const handleReset = () => {
    reset();
    setIsGenerating(false);
    setResearchTopic("");
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-3xl font-bold">Generate Hypotheses</h2>
        <p className="text-muted-foreground mt-2">
          Enter your research topic to generate AI-powered scientific hypotheses
        </p>
      </div>

      {/* Input Form */}
      {!isGenerating && !result && (
        <Card>
          <CardHeader>
            <CardTitle>Research Topic</CardTitle>
            <CardDescription>
              Describe your research area or specific question
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="topic">Research Topic *</Label>
              <Input
                id="topic"
                placeholder="e.g., UBR-5 role in cancer immunotherapy"
                value={researchTopic}
                onChange={(e) => setResearchTopic(e.target.value)}
                className="text-lg"
              />
              <p className="text-xs text-muted-foreground">
                Be specific about your research area for better results
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="count">Number of Hypotheses</Label>
              <div className="flex items-center gap-4">
                <Input
                  id="count"
                  type="number"
                  min="1"
                  max="50"
                  value={numHypotheses}
                  onChange={(e) =>
                    setNumHypotheses(parseInt(e.target.value) || 10)
                  }
                  className="w-24"
                />
                <span className="text-sm text-muted-foreground">
                  (1-50 hypotheses)
                </span>
              </div>
            </div>

            {error && (
              <div className="bg-destructive/10 text-destructive p-3 rounded-md text-sm">
                {error}
              </div>
            )}

            <Button
              onClick={handleGenerate}
              disabled={!researchTopic.trim()}
              className="w-full"
              size="lg"
            >
              <Sparkles className="mr-2 h-5 w-5" />
              Generate Hypotheses
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Progress Display */}
      {isGenerating && status && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {status.status === "completed" ? (
                <CheckCircle2 className="h-6 w-6 text-green-500" />
              ) : status.status === "failed" ? (
                <XCircle className="h-6 w-6 text-destructive" />
              ) : (
                <Loader2 className="h-6 w-6 animate-spin" />
              )}
              {status.status === "completed"
                ? "Generation Complete!"
                : status.status === "failed"
                ? "Generation Failed"
                : "Generating Hypotheses..."}
            </CardTitle>
            <CardDescription>
              Topic: {researchTopic}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>{status.current_step}</span>
                <span className="text-muted-foreground">
                  {Math.round(status.progress)}%
                </span>
              </div>
              <Progress value={status.progress} className="h-3" />
            </div>

            <div className="flex justify-between items-center p-4 bg-secondary rounded-lg">
              <div>
                <p className="text-2xl font-bold">
                  {status.hypotheses_generated}
                </p>
                <p className="text-sm text-muted-foreground">
                  of {status.total_hypotheses} hypotheses
                </p>
              </div>
              {status.started_at && (
                <div className="text-right">
                  <p className="text-sm text-muted-foreground">
                    Started {new Date(status.started_at).toLocaleTimeString()}
                  </p>
                </div>
              )}
            </div>

            {status.status === "completed" && (
              <div className="space-y-2">
                <Button onClick={handleViewResults} className="w-full" size="lg">
                  View Results
                </Button>
                <Button
                  onClick={handleReset}
                  variant="outline"
                  className="w-full"
                >
                  Generate New Hypotheses
                </Button>
              </div>
            )}

            {status.status === "failed" && (
              <div>
                {status.error_message && (
                  <div className="bg-destructive/10 text-destructive p-3 rounded-md text-sm mb-2">
                    {status.error_message}
                  </div>
                )}
                <Button onClick={handleReset} variant="outline" className="w-full">
                  Try Again
                </Button>
              </div>
            )}

            {status.status === "in_progress" && (
              <Button
                variant="outline"
                className="w-full"
                onClick={() => {
                  setIsGenerating(false);
                  reset();
                }}
              >
                Cancel
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Information Cards */}
      {!isGenerating && !result && (
        <div className="grid md:grid-cols-2 gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">What to Expect</CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-2">
              <p>• Generation typically takes 2-5 minutes</p>
              <p>• Each hypothesis includes rationale and experimental design</p>
              <p>• Hypotheses are scored for novelty, accuracy, and relevancy</p>
              <p>• Citations are included from the literature database</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Tips for Best Results</CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-2">
              <p>• Be specific about your research area</p>
              <p>• Include key proteins, pathways, or mechanisms</p>
              <p>• Specify the disease or biological context</p>
              <p>• Use scientific terminology when relevant</p>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

