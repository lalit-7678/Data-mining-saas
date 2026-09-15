import React, { useState } from 'react';
import { ApiService } from '../services/api';

export default function Dashboard({ onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [summary, setSummary] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.name.endsWith('.csv')) {
        setFile(droppedFile);
        setError(null);
      } else {
        setError('Please drop a valid .csv file.');
      }
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setIsLoading(true);
    setError(null);

    try {
      // 1. Send file to backend
      const uploadRes = await ApiService.uploadCSV(file);
      ApiService.setDatasetId(uploadRes.dataset_id);
      localStorage.setItem(`analysis_${uploadRes.dataset_id}`, JSON.stringify(uploadRes));

      // 2. Fetch dataset overview metrics directly from backend
      const overviewRes = await ApiService.getEDAOverview(uploadRes.dataset_id);

      setSummary({
        rows: overviewRes.overview?.total_rows ?? 0,
        columns: overviewRes.overview?.total_columns ?? 0,
        missingPct: overviewRes.overview?.missing_pct ?? 0,
        qualityScore: overviewRes.overview?.quality_score ?? 'N/A',
      });

      if (onUploadSuccess) {
        onUploadSuccess(uploadRes);
      }
    } catch (err) {
      setError(err.message || 'Error uploading dataset.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Description Banner */}
      <div className="theme-card p-6 rounded-xl border shadow-sm">
        <h2 className="text-xl font-bold mb-2">Dataset Profiling & Upload Hub</h2>
        <p className="text-sm theme-muted">
          Upload your raw CSV file to trigger automated semantic profiling, data quality auditing, and interactive EDA diagnostics. Supported target size: Up to 100,000 rows.
        </p>
      </div>

      {/* Upload Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`theme-card p-10 rounded-xl border-2 border-dashed text-center transition ${
          isDragging ? 'drag-active' : ''
        }`}
      >
        <div className="w-12 h-12 mx-auto mb-4 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-bold text-xl">
          📁
        </div>
        <p className="text-base font-semibold mb-1">Drag and drop your CSV file here</p>
        <p className="text-xs theme-muted mb-4">Maximum file size recommended: 100MB (.csv format)</p>

        <input
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          id="csvFileInput"
          className="hidden"
        />

        <div className="flex justify-center items-center space-x-3">
          <label
            htmlFor="csvFileInput"
            className="px-4 py-2 bg-slate-200 dark:bg-slate-700 hover:opacity-80 rounded-lg text-xs font-semibold cursor-pointer transition"
          >
            Browse File
          </label>
          {file && (
            <button
              onClick={handleUpload}
              disabled={isLoading}
              className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-md transition disabled:opacity-50"
            >
              {isLoading ? 'Processing Pipeline...' : 'Upload & Analyze'}
            </button>
          )}
        </div>

        {file && (
          <div className="mt-4 text-xs font-medium theme-muted">
            Selected File: <span className="font-bold text-blue-600">{file.name}</span> ({(file.size / (1024 * 1024)).toFixed(2)} MB)
          </div>
        )}

        {error && (
          <div className="mt-4 p-3 bg-red-100 text-red-700 rounded-lg text-xs font-semibold">
            {error}
          </div>
        )}
      </div>

      {/* Dataset Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="theme-card p-5 rounded-xl border shadow-sm">
            <p className="text-xs theme-muted uppercase font-semibold">Total Rows</p>
            <p className="text-2xl font-bold mt-1">{summary.rows.toLocaleString()}</p>
          </div>
          <div className="theme-card p-5 rounded-xl border shadow-sm">
            <p className="text-xs theme-muted uppercase font-semibold">Total Columns</p>
            <p className="text-2xl font-bold mt-1">{summary.columns}</p>
          </div>
          <div className="theme-card p-5 rounded-xl border shadow-sm">
            <p className="text-xs theme-muted uppercase font-semibold">Missing Cells</p>
            <p className="text-2xl font-bold mt-1 text-amber-600">{summary.missingPct}%</p>
          </div>
          <div className="theme-card p-5 rounded-xl border shadow-sm">
            <p className="text-xs theme-muted uppercase font-semibold">Quality Score</p>
            <p className="text-2xl font-bold mt-1 text-emerald-600">{summary.qualityScore}</p>
          </div>
        </div>
      )}
    </div>
  );
}