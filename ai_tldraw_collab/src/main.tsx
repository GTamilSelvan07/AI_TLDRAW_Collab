// src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// Add global error handler for debugging
window.addEventListener('error', (event) => {
  console.error('Global error caught:', event.error);
});

// Prevent common unhandled promise rejection issues
window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason);
  event.preventDefault();
});

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <App />
);