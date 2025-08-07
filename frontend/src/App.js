import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import './App.css';
import Dashboard from './components/Dashboard';
import LicenseBanner from './components/LicenseBanner';

function App() {
  return (
    <div className="App">
      <Toaster 
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            duration: 3000,
            theme: {
              primary: '#4ade80',
              secondary: '#000',
            },
          },
          error: {
            duration: 5000,
            theme: {
              primary: '#ef4444',
              secondary: '#000',
            },
          },
        }}
      />
      <Router>
        <Routes>
          <Route path="/" element={<Dashboard />} />
        </Routes>
      </Router>
    </div>
  );
}

export default App;