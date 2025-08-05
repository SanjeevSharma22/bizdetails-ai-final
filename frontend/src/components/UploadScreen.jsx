import React from 'react';

export function UploadScreen({ onFileUploaded }) {
  const handleChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const text = reader.result;
      const lines = text.split(/\r?\n/).filter(Boolean);
      if (!lines.length) return;
      const columns = lines[0].split(",");
      const data = lines.slice(1).map((line) => {
        const values = line.split(",");
      const columns = lines[0].split(',');
      const data = lines.slice(1).map(line => {
        const values = line.split(',');
        const row = {};
        columns.forEach((col, i) => {
          row[col] = values[i];
        });
        return row;
      });
      onFileUploaded({ file, data, columns });
    };
    reader.readAsText(file);
  };

  return (
    <div className="p-8 border-2 border-dashed rounded text-center">
      <input type="file" accept=".csv" onChange={handleChange} />
    </div>
  );
}
