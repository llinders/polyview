import React from 'react';

interface SummaryViewProps {
  topic: string;
  summary: string;
}

const SummaryView: React.FC<SummaryViewProps> = ({ topic, summary }) => {
  return (
    <div className="summary-section">
      <h2>Analysis Results for "{topic}"</h2>
      <h3>Summary:</h3>
      <p>{summary}</p>
    </div>
  );
};

export default SummaryView;
