import React from 'react';

export function UploadScreen({ onFileUploaded }) {
  // Fallback to relative path when VITE_API_BASE isn't provided to avoid
  // "Failed to fetch" errors due to an undefined base URL.
  const API = import.meta.env.VITE_API_BASE || '';

  const handleChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // 1. Send file to backend to extract headers
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch(`${API}/api/upload`, {
      method: 'POST',
      body: formData,
    });
    const { headers } = await response.json();  // e.g. ["Company Name", "Country", ...]

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

    // 4. Notify parent with the raw file, parsed rows, and header list
    onFileUploaded({ file, data, columns: headers });
  };

  return (
    <div className="p-8 border-2 border-dashed rounded text-center">
      <input type="file" accept=".csv" onChange={handleChange} />
    </div>
  );
}
