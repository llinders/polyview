
import React, { useState, useEffect, useRef } from 'react';
import { TopicInput } from './components/TopicInput';
import { AnalysisDisplay } from './components/AnalysisDisplay';
import { ProgressTracker } from './components/ProgressTracker';
import Settings from './components/Settings';
import type { AnalysisReport } from './types';
import { APP_TITLE, APP_SUBTITLE, ANALYSIS_STEPS } from './constants';
import { startAnalysis, connectToWebSocket, type AnalysisMessage } from './services/polyViewAgentService';

const App: React.FC = () => {
  const [analysis, setAnalysis] = useState<AnalysisReport | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [iteration, setIteration] = useState<number | undefined>();
  const [articlesFound, setArticlesFound] = useState<number | undefined>();

  const ws = useRef<WebSocket | null>(null);

  const resetState = () => {
    setAnalysis(null);
    setIsLoading(false);
    setError(null);
    setSessionId(null);
    setCurrentStep(0);
    setIteration(undefined);
    setArticlesFound(undefined);
  };

  const handleStatusUpdate = (msg: AnalysisMessage) => {
    if (msg.step_name) {
      const completedStepIndex = ANALYSIS_STEPS.findIndex(step => step === msg.step_name);
      if (completedStepIndex > -1 && completedStepIndex < ANALYSIS_STEPS.length - 1) {
        setCurrentStep(completedStepIndex + 1);
      }
    }

    if (msg.message) {
        const iterationMatch = msg.message.match(/Iteration: (\d+)/);
        if (iterationMatch) {
          setIteration(parseInt(iterationMatch[1], 10));
        }

        const articlesMatch = msg.message.match(/Articles found: (\d+)/);
        if (articlesMatch) {
          setArticlesFound(parseInt(articlesMatch[1], 10));
        }
    }
  };

  useEffect(() => {
    if (sessionId) {
      const callbacks = {
        onStatusUpdate: handleStatusUpdate,
        onAnalysisUpdate: (report: AnalysisReport) => {
            setAnalysis(report);
            setIsLoading(false);
        },
        onError: (error: string) => {
            setError(error);
            setIsLoading(false);
        },
        onIsLoading: setIsLoading,
        onSessionId: setSessionId,
      };
      ws.current = connectToWebSocket(sessionId, callbacks);
    }

    return () => {
      ws.current?.close();
    };
  }, [sessionId]);

  const handleAnalyzeTopic = async (topic: string) => {
    if (!topic.trim()) {
      setError("Please enter a topic to analyze.");
      setAnalysis(null);
      return;
    }
    resetState();
    setIsLoading(true);

    const callbacks = {
        onAnalysisUpdate: (report: AnalysisReport) => {
          setAnalysis(report);
          setIsLoading(false);
        },
        onStatusUpdate: handleStatusUpdate,
        onError: (error: string) => {
            setError(error);
            setIsLoading(false);
        },
        onIsLoading: setIsLoading,
        onSessionId: setSessionId,
    };

    await startAnalysis(topic, callbacks);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 text-slate-100 flex flex-col items-center p-4 sm:p-6 md:p-8 selection:bg-sky-500 selection:text-white">
      <Settings />
      <header className="w-full max-w-4xl text-center my-8 md:my-12">
        <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-sky-400 via-cyan-300 to-teal-400">
          {APP_TITLE}
        </h1>
        <p className="text-slate-400 mt-2 text-lg sm:text-xl">{APP_SUBTITLE}</p>
      </header>

      <main className="w-full max-w-4xl bg-slate-800 shadow-2xl rounded-xl p-6 sm:p-8 md:p-10 flex-grow">
        <TopicInput onSubmit={handleAnalyzeTopic} isLoading={isLoading} />

        {isLoading && (
          <ProgressTracker 
            currentStep={currentStep} 
            iteration={iteration} 
            articlesFound={articlesFound} 
          />
        )}

        {error && !isLoading && (
          <div 
            className="mt-6 p-4 bg-red-500/10 border border-red-500/30 text-red-300 rounded-md"
            role="alert"
          >
            <p className="font-semibold">Analysis Failed</p>
            <p>{error}</p>
          </div>
        )}

        {analysis && !isLoading && !error && (
          <div className="mt-8">
            <AnalysisDisplay report={analysis} />
          </div>
        )}

        {!analysis && !isLoading && !error && (
            <div className="mt-10 text-center text-slate-500">
                <p className="text-xl">Enter a topic above to begin your multi-perspective analysis.</p>
                <p className="mt-2 text-sm">Example: "The future of artificial intelligence in healthcare"</p>
            </div>
        )}
      </main>

      <footer className="w-full max-w-4xl text-center py-8 text-slate-500 text-sm">
        <p>&copy; {new Date().getFullYear()} PolyView.</p>
      </footer>
    </div>
  );
};

export default App;
