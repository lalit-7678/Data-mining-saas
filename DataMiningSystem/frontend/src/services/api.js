/**
 * Centralized API Service Client for FastAPI Backend
 */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const ApiService = {
  // Session Persistence
  getDatasetId: () => localStorage.getItem('active_dataset_id'),
  setDatasetId: (id) => localStorage.setItem('active_dataset_id', id),

  getCleanedDatasetId: () => localStorage.getItem('cleaned_dataset_id'),
  setCleanedDatasetId: (id) => localStorage.setItem('cleaned_dataset_id', id),

  /**
   * Upload CSV File
   * @param {File} file 
   */
  async uploadCSV(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/api/v1/data/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Failed to upload CSV file.');
    }
    return await response.json();
  },

  /**
   * Get Dataset Overview Metrics & Static Chart Links
   * @param {string} datasetId 
   */
  async getEDAOverview(datasetId) {
    const response = await fetch(`${API_BASE_URL}/api/v1/eda/overview/${datasetId}`);
    if (!response.ok) throw new Error('Failed to fetch dataset overview.');
    return await response.json();
  },

  /**
   * Get Automated Evidence-Based Insights
   * @param {string} datasetId 
   */
  async getEDAInsights(datasetId) {
    const response = await fetch(`${API_BASE_URL}/api/v1/eda/insights/${datasetId}`);
    if (!response.ok) throw new Error('Failed to fetch insights.');
    return await response.json();
  },

  /**
   * Execute Approved Data Cleaning Pipeline
   * @param {string} datasetId 
   * @param {Array<string>} approvedItemIds 
   */
  async executeCleaning(datasetId, approvedItemIds = []) {
    const response = await fetch(`${API_BASE_URL}/api/v1/data/clean`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        dataset_id: datasetId,
        approved_item_ids: approvedItemIds,
      }),
    });

    if (!response.ok) throw new Error('Failed to execute cleaning pipeline.');
    return await response.json();
  },

  /**
   * Trigger ReportLab PDF Export
   * @param {string} datasetId 
   */
  async exportPDF(datasetId) {
    const response = await fetch(`${API_BASE_URL}/api/v1/eda/export-pdf/${datasetId}`);
    if (!response.ok) throw new Error('Failed to generate PDF report.');
    return await response.json();
  },

  /**
   * Helper to append API Base URL to relative static asset paths
   * @param {string} relativePath 
   */
  getStaticUrl(relativePath) {
    if (!relativePath) return '';
    return relativePath.startsWith('http') ? relativePath : `${API_BASE_URL}${relativePath}`;
  }
};