import React, { useRef, useState } from "react";

const API = import.meta.env.VITE_API_BASE || "";

export function JobUploader({ onComplete }) {
  const [file, setFile] = useState(null);
  const [jobName, setJobName] = useState("");
  const [strategy, setStrategy] = useState("internal_then_ai_fallback");
  const inputRef = useRef(null);

  const handleBrowse = () => inputRef.current?.click();

  const handleFile = (f) => {
    if (!f) return;
    setFile(f);
    if (!jobName) {
      const base = f.name.replace(/\.csv$/i, "");
      setJobName(base);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files?.length) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async () => {
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    form.append("job_name", jobName);
    form.append("strategy", strategy);
    const res = await fetch(`${API}/api/jobs`, { method: "POST", body: form });
    if (res.ok) {
      setFile(null);
      setJobName("");
      setStrategy("internal_then_ai_fallback");
      onComplete && onComplete();
    }
  };

  return (
    <div className="space-y-4">
      <div
        className="border-2 border-dashed border-green-500 rounded p-6 text-center cursor-pointer"
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onClick={handleBrowse}
      >
        {file ? <p>{file.name}</p> : <p>Drag & drop CSV here or click to browse</p>}
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          onChange={(e) => handleFile(e.target.files?.[0])}
          className="hidden"
        />
      </div>
      <div className="grid sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm mb-1">Job Name</label>
          <input
            value={jobName}
            onChange={(e) => setJobName(e.target.value)}
            className="w-full p-2 bg-black border border-green-500 rounded"
          />
        </div>
        <div>
          <label className="block text-sm mb-1">Strategy</label>
          <select
            value={strategy}
            onChange={(e) => setStrategy(e.target.value)}
            className="w-full p-2 bg-black border border-green-500 rounded"
          >
            <option value="internal_only">internal_only</option>
            <option value="ai_only">ai_only</option>
            <option value="internal_then_ai_fallback">internal_then_ai_fallback</option>
          </select>
        </div>
      </div>
      <div className="text-right">
        <button
          onClick={handleSubmit}
          disabled={!file}
          className="px-4 py-2 bg-green-600 text-black rounded disabled:opacity-50"
        >
          Start Job
        </button>
      </div>
    </div>
  );
}
