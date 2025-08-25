import React, { useState } from 'react';
import type { Perspective } from '../types';
import { CredibilityLevel, FactCheckStatus } from '../types';
import { CheckCircleIcon } from './icons/CheckCircleIcon';
import { XCircleIcon } from './icons/XCircleIcon';
import { QuestionMarkCircleIcon } from './icons/QuestionMarkCircleIcon';
import { ShieldCheckIcon } from './icons/ShieldCheckIcon';
import { ShieldExclamationIcon } from './icons/ShieldExclamationIcon';
import { InformationCircleIcon } from './icons/InformationCircleIcon';

type ExpandedSection = 'evidence' | 'strengths' | 'weaknesses' | null;

const FactCheckStatusIcon: React.FC<{ status: FactCheckStatus }> = ({ status }) => {
  switch (status) {
    case FactCheckStatus.VERIFIED:
      return <CheckCircleIcon className="w-5 h-5 text-green-400" />;
    case FactCheckStatus.DISPUTED:
      return <XCircleIcon className="w-5 h-5 text-red-400" />;
    case FactCheckStatus.UNVERIFIED:
      return <QuestionMarkCircleIcon className="w-5 h-5 text-yellow-400" />;
    case FactCheckStatus.IN_PROGRESS:
      return <InformationCircleIcon className="w-5 h-5 text-blue-400" />;
    default:
      return <InformationCircleIcon className="w-5 h-5 text-slate-500" />;
  }
};

const CredibilityIcon: React.FC<{ level: CredibilityLevel }> = ({ level }) => {
  switch (level) {
    case CredibilityLevel.HIGH:
      return <ShieldCheckIcon className="w-5 h-5 text-green-400" />;
    case CredibilityLevel.MEDIUM:
      return <ShieldExclamationIcon className="w-5 h-5 text-yellow-400" />;
    case CredibilityLevel.LOW:
      return <ShieldExclamationIcon className="w-5 h-5 text-red-400" />;
    default:
      return <InformationCircleIcon className="w-5 h-5 text-slate-500" />;
  }
};

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
          <CredibilityIcon level={perspective.credibility} />
          <span>Credibility: <span className={`font-semibold`}>{perspective.credibility}</span></span>
        </div>
        <div className="flex items-center space-x-2 text-slate-300">
          <FactCheckStatusIcon status={perspective.factCheckStatus} />
          <span>Fact-Check: <span className={`font-semibold`}>{perspective.factCheckStatus}</span></span>
        </div>
      </div>

      <p className="text-slate-300 mb-4 leading-relaxed text-sm">{perspective.summary}</p>

      {renderCollapsibleSection('evidence', 'Supporting Points / Evidence', perspective.evidence)}
      {renderCollapsibleSection('strengths', 'Strengths', perspective.strengths)}
      {renderCollapsibleSection('weaknesses', 'Weaknesses', perspective.weaknesses)}
    </div>
  );
};
