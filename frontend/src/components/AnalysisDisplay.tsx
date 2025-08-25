import React from 'react';
import type { Perspective } from '../types';
import { PerspectiveCard } from './PerspectiveCard';

interface AnalysisDisplayProps {
  topic: string;
  overallSummary?: string;
  perspectives?: Perspective[];
}

export const AnalysisDisplay: React.FC<AnalysisDisplayProps> = ({ topic, overallSummary, perspectives }) => {
  const showSummary = overallSummary !== undefined && overallSummary !== null && overallSummary.trim() !== '';
  const showPerspectives = perspectives !== undefined && perspectives !== null && perspectives.length > 0;

  return (
    <div className="space-y-8 animate-fadeIn">
      <div>
        <h2 className="text-3xl font-semibold text-sky-400 mb-3">
          Analysis for: <span className="text-slate-100">{topic}</span>
        </h2>
        {/* <p className="text-xs text-slate-500 mb-4">Generated on: {new Date(report.timestamp).toLocaleString()}</p> */}
        
        <div className="bg-slate-700/50 p-6 rounded-lg shadow">
            <h3 className="text-xl font-semibold text-teal-400 mb-2">Overall Summary</h3>
            {showSummary ? (
                <p className="text-slate-300 leading-relaxed">{overallSummary}</p>
            ) : (
                <div className="space-y-2.5 animate-pulse">
                  <div className="h-4 bg-slate-700 rounded w-full"></div>
                  <div className="h-4 bg-slate-700 rounded w-5/6"></div>
                  <div className="h-4 bg-slate-700 rounded w-4/5"></div>
                </div>
            )}
        </div>
      </div>

      <div>
        <h3 className="text-2xl font-semibold text-sky-400 mb-4">Identified Perspectives</h3>
        {showPerspectives ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {perspectives.map((perspective) => (
              <PerspectiveCard key={perspective.id} perspective={perspective} />
            ))}
          </div>
        ) : (
          <div className="space-y-2.5 animate-pulse">
            <div className="h-4 bg-slate-700 rounded w-full"></div>
            <div className="h-4 bg-slate-700 rounded w-3/4"></div>
          </div>
        )}
      </div>
    </div>
  );
};
