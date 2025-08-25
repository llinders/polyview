
import React, { useState, useEffect, useRef } from 'react';
import { TopicInput } from './components/TopicInput';
import { AnalysisDisplay } from './components/AnalysisDisplay';
import { Spinner } from './components/Spinner';
import Settings from './components/Settings';
import type { AnalysisReport } from './types';
import { APP_TITLE, APP_SUBTITLE } from './constants';
import { startAnalysis, connectToWebSocket } from './services/polyViewAgentService';

const App: React.FC = () => {
  const [analysis, setAnalysis] = useState<AnalysisReport | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<string[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (sessionId) {
      const callbacks = {
        onStatusUpdate: (message: string) => setMessages(prev => [...prev, message]),
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
    setMessages([]);
    setError(null);
    setAnalysis(null);

    const callbacks = {
        onAnalysisUpdate: setAnalysis,
        onStatusUpdate: (message: string) => setMessages(prev => [...prev, message]),
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
          <div className="flex flex-col items-center justify-center mt-10 text-slate-400">
            <Spinner />
            <p className="mt-4 text-lg">Analyzing perspectives... this may take a moment.</p>
            <div className="mt-4 text-sm text-slate-500 w-full text-left">
                {messages.map((msg, index) => (
                    <p key={index}>{msg}</p>
                ))}
            </div>
          </div>
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
