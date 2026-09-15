import React, { useState, useEffect } from 'react';
import { ApiService } from '../services/api';

export default function Cleaning() {
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState(null);
  const [cleaningPlan, setCleaningPlan] = useState(null);
  const [cleaningResult, setCleaningResult] = useState(null);

  const datasetId = ApiService.getDatasetId();

  useEffect(() => {
    if (!datasetId) {
      setLoading(false);
      return;
    }

    const fetchPlan = async () => {
      try {
        setLoading(true);
        // Load cached plan from upload response first
        const cachedAnalysis = localStorage.getItem(`analysis_${datasetId}`);
        if (cachedAnalysis) {
          const parsed = JSON.parse(cachedAnalysis);
          if (parsed.cleaning_plan) {
            setCleaningPlan(parsed.cleaning_plan);
            setLoading(false);
            return;
          }
        }

        // Fallback to overview backend endpoint
        const overview = await ApiService.getEDAOverview(datasetId);
        setCleaningPlan(overview.cleaning_plan || { items: [] });
      } catch (err) {
        setError(err.message || 'Failed to load cleaning plan.');
      } finally {
        setLoading(false);
      }
    };

    fetchPlan();
  }, [datasetId]);

  // Toggle item selection
  const handleToggleItem = (index) => {
    if (!cleaningPlan) return;
    const updatedItems = [...cleaningPlan.items];
    updatedItems[index].enabled = !updatedItems[index].enabled;
    setCleaningPlan({ ...cleaningPlan, items: updatedItems });
  };

  // Execute cleaning pipeline with approved_item_ids schema
  const handleExecuteCleaning = async () => {
    if (!datasetId || !cleaningPlan) return;

    try {
      setExecuting(true);
      setError(null);

      // Extract item IDs/column names for approved_item_ids
      const approvedIds = (cleaningPlan.items || [])
        .filter((item) => item.enabled !== false)
        .map((item, idx) => String(item.id || item.item_id || item.column || idx));

      // Construct payload required by FastAPI CleaningRequest schema
      const payload = {
        dataset_id: datasetId,
        approved_item_ids: approvedIds,
      };

      const response = await fetch('http://localhost:8000/api/v1/data/clean', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const resData = await response.json();

      if (!response.ok) {
        const errorMsg = Array.isArray(resData.detail)
          ? resData.detail.map((err) => `${err.loc?.slice(-1)}: ${err.msg}`).join(' | ')
          : resData.detail || 'Failed to clean dataset';
        throw new Error(errorMsg);
      }

      setCleaningResult(resData);
    } catch (err) {
      setError(err.message);
    } finally {
      setExecuting(false);
    }
  };

  if (!datasetId) {
    return (
      <div className="theme-card p-12 text-center rounded-xl border shadow-sm max-w-4xl mx-auto">
        <h3 className="text-lg font-bold mb-1">No Active Dataset Found</h3>
        <p className="text-sm theme-muted">
          Please upload a CSV dataset on Page 1 (Dashboard / Upload) first.
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto p-12 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent mb-3"></div>
        <p className="text-sm font-semibold theme-muted">Generating interactive cleaning recipe...</p>
      </div>
    );
  }

  const items = cleaningPlan?.items || [];

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header Banner */}
      <div className="theme-card p-6 rounded-xl border shadow-sm flex flex-wrap justify-between items-center gap-4">
        <div>
          <h2 className="text-xl font-bold mb-1">Interactive Data Cleaning Recipe</h2>
          <p className="text-xs theme-muted">
            Review, enable, or disable automated remediation steps before executing the pipeline.
          </p>
        </div>
        <button
          onClick={handleExecuteCleaning}
          disabled={executing || items.length === 0}
          className="px-5 py-2.5 bg-blue-600 text-white text-xs font-bold rounded-lg hover:bg-blue-700 disabled:opacity-50 transition flex items-center space-x-2 cursor-pointer"
        >
          {executing ? (
            <>
              <span className="inline-block animate-spin rounded-full h-3 w-3 border-2 border-white border-t-transparent"></span>
              <span>Applying Pipeline...</span>
            </>
          ) : (
            <span>⚡ Apply & Clean Data</span>
          )}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-xl text-xs font-semibold">
          {error}
        </div>
      )}

      {/* Output / Downloads */}
      {cleaningResult && (
        <div className="theme-card p-6 rounded-xl border border-emerald-500/50 shadow-sm space-y-4">
          <div className="flex items-center space-x-3 text-emerald-600 dark:text-emerald-400">
            <span className="text-xl">✅</span>
            <h3 className="text-base font-bold">Data Cleaning Successful</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div className="p-3 border rounded-lg">
              <span className="theme-muted block">Status</span>
              <strong className="text-sm font-bold text-emerald-600 dark:text-emerald-400">
                {cleaningResult.status || 'SUCCESS'}
              </strong>
            </div>
            <div className="p-3 border rounded-lg">
              <span className="theme-muted block">Cleaned Dataset ID</span>
              <strong className="text-xs font-mono">{cleaningResult.cleaned_dataset_id || datasetId}</strong>
            </div>
            <div className="p-3 border rounded-lg flex flex-col justify-center space-y-2">
              <span className="theme-muted font-bold block">Download Options</span>
              <div className="flex flex-wrap gap-2">
                <a
                  href={ApiService.getStaticUrl(cleaningResult.download_url)}
                  download
                  className="px-3 py-1.5 bg-emerald-600 text-white rounded font-bold hover:bg-emerald-700 transition"
                >
                  Download CSV
                </a>
                <a
                  href={ApiService.getStaticUrl(cleaningResult.download_url?.replace('.csv', '.xlsx'))}
                  download
                  className="px-3 py-1.5 bg-blue-600 text-white rounded font-bold hover:bg-blue-700 transition"
                >
                  Download Excel (.xlsx)
                </a>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Cleaning Plan Actions Table */}
      <div className="theme-card rounded-xl border shadow-sm overflow-hidden">
        <div className="p-5 border-b font-bold text-base flex justify-between items-center">
          <span>Proposed Remediation Actions</span>
          <span className="text-xs theme-muted font-normal">{items.length} actions queued</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b uppercase font-semibold theme-muted bg-gray-50 dark:bg-slate-800">
              <tr>
                <th className="p-3.5 text-center">Enable</th>
                <th className="p-3.5">Severity</th>
                <th className="p-3.5">Target Column</th>
                <th className="p-3.5">Issue Detected</th>
                <th className="p-3.5">Recommended Action</th>
                <th className="p-3.5">Method</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-slate-700">
              {items.length === 0 ? (
                <tr>
                  <td colSpan="6" className="p-6 text-center theme-muted">
                    No cleaning actions required. Your dataset appears fully clean!
                  </td>
                </tr>
              ) : (
                items.map((item, idx) => (
                  <tr key={idx} className="hover:bg-gray-50 dark:hover:bg-slate-800/50 transition">
                    <td className="p-3.5 text-center">
                      <input
                        type="checkbox"
                        checked={item.enabled !== false}
                        onChange={() => handleToggleItem(idx)}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500 cursor-pointer"
                      />
                    </td>
                    <td className="p-3.5">
                      <span
                        className={
                          item.severity?.toUpperCase() === 'HIGH'
                            ? 'severity-high px-2 py-0.5 rounded text-xs font-bold'
                            : item.severity?.toUpperCase() === 'MEDIUM'
                            ? 'severity-medium px-2 py-0.5 rounded text-xs font-bold'
                            : 'severity-low px-2 py-0.5 rounded text-xs font-bold'
                        }
                      >
                        {item.severity || 'LOW'}
                      </span>
                    </td>
                    <td className="p-3.5 font-bold font-mono">{item.column}</td>
                    <td className="p-3.5 text-slate-700 dark:text-slate-300 font-medium">{item.issue_type}</td>
                    <td className="p-3.5 text-blue-600 dark:text-blue-400 font-semibold">
                      {item.recommended_action || item.action}
                    </td>
                    <td className="p-3.5 font-mono theme-muted">{item.method || 'Standard Imputation'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}