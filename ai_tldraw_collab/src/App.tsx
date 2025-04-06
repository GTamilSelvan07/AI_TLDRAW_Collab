// src/App.tsx
import { useState, useEffect } from 'react';
import { CollaborativeCanvas } from './components/CollaborativeCanvas';
import { AISidePanel } from './components/AISidePanel';
import { useWebSocketConnection } from './hooks/useWebSocketConnection';
import './App.css';

function App() {
  const [isSidePanelOpen, setIsSidePanelOpen] = useState(false);
  const [currentMode, setCurrentMode] = useState('manual');
  const { 
    isConnected, 
    aiResponse, 
    isProcessing, 
    sendPrompt,
    socketError,
    resetResponse 
  } = useWebSocketConnection('ws://localhost:8000/ws');
  
  useEffect(() => {
    // When AI panel is opened, reset previous response
    if (isSidePanelOpen) {
      resetResponse();
    }
  }, [isSidePanelOpen, resetResponse]);
  
  return (
    <div className="app">
      <CollaborativeCanvas 
        isSidePanelOpen={isSidePanelOpen}
        aiData={aiResponse?.shapes}
      />
      
      <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
        {isConnected ? 'Backend Connected' : 'Backend Disconnected'}
      </div>
      
      <button 
        className="ai-toggle-button" 
        onClick={() => setIsSidePanelOpen(!isSidePanelOpen)}
        title="AI Assistant"
      >
        {isSidePanelOpen ? 'Hide AI' : 'Show AI'}
      </button>
      
      <AISidePanel 
        isOpen={isSidePanelOpen} 
        onClose={() => setIsSidePanelOpen(false)}
        mode={currentMode}
        onModeChange={setCurrentMode}
        onSubmitPrompt={sendPrompt}
        aiResponse={aiResponse}
        isLoading={isProcessing}
        isConnected={isConnected}
        socketError={socketError}
      />
    </div>
  );
}

export default App;