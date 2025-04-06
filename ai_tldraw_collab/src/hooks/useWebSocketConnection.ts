// src/hooks/useWebSocketConnection.ts
import { useState, useEffect, useCallback, useRef } from 'react';

export interface AIResponse {
  text: string;
  shapes: any[];
  id: string;
  type: string;
  title?: string;
  description?: string;
}

export function useWebSocketConnection(url: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [aiResponse, setAiResponse] = useState<AIResponse | null>(null);
  const [socketError, setSocketError] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);

  // Setup WebSocket connection
  useEffect(() => {
    let reconnectTimeout: NodeJS.Timeout;
    
    const connectWebSocket = () => {
      try {
        console.log(`Connecting to WebSocket at ${url}...`);
        const socket = new WebSocket(url);
        socketRef.current = socket;
        
        socket.onopen = () => {
          console.log('WebSocket connection established');
          setIsConnected(true);
          setSocketError(null);
        };
    
        socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('Received data:', data);
            
            if (data.type === 'processing') {
              setIsProcessing(true);
            } else if (data.type === 'response') {
              // Extract title and description from the response if available
              let responseText = data.text || '';
              const responseTitle = data.title || '';
              const responseDescription = data.description || '';
              
              // Format the response text if we have title/description
              if (responseTitle || responseDescription) {
                responseText = `${responseTitle ? `Title: ${responseTitle}\n\n` : ''}${
                  responseDescription ? `Description: ${responseDescription}\n\n` : ''
                }${responseText}`;
              }
              
              setAiResponse({
                ...data,
                text: responseText
              });
              setIsProcessing(false);
            } else if (data.type === 'error') {
              setSocketError(data.message);
              setIsProcessing(false);
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
            setSocketError('Received invalid data from backend');
          }
        };
    
        socket.onclose = (event) => {
          console.log(`WebSocket connection closed: ${event.reason}`);
          setIsConnected(false);
          
          // Attempt to reconnect after 3 seconds
          reconnectTimeout = setTimeout(connectWebSocket, 3000);
        };
    
        socket.onerror = (error) => {
          console.error('WebSocket error:', error);
          setSocketError('Failed to connect to backend server');
          setIsConnected(false);
        };
      } catch (error) {
        console.error('Error setting up WebSocket:', error);
        setSocketError('Failed to setup WebSocket connection');
        
        // Attempt to reconnect after 3 seconds
        reconnectTimeout = setTimeout(connectWebSocket, 3000);
      }
    };
    
    connectWebSocket();

    // Clean up function
    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
      clearTimeout(reconnectTimeout);
    };
  }, [url]);

  // Function to send a prompt to the backend
  const sendPrompt = useCallback((prompt: string, mode: string = 'text_to_flowchart') => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      setIsProcessing(true);
      socketRef.current.send(JSON.stringify({
        prompt,
        mode
      }));
    } else {
      setSocketError('WebSocket is not connected');
    }
  }, []);

  // Function to reset the AI response
  const resetResponse = useCallback(() => {
    setAiResponse(null);
    setIsProcessing(false);
  }, []);

  return {
    isConnected,
    isProcessing,
    aiResponse,
    sendPrompt,
    socketError,
    resetResponse
  };
}