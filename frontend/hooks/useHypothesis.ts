
/**
 * Hook for hypothesis generation management
 */

import { useState, useCallback, useEffect } from "react";
import { apiClient } from "@/lib/api";
import type {
  HypothesisGenerateRequest,
  HypothesisStatus,
  HypothesisResult,
  WebSocketMessage,
} from "@/lib/types";

export function useHypothesis(wsMessage: WebSocketMessage | null) {
  const [status, setStatus] = useState<HypothesisStatus | null>(null);
  const [result, setResult] = useState<HypothesisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);

  // Update status from WebSocket messages
  useEffect(() => {
    if (!wsMessage || wsMessage.type !== "progress") return;

    if (wsMessage.job_id === currentJobId) {
      setStatus((prev) => ({
        ...prev!,
        status: wsMessage.status || prev!.status,
        progress: wsMessage.progress ?? prev!.progress,
        current_step: wsMessage.current_step || prev!.current_step,
        hypotheses_generated:
          wsMessage.hypotheses_generated ?? prev!.hypotheses_generated,
        total_hypotheses: wsMessage.total_hypotheses ?? prev!.total_hypotheses,
      }));
    }
  }, [wsMessage, currentJobId]);

  const generate = useCallback(async (request: HypothesisGenerateRequest) => {
    try {
      setError(null);
      setResult(null);

      const response = await apiClient.generateHypotheses(request);
      setCurrentJobId(response.job_id);

      // Initial status
      setStatus({
        job_id: response.job_id,
        status: response.status,
        progress: 0,
        current_step: "Starting...",
        hypotheses_generated: 0,
        total_hypotheses: request.num_hypotheses,
      });

      return response.job_id;
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to start generation";
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, []);

  const pollStatus = useCallback(async (jobId: string) => {
    try {
      const statusData = await apiClient.getHypothesisStatus(jobId);
      setStatus(statusData);
      return statusData;
    } catch (err) {
      console.error("Failed to poll status:", err);
      return null;
    }
  }, []);

  const fetchResults = useCallback(async (jobId: string) => {
    try {
      const resultData = await apiClient.getHypothesisResults(jobId);
      setResult(resultData);
      return resultData;
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to fetch results";
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, []);

  const cancel = useCallback(async (jobId: string) => {
    try {
      await apiClient.cancelHypothesisJob(jobId);
      setStatus((prev) =>
        prev ? { ...prev, status: "cancelled" } : null
      );
    } catch (err) {
      console.error("Failed to cancel job:", err);
    }
  }, []);

  const reset = useCallback(() => {
    setStatus(null);
    setResult(null);
    setError(null);
    setCurrentJobId(null);
  }, []);

  return {
    status,
    result,
    error,
    currentJobId,
    generate,
    pollStatus,
    fetchResults,
    cancel,
    reset,
  };
}

