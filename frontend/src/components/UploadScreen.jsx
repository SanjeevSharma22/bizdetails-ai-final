import React, { useRef, useState } from 'react';

export function UploadScreen({ onFileUploaded }) {
  // Fallback to relative path when VITE_API_BASE isn't provided to avoid
  // "Failed to fetch" errors due to an undefined base URL.
  const API = import.meta.env.VITE_API_BASE || '';
  const inputRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleFileSelect = () => inputRef.current?.click();

  const handleChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    setProgress(10);

    // 1. Send file to backend to extract headers
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch(`${API}/api/upload`, {
      method: 'POST',
      body: formData,
    });
    setProgress(60);
    const { headers } = await response.json(); // e.g. ["Company Name", "Country", ...]

    // 2. Read file text and split into rows
    const text = await file.text();
    const lines = text.split(/\r?\n/).filter((l) => l.trim() !== '');

    // 3. Build array of objects keyed by header names
    const data = lines.slice(1).map((line) => {
      const values = line.split(',');
      const row = {};
      headers.forEach((col, i) => {
        row[col] = values[i] ?? '';
      });
      return row;
    });

    setProgress(100);
    setTimeout(() => setUploading(false), 300);
    // 4. Notify parent with the raw file, parsed rows, and header list
    onFileUploaded({ file, data, columns: headers });
  };

  return (
    <div className="card p-8 text-center">
      <p className="mb-4">Upload a .csv file with a Domain or Company Name column.</p>
      <button onClick={handleFileSelect} className="btn btn-primary">
        Upload CSV
      </button>
      <input
        ref={inputRef}
        type="file"
        accept=".csv"
        onChange={handleChange}
        className="hidden"
      />
      {uploading && (
        <div className="mt-4 w-full bg-gray-200 h-2 rounded">
          <div
            className="h-full bg-purple-600 transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
    </div>
  );
}
