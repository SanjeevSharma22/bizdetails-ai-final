import React from 'react';

export function UploadScreen({ onFileUploaded }) {
  const API = import.meta.env.VITE_API_BASE;

  const handleChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch(`${API}/api/upload`, {
      method: 'POST',
      body: formData,
    });
    const { headers } = await response.json();

    const text = await file.text();
    const lines = text.split(/\r?\n/).filter(Boolean);
    const data = lines.slice(1).map(line => {
      const values = line.split(',');
      const row = {};
      headers.forEach((col, i) => {
        row[col] = values[i];
      });
      return row;
    });
    onFileUploaded({ file, data, columns: headers });
  };

  return (
    <div className="p-8 border-2 border-dashed rounded text-center">
      <input type="file" accept=".csv" onChange={handleChange} />
    </div>
  );
}
