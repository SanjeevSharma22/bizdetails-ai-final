import React, { useRef, useState } from "react";
import { ColumnMappingScreen } from "./ColumnMappingScreen";

const API = import.meta.env.VITE_API_BASE || "";

export function JobUploader({ onComplete }) {
  const [file, setFile] = useState(null);
  const [jobName, setJobName] = useState("");
  const [strategy, setStrategy] = useState("internal_then_ai_fallback");
  const [step, setStep] = useState("upload");
  const [uploadedFile, setUploadedFile] = useState(null);
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

  const startMapping = async () => {
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API}/api/upload`, { method: "POST", body: form });
    const { headers } = await res.json();
    setUploadedFile({ file, columns: headers, data: [] });
    setStep("mapping");
  };

  const handleMappingComplete = async (_mapped, mapping) => {
    const backendKeyMap = {
      domain: "domain",
      companyName: "company_name",
      linkedinUrl: "linkedin_url",
      country: "country",
      industry: "industry",
      subindustry: "subindustry",
      size: "size",
      keywords: "keywords_cntxt",
    };
    const colMap = {};
    Object.entries(mapping).forEach(([uiKey, srcCol]) => {
      if (srcCol) {
        const backendKey = backendKeyMap[uiKey] || uiKey;
        colMap[backendKey] = srcCol.toLowerCase();
      }
    });
    const form = new FormData();
    form.append("file", file);
    form.append("job_name", jobName);
    form.append("strategy", strategy);
    if (Object.keys(colMap).length) {
      form.append("column_map", JSON.stringify(colMap));
    }
    const res = await fetch(`${API}/api/jobs`, { method: "POST", body: form });
    if (res.ok) {
      setFile(null);
      setJobName("");
      setStrategy("internal_then_ai_fallback");
      setUploadedFile(null);
      setStep("upload");
      onComplete && onComplete();
    }
  };

  if (step === "mapping" && uploadedFile) {
    return (
      <ColumnMappingScreen
        uploadedFile={uploadedFile}
        onMappingComplete={handleMappingComplete}
        onBack={() => setStep("upload")}
      />
    );
  }

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
          onClick={startMapping}
          disabled={!file}
          className="px-4 py-2 bg-green-600 text-black rounded disabled:opacity-50"
        >
          Start Job
        </button>
      </div>
    </div>
  );
}
