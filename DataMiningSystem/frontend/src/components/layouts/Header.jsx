import React, { useState, useEffect } from 'react';
import { AppTheme } from '../../utils/theme';

export default function Header({ activeTab, setActiveTab }) {
  const [theme, setTheme] = useState(AppTheme.getTheme());

  useEffect(() => {
    AppTheme.init();
  }, []);

  const handleThemeToggle = () => {
    const nextTheme = AppTheme.toggle();
    setTheme(nextTheme);
  };

  const navItems = [
    { id: 'dashboard', label: '1. Dashboard / Upload' },
    { id: 'quality', label: '2. Data Quality' },
    { id: 'cleaning', label: '3. Cleaning' },
    { id: 'analytics', label: '4. EDA & Insights' },
  ];

  return (
    <header className="theme-card border-b px-6 py-4 flex flex-wrap justify-between items-center shadow-sm">
      <div className="flex items-center space-x-3">
        <div className="w-9 h-9 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-xl shadow-md">
          D
        </div>
        <div>
          <h1 className="font-bold text-lg leading-tight">Data Mining System</h1>
          <p className="text-xs theme-muted">Intelligent Profiling & Diagnostics Engine</p>
        </div>
      </div>

      <nav className="flex items-center space-x-2 sm:space-x-4 my-2 sm:my-0">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            className={`px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
              activeTab === item.id
                ? 'bg-blue-600 text-white shadow-sm'
                : 'hover:bg-gray-100 dark:hover:bg-slate-800 theme-muted'
            }`}
          >
            {item.label}
          </button>
        ))}
      </nav>

      <button
        onClick={handleThemeToggle}
        className="px-3.5 py-1.5 rounded-lg border theme-card text-xs font-semibold hover:opacity-80 transition flex items-center space-x-2"
      >
        <span>{theme === 'dark' ? '☀️ Light Mode' : '🌙 Dark Mode'}</span>
      </button>
    </header>
  );
}