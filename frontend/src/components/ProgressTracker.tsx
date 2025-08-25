
import React from 'react';
import { ANALYSIS_STEPS, formatStepName } from '../constants';
import { Spinner } from './Spinner';
import CircleIcon from './icons/CircleIcon';
import { CheckCircleIcon } from './icons/CheckCircleIcon';
import './ProgressTracker.css';

interface ProgressTrackerProps {
  currentStep: number;
  iteration?: number;
  articlesFound?: number;
}

export const ProgressTracker: React.FC<ProgressTrackerProps> = ({ currentStep, iteration, articlesFound }) => {
  return (
    <div className="progress-tracker-container">
      <ul className="progress-steps">
        {ANALYSIS_STEPS.map((step, index) => {
          const isCompleted = index < currentStep;
          const isCurrent = index === currentStep;

          return (
            <li key={step} className={`step ${isCompleted ? 'completed' : ''} ${isCurrent ? 'current' : ''}`}>
              <div className="step-icon">
                {isCompleted ? <CheckCircleIcon /> : isCurrent ? <Spinner /> : <CircleIcon />}
              </div>
              <div className="step-label">
                <span className="step-name-text">{formatStepName(step)}</span>
                {step === 'search_agent' && articlesFound !== undefined && (
                  <span className="step-stats">Articles Found: {articlesFound}</span>
                )}
                 {step === 'search_agent' && iteration !== undefined && (
                  <span className="step-stats">Iteration: {iteration}</span>
                )}
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
};
