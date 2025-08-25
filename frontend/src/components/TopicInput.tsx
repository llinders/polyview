import React, { useState } from 'react';

interface TopicInputProps {
  onSubmit: (topic: string) => void;
  isLoading: boolean;
}

export const TopicInput: React.FC<TopicInputProps> = ({ onSubmit, isLoading }) => {
  const [topic, setTopic] = useState<string>('');

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!topic.trim() || isLoading) return;
    onSubmit(topic);
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3 items-stretch">
      <input
        type="text"
        value={topic}
        onChange={(e) => setTopic(e.target.value)}
        placeholder="Enter a topic to analyze (e.g., climate change impacts)"
        className="flex-grow p-3 bg-slate-700 text-slate-100 border border-slate-600 rounded-lg focus:ring-2 focus:ring-sky-500 focus:border-sky-500 outline-none transition-shadow placeholder-slate-400"
        disabled={isLoading}
        aria-label="Topic for analysis"
      />
      <button
        type="submit"
        disabled={isLoading || !topic.trim()}
        className="px-6 py-3 bg-sky-600 hover:bg-sky-500 text-white font-semibold rounded-lg transition-colors duration-150 ease-in-out focus:outline-none focus:ring-2 focus:ring-sky-500 focus:ring-opacity-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
      >
        {isLoading ? (
          <>
            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Analyzing...
          </>
        ) : (
          'Analyze Topic'
        )}
      </button>
    </form>
  );
};
