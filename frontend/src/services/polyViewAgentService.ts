import type { AnalysisReport, Perspective } from './types';
import mockData from '../mock-data.json';
import { ANALYSIS_STEPS } from '../constants';

const API_BASE_URL = 'http://localhost:8000/api/v1';
const WS_BASE_URL = 'ws://localhost:8000/api/v1/ws';

export interface AnalysisMessage {
  type: 'status' | 'partial_result' | 'final_result' | 'error' | 'end_of_stream';
  message?: string;
  step_name?: string;
  data?: {
    type?: 'summary' | 'perspective' | 'cluster_count'; // New field to indicate data type
    content?: string; // For summary
    perspective?: Perspective; // For individual perspective
    count?: number; // For cluster count
    topic?: string; // For final result
    overallSummary?: string; // For final result
    perspectives?: Perspective[]; // For final result
  };
}

interface AnalysisCallbacks {
  onAnalysisUpdate: (report: AnalysisReport) => void;
  onStatusUpdate: (message: AnalysisMessage) => void;
  onPartialSummary: (summary: string) => void;
  onPartialPerspective: (perspective: Perspective) => void;
  onClusterCount: (count: number) => void; // New callback
  onError: (error: string) => void;
  onIsLoading: (loading: boolean) => void;
  onSessionId: (sessionId: string) => void;
}

const handleMockData = (callbacks: AnalysisCallbacks) => {
  const { onStatusUpdate, onAnalysisUpdate, onIsLoading, onPartialSummary, onPartialPerspective, onClusterCount } = callbacks;

  let currentStepIndex = 0;
  let perspectiveIndex = 0;
  let summarySent = false;

  const mockInterval = setInterval(() => {
    if (currentStepIndex < ANALYSIS_STEPS.length) {
      // Send status update for the completed step
      onStatusUpdate({
        type: 'status',
        message: `Completed step: ${ANALYSIS_STEPS[currentStepIndex]} `,
        step_name: ANALYSIS_STEPS[currentStepIndex],
      });

      // After clustering, send cluster count
      if (ANALYSIS_STEPS[currentStepIndex] === 'perspective_clustering') {
        onStatusUpdate({
          type: 'partial_result',
          data: {
            type: 'cluster_count',
            count: mockData.perspectives.length,
          },
        });
      }

      currentStepIndex++;
    } else if (!summarySent) {
      // Send summary
      onPartialSummary(mockData.overallSummary);
      summarySent = true;
    } else if (perspectiveIndex < mockData.perspectives.length) {
      // Send individual perspectives
      const mockPerspective = mockData.perspectives[perspectiveIndex];
      onPartialPerspective({
        id: mockPerspective.perspective_name,
        title: mockPerspective.perspective_name,
        summary: mockPerspective.narrative,
        evidence: mockPerspective.supporting_evidence?.map((e: string, i: number) => ({ id: `${mockPerspective.perspective_name}-evidence-${i}`, statement: e })) || [],
        strengths: mockPerspective.strengths || [],
        weaknesses: mockPerspective.weaknesses || [],
        rated_perspective_strength: mockPerspective.rated_perspective_strength || 0,
      });
      perspectiveIndex++;
    } else {
      // All data sent, send final report and clear interval
      clearInterval(mockInterval);
      const report: AnalysisReport = {
          topic: mockData.topic,
          overallSummary: mockData.overallSummary,
          perspectives: mockData.perspectives.map((p: any) => ({
            id: p.perspective_name, // Or generate a unique ID
            title: p.perspective_name,
            summary: p.narrative,
            evidence: p.supporting_evidence?.map((e: string, i: number) => ({ id: `${p.perspective_name}-evidence-${i}`, statement: e })) || [],
            strengths: p.strengths || [],
            weaknesses: p.weaknesses || [],
            rated_perspective_strength: p.rated_perspective_strength || 0,
          })),
          timestamp: new Date().toISOString(),
        };
      onAnalysisUpdate(report);
      onIsLoading(false);
    }
  }, 1000);
};

export const startAnalysis = async (topic: string, callbacks: AnalysisCallbacks) => {
  const { onIsLoading, onError, onSessionId } = callbacks;

  onIsLoading(true);

  const useMockData = localStorage.getItem('useMockData') === 'true';

  if (useMockData) {
    handleMockData(callbacks);
    return;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ topic }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    onSessionId(data.session_id);
  } catch (err) {
    console.error("Analysis error:", err);
    if (err instanceof Error) {
        onError(`Failed to start analysis: ${err.message}`);
    } else {
        onError("An unknown error occurred during analysis.");
    }
    onIsLoading(false);
  }
};

export const connectToWebSocket = (sessionId: string, callbacks: AnalysisCallbacks) => {
    const { onStatusUpdate, onAnalysisUpdate, onError, onPartialSummary, onPartialPerspective, onClusterCount } = callbacks;
    const ws = new WebSocket(`${WS_BASE_URL}/${sessionId}`);

    ws.onopen = () => {
        // Optional: send a message to confirm connection, but not a step update
    };

    ws.onmessage = (event) => {
        const msg: AnalysisMessage = JSON.parse(event.data);

        if (msg.type === 'status') {
            onStatusUpdate(msg);
        } else if (msg.type === 'partial_result') {
            if (msg.data?.type === 'summary' && msg.data.content) {
                onPartialSummary(msg.data.content);
            } else if (msg.data?.type === 'perspective' && msg.data.perspective) {
                onPartialPerspective(msg.data.perspective);
            } else if (msg.data?.type === 'cluster_count' && typeof msg.data.count === 'number') {
                onClusterCount(msg.data.count);
            }
        } else if (msg.type === 'final_result') {
            const report: AnalysisReport = {
                topic: msg.data.topic,
                overallSummary: msg.data.overallSummary,
                perspectives: msg.data.perspectives.map((p: any) => ({
                    id: p.perspective_name, // Or generate a unique ID
                    title: p.perspective_name,
                    summary: p.narrative,
                    evidence: p.supporting_evidence?.map((e: string, i: number) => ({ id: `${p.perspective_name}-evidence-${i}`, statement: e })) || [],
                    strengths: p.strengths || [],
                    weaknesses: p.weaknesses || [],
                    rated_perspective_strength: p.rated_perspective_strength || 0,
                })),
                timestamp: new Date().toISOString(),
            };
            onAnalysisUpdate(report);
        } else if (msg.type === 'error') {
            onError(msg.message || 'An unknown error occurred.');
        } else if (msg.type === 'end_of_stream') {
            ws.close();
        }
    };

    ws.onclose = () => {
        // WebSocket closed
    };

    ws.onerror = (event) => {
        console.error("WebSocket error:", event);
        onError('WebSocket connection error.');
    };

    return ws;
};