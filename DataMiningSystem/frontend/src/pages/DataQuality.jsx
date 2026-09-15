import React, { useState, useEffect } from 'react';
import { ApiService } from '../services/api';

export default function DataQuality() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [semanticData, setSemanticData] = useState([]);
  const [cleaningItems, setCleaningItems] = useState([]);
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const datasetId = ApiService.getDatasetId();
    if (!datasetId) {
      setLoading(false);
      return;
    }

    const fetchData = async () => {
      try {
        setLoading(true);
        // Pehle localStorage se check karo agar upload data cached hai
        const cachedAnalysis = localStorage.getItem(`analysis_${datasetId}`);
        
        if (cachedAnalysis) {
          const parsed = JSON.parse(cachedAnalysis);
          setSemanticData(parsed.semantic_analysis || []);
          setCleaningItems(parsed.cleaning_plan?.items || []);
        } else {
          // Fallback to overview call
          const overviewRes = await ApiService.getEDAOverview(datasetId);
          setSemanticData(overviewRes.semantic_analysis || []);
          setCleaningItems(overviewRes.cleaning_plan?.items || []);
        }
      } catch (err) {
        setError(err.message || 'Failed to load data quality profile.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const datasetId = ApiService.getDatasetId();

  if (!datasetId) {
    return (
      <div className="theme-card p-12 text-center rounded-xl border shadow-sm max-w-4xl mx-auto">
        <h3 className="text-lg font-bold mb-1">No Active Dataset Found</h3>
        <p className="text-sm theme-muted">Please go to Page 1 (Dashboard / Upload) and upload a CSV dataset first.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto p-12 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent mb-3"></div>
        <p className="text-sm font-semibold theme-muted">Profiling dataset & analyzing semantic types...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto p-6 bg-red-100 text-red-700 rounded-xl text-sm font-semibold">
        {error}
      </div>
    );
  }

  const filteredIssues = cleaningItems.filter((item) => {
    const matchesSeverity =
      severityFilter === 'ALL' || item.severity?.toUpperCase() === severityFilter;
    const matchesSearch =
      item.column?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.issue_type?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesSeverity && matchesSearch;
  });

  const getSeverityBadgeClass = (severity) => {
    switch (severity?.toUpperCase()) {
      case 'HIGH': return 'severity-high px-2.5 py-1 rounded-full text-xs font-bold';
      case 'MEDIUM': return 'severity-medium px-2.5 py-1 rounded-full text-xs font-bold';
      case 'LOW': return 'severity-low px-2.5 py-1 rounded-full text-xs font-bold';
      default: return 'bg-gray-200 dark:bg-gray-700 px-2.5 py-1 rounded-full text-xs font-bold';
    }
  };

  const getSemanticBadgeClass = (type) => {
    switch (type?.toUpperCase()) {
      case 'NUMERICAL': return 'badge-numerical px-2 py-0.5 rounded text-xs font-semibold';
      case 'CATEGORICAL': return 'badge-categorical px-2 py-0.5 rounded text-xs font-semibold';
      case 'IDENTIFIER': return 'badge-identifier px-2 py-0.5 rounded text-xs font-semibold';
      case 'DATETIME': return 'badge-datetime px-2 py-0.5 rounded text-xs font-semibold';
      default: return 'bg-gray-100 text-gray-800 px-2 py-0.5 rounded text-xs font-semibold';
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="theme-card p-6 rounded-xl border shadow-sm">
        <h2 className="text-xl font-bold mb-1">Data Understanding & Quality Diagnostics</h2>
        <p className="text-xs theme-muted">
          Review automatically detected semantic classifications, column roles, and granular quality flags directly from the backend.
        </p>
      </div>

      <div className="theme-card rounded-xl border shadow-sm overflow-hidden">
        <div className="p-5 border-b font-bold text-base flex justify-between items-center">
          <span>Column Understanding Matrix</span>
          <span className="text-xs theme-muted font-normal">{semanticData.length} total columns</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b uppercase font-semibold theme-muted bg-gray-50 dark:bg-slate-800">
              <tr>
                <th className="p-3.5">Column Name</th>
                <th className="p-3.5">Physical Type</th>
                <th className="p-3.5">Semantic Type</th>
                <th className="p-3.5">Role</th>
                <th className="p-3.5">Unique Values</th>
                <th className="p-3.5">Missing Values</th>
                <th className="p-3.5">Confidence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-slate-700">
              {semanticData.length === 0 ? (
                <tr>
                  <td colSpan="7" className="p-6 text-center theme-muted">No column metadata available.</td>
                </tr>
              ) : (
                semanticData.map((col, idx) => (
                  <tr key={idx} className="hover:bg-gray-50 dark:hover:bg-slate-800/50 transition">
                    <td className="p-3.5 font-bold font-mono">{col.column_name || col.name}</td>
                    <td className="p-3.5 theme-muted font-mono">{col.physical_type || 'string'}</td>
                    <td className="p-3.5"><span className={getSemanticBadgeClass(col.semantic_type)}>{col.semantic_type || 'UNKNOWN'}</span></td>
                    <td className="p-3.5 font-medium">{col.role || 'Feature'}</td>
                    <td className="p-3.5">{col.unique_count ?? 'N/A'}</td>
                    <td className="p-3.5 text-amber-600 font-semibold">{col.missing_count ?? 0}</td>
                    <td className="p-3.5 font-mono">{col.confidence ? `${(col.confidence * 100).toFixed(0)}%` : '100%'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="theme-card p-6 rounded-xl border shadow-sm space-y-4">
        <div className="flex flex-wrap justify-between items-center gap-4">
          <div>
            <h3 className="font-bold text-base">Detected Quality Issues</h3>
            <p className="text-xs theme-muted">Audit findings requiring review or cleaning actions</p>
          </div>
          <div className="flex items-center space-x-3">
            <input
              type="text"
              placeholder="Search column or issue..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="px-3 py-1.5 border rounded-lg text-xs theme-card focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="px-3 py-1.5 border rounded-lg text-xs theme-card focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="ALL">All Severities</option>
              <option value="HIGH">High Severity</option>
              <option value="MEDIUM">Medium Severity</option>
              <option value="LOW">Low Severity</option>
              <option value="REVIEW REQUIRED">Review Required</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b uppercase font-semibold theme-muted bg-gray-50 dark:bg-slate-800">
              <tr>
                <th className="p-3.5">Severity</th>
                <th className="p-3.5">Column</th>
                <th className="p-3.5">Issue Type</th>
                <th className="p-3.5">Recommended Action</th>
                <th className="p-3.5">Method</th>
                <th className="p-3.5">Reason</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-slate-700">
              {filteredIssues.length === 0 ? (
                <tr>
                  <td colSpan="6" className="p-6 text-center theme-muted">No matching quality issues detected.</td>
                </tr>
              ) : (
                filteredIssues.map((issue, idx) => (
                  <tr key={idx} className="hover:bg-gray-50 dark:hover:bg-slate-800/50 transition">
                    <td className="p-3.5"><span className={getSeverityBadgeClass(issue.severity)}>{issue.severity || 'LOW'}</span></td>
                    <td className="p-3.5 font-bold font-mono">{issue.column}</td>
                    <td className="p-3.5 font-semibold text-slate-700 dark:text-slate-300">{issue.issue_type}</td>
                    <td className="p-3.5 text-blue-600 dark:text-blue-400 font-medium">{issue.recommended_action || issue.action}</td>
                    <td className="p-3.5 font-mono theme-muted">{issue.method || 'Standard'}</td>
                    <td className="p-3.5 max-w-xs truncate theme-muted" title={issue.reason}>{issue.reason || 'N/A'}</td>
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