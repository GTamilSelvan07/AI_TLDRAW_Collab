// src/components/AISidePanel.tsx
import { useState, useEffect } from 'react';
import './AISidePanel.css';

export interface AIResponse {
  text: string;
  shapes: any[];
  id: string;
}

interface AISidePanelProps {
  isOpen: boolean;
  onClose: () => void;
  mode: string;
  onModeChange: (mode: string) => void;
  onSubmitPrompt: (prompt: string, mode: string) => void;
  aiResponse: AIResponse | null;
  isLoading: boolean;
  isConnected: boolean;
  socketError: string | null;
}

export const AISidePanel = ({ 
  isOpen, 
  onClose, 
  mode, 
  onModeChange,
  onSubmitPrompt,
  aiResponse,
  isLoading,
  isConnected,
  socketError
}: AISidePanelProps) => {
  const [prompt, setPrompt] = useState('');
  const [generationMode, setGenerationMode] = useState('text_to_flowchart');
  
  // Clear prompt when response is received
  useEffect(() => {
    if (aiResponse && !isLoading) {
      setPrompt('');
    }
  }, [aiResponse, isLoading]);
  
  if (!isOpen) return null;
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || !isConnected) return;
    
    onSubmitPrompt(prompt, generationMode);
  };
  
  return (
    <div className="ai-side-panel">
      <div className="panel-header">
        <h2>AI Assistant</h2>
        <button className="close-button" onClick={onClose}>×</button>
      </div>
      
      <div className="panel-content">
        <div className="connection-indicator">
          <div className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`}></div>
          <span>{isConnected ? 'Connected to LLM' : 'Disconnected'}</span>
        </div>
        
        {socketError && (
          <div className="error-message">
            {socketError}
          </div>
        )}
        
        <div className="mode-selector">
          <h3>AI Mode</h3>
          <div className="mode-options">
            <label>
              <input
                type="radio"
                name="mode"
                value="manual"
                checked={mode === 'manual'}
                onChange={() => onModeChange('manual')}
              />
              Manual
            </label>
            <label>
              <input
                type="radio"
                name="mode"
                value="semi-automatic"
                checked={mode === 'semi-automatic'}
                onChange={() => onModeChange('semi-automatic')}
              />
              Semi-Automatic
            </label>
            <label>
              <input
                type="radio"
                name="mode"
                value="automatic"
                checked={mode === 'automatic'}
                onChange={() => onModeChange('automatic')}
              />
              Automatic
            </label>
          </div>
        </div>
        
        <div className="generation-type">
          <h3>Generation Type</h3>
          <div className="generation-options">
            <label>
              <input
                type="radio"
                name="generation"
                value="text_to_flowchart"
                checked={generationMode === 'text_to_flowchart'}
                onChange={() => setGenerationMode('text_to_flowchart')}
              />
              Flowchart
            </label>
            <label>
              <input
                type="radio"
                name="generation"
                value="process_diagram"
                checked={generationMode === 'process_diagram'}
                onChange={() => setGenerationMode('process_diagram')}
              />
              Process Diagram
            </label>
            <label>
              <input
                type="radio"
                name="generation"
                value="mind_map"
                checked={generationMode === 'mind_map'}
                onChange={() => setGenerationMode('mind_map')}
              />
              Mind Map
            </label>
          </div>
        </div>
        
        <form onSubmit={handleSubmit} className="ai-prompt-form">
          <h3>Ask AI</h3>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder={`Example: "Create a flowchart for user registration process"`}
            disabled={isLoading || !isConnected}
          />
          <button 
            type="submit" 
            disabled={isLoading || !isConnected || !prompt.trim()}
            className="generate-button"
          >
            {isLoading ? 'Generating...' : 'Generate'}
          </button>
        </form>
        
        {(aiResponse?.text || isLoading) && (
          <div className="ai-output">
            <h3>AI Response</h3>
            {isLoading ? (
              <div className="loading">
                <div className="spinner"></div>
                <p>AI is generating your diagram...</p>
              </div>
            ) : (
              <div className="output-content">
                {aiResponse?.text}
                {aiResponse?.shapes && (
                  <div className="shape-info">
                    <p>✓ {aiResponse.shapes.length} shapes generated</p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};