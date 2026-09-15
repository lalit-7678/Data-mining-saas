import React, { useState } from 'react';
import Header from './components/layouts/Header';
import Dashboard from './pages/Dashboard';
import DataQuality from './pages/DataQuality';
import Cleaning from './pages/Cleaning';
import Analytics from './pages/Analytics';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  // Callback when a file is successfully uploaded on Page 1
  const handleUploadSuccess = () => {
    setActiveTab('quality');
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 transition-colors duration-200 flex flex-col">
      {/* Top Shared Header */}
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Container */}
      <main className="flex-1 container mx-auto px-4 py-8">
        {activeTab === 'dashboard' && (
          <Dashboard onUploadSuccess={handleUploadSuccess} />
        )}
        {activeTab === 'quality' && <DataQuality />}
        {activeTab === 'cleaning' && <Cleaning />}
        {activeTab === 'analytics' && <Analytics />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-800 py-4 text-center text-xs theme-muted">
        Data Mining & Analytics Platform — FastAPI + Vanilla JS/React Engine
      </footer>
    </div>
  );
}