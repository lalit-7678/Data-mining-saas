import React, { useState, useEffect } from 'react';
import { ApiService } from '../services/api';

export default function Analytics() {
  const [loading, setLoading] = useState(true);
  const [pdfGenerating, setPdfGenerating] = useState(false);
  const [error, setError] = useState(null);
  const [overview, setOverview] = useState(null);
  const [insights, setInsights] = useState([]);
  const [pdfUrl, setPdfUrl] = useState(null);

  useEffect(() => {
    const datasetId = ApiService.getCleanedDatasetId() || ApiService.getDatasetId();
    if (!datasetId) {
      setLoading(false);
      return;
    }

    const fetchAnalytics = async () => {
      try {
        setLoading(true);
        const [overviewRes, insightsRes] = await Promise.all([
          ApiService.getEDAOverview(datasetId),
          ApiService.getEDAInsights(datasetId),
        ]);

        setOverview(overviewRes.overview || {});
        setInsights(insightsRes.insights || []);
      } catch (err) {
        setError(err.message || 'Failed to load exploratory analysis.');
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  const activeDatasetId = ApiService.getCleanedDatasetId() || ApiService.getDatasetId();

  const handleExportPDF = async () => {
    if (!activeDatasetId) return;
    setPdfGenerating(true);
    setError(null);

    try {
      const res = await ApiService.exportPDF(activeDatasetId);
      setPdfUrl(res.download_url);
    } catch (err) {
      setError(err.message || 'Failed to export PDF report.');
    } finally {
      setPdfGenerating(false);
    }
  };

  if (!activeDatasetId) {
    return (
      <div className="theme-card p-12 text-center rounded-xl border shadow-sm max-w-4xl mx-auto">
        <h3 className="text-lg font-bold mb-1">No Active Dataset</h3>
        <p className="text-sm theme-muted">Please upload a dataset on Page 1 first.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto p-12 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent mb-3"></div>
        <p className="text-sm font-semibold theme-muted">Generating EDA charts & compiling evidence-based insights...</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Top Banner & PDF Export Trigger */}
      <div className="theme-card p-6 rounded-xl border shadow-sm flex flex-wrap justify-between items-center gap-4">
        <div>
          <h2 className="text-xl font-bold mb-1">Exploratory Data Analysis & Evidence Insights</h2>
          <p className="text-xs theme-muted">
            Viewing analytical distributions and automated insights for dataset: <span className="font-mono text-blue-600">{activeDatasetId}</span>
          </p>
        </div>
        <button
          onClick={handleExportPDF}
          disabled={pdfGenerating}
          className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-md transition disabled:opacity-50 flex items-center space-x-2"
        >
          <span>{pdfGenerating ? 'Compiling PDF Report...' : '📄 Export PDF Executive Report'}</span>
        </button>
      </div>

      {pdfUrl && (
        <div className="p-4 theme-card border border-blue-500/50 rounded-xl text-xs flex justify-between items-center">
          <span className="font-semibold text-blue-600">Your ReportLab Executive PDF Report is ready!</span>
          <a
            href={ApiService.getStaticUrl(pdfUrl)}
            download
            className="px-4 py-1.5 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700 transition"
          >
            Download PDF
          </a>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-100 text-red-700 rounded-xl text-xs font-semibold">
          {error}
        </div>
      )}

      {/* Evidence-Based Insights Grid */}
      <div className="space-y-4">
        <h3 className="font-bold text-base">Automated Statistical Findings</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {insights.length === 0 ? (
            <div className="col-span-2 theme-card p-6 text-center text-xs theme-muted rounded-xl border">
              No statistical findings generated for this dataset.
            </div>
          ) : (
            insights.map((insight, idx) => (
              <div key={idx} className="theme-card p-5 rounded-xl border shadow-sm space-y-2">
                <div className="flex justify-between items-start">
                  <h4 className="text-sm font-bold text-blue-600">{insight.title || `Finding #${idx + 1}`}</h4>
                  <span className="px-2 py-0.5 rounded text-xs font-mono bg-blue-100 text-blue-800">
                    {insight.severity || 'STATISTICAL'}
                  </span>
                </div>
                <p className="text-xs font-medium">{insight.interpretation || insight.description}</p>
                {insight.evidence && (
                  <div className="p-2.5 bg-gray-50 dark:bg-slate-800 rounded-lg text-xs font-mono theme-muted">
                    <strong>Evidence:</strong> {insight.evidence}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Backend Generated EDA Charts */}
      <div className="space-y-4">
        <h3 className="font-bold text-base">Analytical Visualizations</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {(!overview?.charts || overview.charts.length === 0) ? (
            <div className="col-span-2 theme-card p-8 text-center text-xs theme-muted rounded-xl border">
              No chart visualizations available.
            </div>
          ) : (
            overview.charts.map((chartPath, idx) => (
              <div key={idx} className="theme-card p-4 rounded-xl border shadow-sm space-y-2">
                <h4 className="text-xs font-bold theme-muted uppercase">Distribution Plot #{idx + 1}</h4>
                <img
                  src={ApiService.getStaticUrl(chartPath)}
                  alt={`EDA Chart ${idx + 1}`}
                  className="w-full h-auto rounded-lg border object-contain max-h-80"
                />
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}