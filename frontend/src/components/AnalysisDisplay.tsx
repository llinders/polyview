import React from 'react';
import type { AnalysisReport } from '../types';
import { PerspectiveCard } from './PerspectiveCard';

interface AnalysisDisplayProps {
  report: AnalysisReport;
}

export const AnalysisDisplay: React.FC<AnalysisDisplayProps> = ({ report }) => {
  return (
    <div className="space-y-8 animate-fadeIn">
      <div>
        <h2 className="text-3xl font-semibold text-sky-400 mb-3">
          Analysis for: <span className="text-slate-100">{report.topic}</span>
        </h2>
        <p className="text-xs text-slate-500 mb-4">Generated on: {new Date(report.timestamp).toLocaleString()}</p>
        
        <div className="bg-slate-700/50 p-6 rounded-lg shadow">
            <h3 className="text-xl font-semibold text-teal-400 mb-2">Overall Summary</h3>
            <p className="text-slate-300 leading-relaxed">{report.overallSummary}</p>
        </div>
      </div>

      <div>
        <h3 className="text-2xl font-semibold text-sky-400 mb-4">Identified Perspectives</h3>
        {report.perspectives.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {report.perspectives.map((perspective) => (
              <PerspectiveCard key={perspective.id} perspective={perspective} />
            ))}
          </div>
        ) : (
          <p className="text-slate-400">No distinct perspectives could be identified for this topic.</p>
        )}
      </div>
      {/* 
      // Optional: For debugging raw response
      {report.rawResponse && (
        <details className="mt-4">
          <summary className="cursor-pointer text-slate-400 hover:text-slate-200">View Raw AI Response (Debug)</summary>
          <pre className="mt-2 p-4 bg-slate-900 text-xs text-slate-300 rounded-md overflow-x-auto">
            {report.rawResponse}
          </pre>
        </details>
      )}
      */}
    </div>
  );
};
