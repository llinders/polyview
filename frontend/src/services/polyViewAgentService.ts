
import type { AnalysisReport } from './types';
import mockData from '../mock-data.json';

const API_BASE_URL = 'http://localhost:8000/api/v1';
const WS_BASE_URL = 'ws://localhost:8000/api/v1/ws';

interface AnalysisMessage {
  type: 'status' | 'partial_result' | 'final_result' | 'error' | 'end_of_stream';
  message?: string;
  data?: any;
}

interface AnalysisCallbacks {
  onAnalysisUpdate: (report: AnalysisReport) => void;
  onStatusUpdate: (message: string) => void;
  onError: (error: string) => void;
  onIsLoading: (loading: boolean) => void;
  onSessionId: (sessionId: string) => void;
}

const handleMockData = (callbacks: AnalysisCallbacks) => {
  const { onStatusUpdate, onAnalysisUpdate, onIsLoading } = callbacks;

  onStatusUpdate('Using mock data. Simulating analysis...');

  setTimeout(() => {
    onStatusUpdate('Simulating perspective identification...');
  }, 1000);

  setTimeout(() => {
    onStatusUpdate('Simulating data synthesis...');
  }, 2000);

  setTimeout(() => {
    const report: AnalysisReport = {
        topic: mockData.topic,
        overallSummary: mockData.summary,
        perspectives: mockData.perspectives.map((p: any) => ({
          id: p.perspective_name, // Or generate a unique ID
          title: p.perspective_name,
          summary: p.narrative,
          evidence: p.supporting_evidence?.map((e: string, i: number) => ({ id: `${p.perspective_name}-evidence-${i}`, statement: e })) || [],
          credibility: p.credibility || 'Unknown',
          factCheckStatus: p.fact_check_status || 'Unverified',
          strengths: p.strengths || [],
          weaknesses: p.weaknesses || [],
        })),
        timestamp: new Date().toISOString(),
      };
    onAnalysisUpdate(report);
    onIsLoading(false);
  }, 3000);
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
    const { onStatusUpdate, onAnalysisUpdate, onError } = callbacks;
    const ws = new WebSocket(`${WS_BASE_URL}/${sessionId}`);

    ws.onopen = () => {
        onStatusUpdate('WebSocket connected. Waiting for analysis updates...');
    };

    ws.onmessage = (event) => {
        const msg: AnalysisMessage = JSON.parse(event.data);

        if (msg.type === 'status') {
            onStatusUpdate(msg.message || '');
        } else if (msg.type === 'final_result') {
            const report: AnalysisReport = {
                topic: msg.data.topic,
                overallSummary: msg.data.summary,
                perspectives: msg.data.perspectives.map((p: any) => ({
                    id: p.perspective_name, // Or generate a unique ID
                    title: p.perspective_name,
                    summary: p.narrative,
                    evidence: p.supporting_evidence?.map((e: string, i: number) => ({ id: `${p.perspective_name}-evidence-${i}`, statement: e })) || [],
                    credibility: p.credibility || 'Unknown',
                    factCheckStatus: p.fact_check_status || 'Unverified',
                    strengths: p.strengths || [],
                    weaknesses: p.weaknesses || [],
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
