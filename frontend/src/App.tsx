import { useState, useRef, useEffect } from 'react';
import './App.css';
import PerspectiveCard from './components/PerspectiveCard';
import SummaryView from './components/SummaryView';
import FollowUpInput from './components/FollowUpInput';

interface AnalysisMessage {
  type: 'status' | 'partial_result' | 'final_result' | 'error' | 'end_of_stream';
  message?: string;
  data?: any;
}

function App() {
  const [topic, setTopic] = useState<string>('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<string[]>([]);
  const [finalResult, setFinalResult] = useState<any>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const ws = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const API_BASE_URL = 'http://localhost:8000/api/v1';
  const WS_BASE_URL = 'ws://localhost:8000/api/v1/ws';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (sessionId) {
      ws.current = new WebSocket(`${WS_BASE_URL}/${sessionId}`);

      ws.current.onopen = () => {
        setMessages((prev) => [...prev, 'WebSocket connected. Waiting for analysis updates...']);
      };

      ws.current.onmessage = (event) => {
        const msg: AnalysisMessage = JSON.parse(event.data);
        console.log('Received message:', msg);

        if (msg.type === 'status') {
          setMessages((prev) => [...prev, `Status: ${msg.message}`]);
        } else if (msg.type === 'partial_result') {
          setMessages((prev) => [...prev, `Partial Result: ${JSON.stringify(msg.data)}`]);
        } else if (msg.type === 'final_result') {
          setMessages((prev) => [...prev, 'Analysis complete!']);
          console.log('Final Result:', msg.data);
          setFinalResult(msg.data);
          setIsLoading(false);
        } else if (msg.type === 'error') {
          setMessages((prev) => [...prev, `Error: ${msg.message}`]);
          setIsLoading(false);
        } else if (msg.type === 'end_of_stream') {
          setMessages((prev) => [...prev, 'End of analysis stream.']);
          ws.current?.close();
        }
      };

      ws.current.onclose = () => {
        setMessages((prev) => [...prev, 'WebSocket disconnected.']);
        setIsLoading(false);
      };

      ws.current.onerror = (error) => {
        setMessages((prev) => [...prev, `WebSocket error: ${error}`]);
        setIsLoading(false);
      };
    }

    return () => {
      ws.current?.close();
    };
  }, [sessionId]);

  const startAnalysis = async () => {
    if (!topic.trim()) {
      alert('Please enter a topic.');
      return;
    }

    setMessages([]);
    setFinalResult(null);
    setSessionId(null);
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ topic }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setSessionId(data.session_id);
      setMessages((prev) => [...prev, `Analysis started with Session ID: ${data.session_id}`]);
    } catch (error) {
      setMessages((prev) => [...prev, `Failed to start analysis: ${error}`]);
      setIsLoading(false);
    }
  };

  const loadMockData = async () => {
    setIsLoading(true);
    setMessages(['Loading mock data...']);
    try {
      const response = await fetch('/src/mock-data.json');
      const data = await response.json();
      setFinalResult(data);
      setMessages(['Mock data loaded successfully!']);
    } catch (error) {
      setMessages([`Failed to load mock data: ${error}`]);
    }
    setIsLoading(false);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>PolyView Analysis</h1>
      </header>
      <main className="App-main">
        <div className="input-section">
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Enter topic for analysis (e.g., 'Climate Change')"
            disabled={isLoading}
          />
          <button onClick={startAnalysis} disabled={isLoading}>
            {isLoading ? 'Analyzing...' : 'Start Analysis'}
          </button>
          <button onClick={loadMockData} disabled={isLoading} className="mock-data-btn">
            Load Mock Data
          </button>
        </div>

        <div className="messages-section">
          <h2>Live Updates</h2>
          <div className="messages-box">
            {messages.length === 0 && <p>No updates yet. Start an analysis!</p>}
            {messages.map((msg, index) => (
              <p key={index}>{msg}</p>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {finalResult && (
          <div className="results-section">
            <SummaryView topic={finalResult.topic} summary={finalResult.summary} />
            <div className="perspectives-grid">
              {finalResult.perspectives && finalResult.perspectives.length > 0 ? (
                finalResult.perspectives.map((p: any, index: number) => (
                  <PerspectiveCard key={index} perspective={p} />
                ))
              ) : (
                <p>No perspectives found.</p>
              )}
            </div>
            <FollowUpInput />
          </div>
        )}
      </main>
    </div>
  );
}

export default App;