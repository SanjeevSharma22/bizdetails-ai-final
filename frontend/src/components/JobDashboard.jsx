import React, { useEffect, useState } from "react";
import { JobUploader } from "./JobUploader";
import { JobsTable } from "./JobsTable";
import { JobDetails } from "./JobDetails";

const API = import.meta.env.VITE_API_BASE || "";

export function JobDashboard() {
  const [jobs, setJobs] = useState([]);
  const [selected, setSelected] = useState(null);

  const fetchJobs = () => {
    fetch(`${API}/api/jobs`)
      .then((r) => r.json())
      .then((d) => setJobs(d.jobs || []));
  };

  useEffect(() => {
    fetchJobs();
    const id = setInterval(fetchJobs, 5000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="space-y-6">
      <JobUploader onComplete={fetchJobs} />
      <JobsTable jobs={jobs} onSelect={setSelected} />
      {selected && <JobDetails jobId={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}
