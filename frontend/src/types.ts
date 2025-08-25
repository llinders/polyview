export interface Evidence {
  id: string;
  statement: string;
  source?: string;
}

export enum CredibilityLevel {
  HIGH = "High",
  MEDIUM = "Medium",
  LOW = "Low",
  UNKNOWN = "Unknown",
}

export enum FactCheckStatus {
  VERIFIED = "Verified",
  DISPUTED = "Disputed",
  UNVERIFIED = "Unverified",
  IN_PROGRESS = "In Progress",
  NOT_APPLICABLE = "Not Applicable"
}

export interface Perspective {
  id: string;
  title: string;
  summary: string;
  evidence: Evidence[];
  credibility: CredibilityLevel;
  factCheckStatus: FactCheckStatus;
  strengths?: string[];
  weaknesses?: string[];
}

export interface AnalysisReport {
  topic: string;
  overallSummary: string;
  perspectives: Perspective[];
  timestamp: string;
  rawResponse?: string; // For debugging
}

// For Gemini response parsing
export interface GeminiPerspectiveOutput {
  title: string;
  summary: string;
  mockEvidence: string[];
  mockCredibility: string; // "High", "Medium", "Low"
  mockFactCheckStatus: string; // "Verified", "Disputed", "Unverified"
}

export interface GeminiAnalysisOutput {
  overallSummary: string;
  perspectives: GeminiPerspectiveOutput[];
}
