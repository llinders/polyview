import React, { useState } from 'react';
import type { Perspective } from '../types';
import StarIcon from './icons/StarIcon';

type ExpandedSection = 'evidence' | 'strengths' | 'weaknesses' | null;

export const PerspectiveCard: React.FC<{ perspective: Perspective }> = ({ perspective }) => {
  const [expandedSection, setExpandedSection] = useState<ExpandedSection>(null);

  const toggleSection = (section: ExpandedSection) => {
    setExpandedSection(prev => (prev === section ? null : section));
  };

  const renderCollapsibleSection = (sectionName: 'evidence' | 'strengths' | 'weaknesses', title: string, items: any[] | undefined) => {
    if (!items || items.length === 0) return null;

    const isExpanded = expandedSection === sectionName;

    return (
      <div className="mt-4 border-t border-slate-700 pt-4">
        <button onClick={() => toggleSection(sectionName)} className="w-full text-left font-semibold text-sky-400 hover:text-sky-300 flex justify-between items-center">
          <span>{title}</span>
          <span className={`transform transition-transform duration-200 ${isExpanded ? 'rotate-90' : ''}`}>►</span>
        </button>
        {isExpanded && (
          <ul className="mt-2 pl-5 border-l-2 border-slate-700 text-slate-400 space-y-2 text-sm">
            {items.map((item, index) => (
              <li key={index}>{typeof item === 'string' ? item : item.statement}</li>
            ))}
          </ul>
        )}
      </div>
    );
  };

  return (
    <div className="bg-slate-700/70 p-6 rounded-lg shadow-lg border border-slate-600 hover:border-sky-500/50 transition-all duration-300 ease-in-out transform hover:scale-[1.01]">
      <h4 className="text-xl font-bold text-cyan-400 mb-3">{perspective.title}</h4>
      
      <div className="flex flex-wrap gap-x-6 gap-y-2 mb-4 text-sm">
        <div className="flex items-center space-x-2 text-slate-300">
          <StarIcon className="w-5 h-5 text-yellow-400" />
          <span>Rated Perspective Strength: <span className={`font-semibold`}>{perspective.rated_perspective_strength}/5</span></span>
        </div>
      </div>

      <p className="text-slate-300 mb-4 leading-relaxed text-sm">{perspective.summary}</p>

      {renderCollapsibleSection('evidence', 'Supporting Points / Evidence', perspective.evidence)}
      {renderCollapsibleSection('strengths', 'Strengths', perspective.strengths)}
      {renderCollapsibleSection('weaknesses', 'Weaknesses', perspective.weaknesses)}
    </div>
  );
};
