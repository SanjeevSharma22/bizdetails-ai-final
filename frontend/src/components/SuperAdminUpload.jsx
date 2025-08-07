import React, { useState } from "react";
import { Button } from "./ui/button";

export function SuperAdminUpload({ token }) {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");
  const API = import.meta.env.VITE_API_BASE;

  const handleUpload = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch(`${API}/api/superadmin/upload-companies`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      const data = await res.json();
      if (res.ok) {
        setStatus(`Inserted ${data.inserted}, updated ${data.updated}`);
      } else {
        setStatus(data.detail || "Upload failed");
      }
    } catch (err) {
      setStatus("Upload failed");
    }
  };

  return (
    <div className="space-y-4">
      <input
        type="file"
        accept=".csv"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      />
      <Button onClick={handleUpload} disabled={!file}>
        Upload
      </Button>
      {status && <p className="text-sm">{status}</p>}
    </div>
  );
}
