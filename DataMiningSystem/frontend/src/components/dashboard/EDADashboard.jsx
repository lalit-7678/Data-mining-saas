import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, ScatterChart, Scatter } from 'recharts';

export default function EDADashboard({ datasetId }) {
  const [overview, setOverview] = useState(null);
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!datasetId) return;

    setLoading(true);
    setError(null);

    // Fetch Overview and Insights concurrently
    Promise.all([
      fetch(`http://127.0.0.1:8000/api/v1/eda/overview/${datasetId}`).then(res => res.json()),
      fetch(`http://127.0.0.1:8000/api/v1/eda/insights/${datasetId}`).then(res => res.json())
    ])
      .then(([overviewRes, insightsRes]) => {
        if (overviewRes.status === 'SUCCESS') setOverview(overviewRes.overview);
        if (insightsRes.status === 'SUCCESS') setInsights(insightsRes.insights);
        setLoading(false);
      })
      .catch(err => {
        setError('Failed to load EDA data. Please ensure the backend is running on http://127.0.0.1:8000');
        setLoading(false);
      });
  }, [datasetId]);

  if (loading) return <div className="p-8 text-center text-slate-400">Loading Exploratory Data Analysis...</div>;
  if (error) return <div className="p-4 bg-red-900/40 border border-red-500 rounded-lg text-red-200">{error}</div>;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Overview Stat Cards */}
      {overview && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-800 p-4 rounded-xl border border-slate-700">
            <span className="text-xs text-slate-400 uppercase font-semibold">Total Rows</span>
            <p className="text-2xl font-bold text-white mt-1">{overview.total_rows.toLocaleString()}</p>
          </div>
          <div className="bg-slate-800 p-4 rounded-xl border border-slate-700">
            <span className="text-xs text-slate-400 uppercase font-semibold">Total Columns</span>
            <p className="text-2xl font-bold text-white mt-1">{overview.total_columns}</p>
          </div>
          <div className="bg-slate-800 p-4 rounded-xl border border-slate-700">
            <span className="text-xs text-slate-400 uppercase font-semibold">Missing Cells</span>
            <p className="text-2xl font-bold text-amber-400 mt-1">{overview.missing_pct}%</p>
          </div>
          <div className="bg-slate-800 p-4 rounded-xl border border-slate-700">
            <span className="text-xs text-slate-400 uppercase font-semibold">Quality Score</span>
            <p className="text-2xl font-bold text-emerald-400 mt-1">{overview.quality_score} / 100</p>
          </div>
        </div>
      )}

      {/* Insights Section */}
      {insights && insights.insights && (
        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
          <h2 className="text-lg font-bold text-white mb-4">Automated Key Insights</h2>
          <div className="space-y-3">
            {insights.insights.map((item, idx) => (
              <div key={idx} className="p-4 bg-slate-900/60 rounded-lg border border-slate-700/50">
                <div className="flex justify-between items-center mb-1">
                  <h3 className="font-semibold text-indigo-300">{item.title}</h3>
                  <span className={`px-2 py-0.5 text-xs rounded font-medium ${item.severity === 'HIGH' ? 'bg-red-900/60 text-red-300' : 'bg-amber-900/60 text-amber-300'}`}>
                    {item.severity}
                  </span>
                </div>
                <p className="text-sm text-slate-300 mt-1">{item.interpretation}</p>
                <div className="text-xs text-slate-500 mt-2">Evidence: {item.evidence}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}