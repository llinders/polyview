export interface Evidence {
  id: string;
  statement: string;
  source?: string;
}

export interface Perspective {
  id: string;
  title: string;
  summary: string;
  evidence: Evidence[];
  strengths?: string[];
  weaknesses?: string[];
  rated_perspective_strength: number;
}

export interface AnalysisReport {
  topic: string;
  overallSummary: string;
  perspectives: Perspective[];
  timestamp: string;
  rawResponse?: string; // For debugging
}

export interface RawPerspectiveData {
  perspective_name: string;
  narrative: string;
  supporting_evidence?: string[];
  strengths?: string[];
  weaknesses?: string[];
  rated_perspective_strength?: number;
}