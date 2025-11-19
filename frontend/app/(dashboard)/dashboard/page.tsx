"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ArrowRight, Database, FileText, Sparkles } from "lucide-react";
import { apiClient } from "@/lib/api";
import type { DatabaseStatus } from "@/lib/types";

export default function DashboardPage() {
  const router = useRouter();
  const [dbStatus, setDbStatus] = useState<DatabaseStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDatabaseStatus();
  }, []);

  const loadDatabaseStatus = async () => {
    try {
      const status = await apiClient.getDatabaseStatus();
      setDbStatus(status);
    } catch (error) {
      console.error("Failed to load database status:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="text-center space-y-2">
        <h2 className="text-4xl font-bold">Welcome to AI Research Processor</h2>
        <p className="text-xl text-muted-foreground">
          Generate novel scientific hypotheses powered by AI and comprehensive
          literature analysis
        </p>
      </div>

      {/* Database Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Database Status
          </CardTitle>
          <CardDescription>
            Literature database statistics and connectivity
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-muted-foreground">Loading...</p>
          ) : dbStatus?.is_connected ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-secondary rounded-lg">
                <p className="text-2xl font-bold">
                  {dbStatus.total_documents.toLocaleString()}
                </p>
                <p className="text-sm text-muted-foreground">Total Documents</p>
              </div>
              <div className="text-center p-4 bg-secondary rounded-lg">
                <p className="text-2xl font-bold">
                  {dbStatus.source_breakdown.pubmed.toLocaleString()}
                </p>
                <p className="text-sm text-muted-foreground">PubMed</p>
              </div>
              <div className="text-center p-4 bg-secondary rounded-lg">
                <p className="text-2xl font-bold">
                  {dbStatus.source_breakdown.biorxiv.toLocaleString()}
                </p>
                <p className="text-sm text-muted-foreground">BioRxiv</p>
              </div>
              <div className="text-center p-4 bg-secondary rounded-lg">
                <p className="text-2xl font-bold">
                  {dbStatus.source_breakdown.semantic_scholar.toLocaleString()}
                </p>
                <p className="text-sm text-muted-foreground">
                  Semantic Scholar
                </p>
              </div>
            </div>
          ) : (
            <div className="text-center p-8 text-destructive">
              ❌ Database connection failed
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid md:grid-cols-2 gap-6">
        <Card className="hover:shadow-lg transition-shadow cursor-pointer"
          onClick={() => router.push("/dashboard/generate")}
        >
          <CardHeader>
            <Sparkles className="h-8 w-8 text-primary mb-2" />
            <CardTitle>Generate Hypotheses</CardTitle>
            <CardDescription>
              Start generating AI-powered research hypotheses from your research
              topic
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button className="w-full">
              Get Started
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow cursor-pointer"
          onClick={() => router.push("/dashboard/results")}
        >
          <CardHeader>
            <FileText className="h-8 w-8 text-primary mb-2" />
            <CardTitle>View Results</CardTitle>
            <CardDescription>
              Access and export your previously generated hypothesis results
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline" className="w-full">
              View Results
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Features */}
      <Card>
        <CardHeader>
          <CardTitle>Features</CardTitle>
          <CardDescription>
            What you can do with AI Research Processor
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm">
            <li className="flex items-start gap-2">
              <span className="text-primary">✓</span>
              <span>
                <strong>AI-Powered Generation:</strong> Leverage advanced AI
                models to generate novel, scientifically-sound hypotheses
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary">✓</span>
              <span>
                <strong>Literature-Based:</strong> Hypotheses are grounded in
                extensive scientific literature analysis
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary">✓</span>
              <span>
                <strong>Scoring & Evaluation:</strong> Each hypothesis is
                scored for novelty, accuracy, and relevancy
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary">✓</span>
              <span>
                <strong>Export Options:</strong> Download results in JSON,
                Excel, CSV, or PDF formats
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary">✓</span>
              <span>
                <strong>Real-time Progress:</strong> Watch your hypotheses
                being generated in real-time
              </span>
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}

