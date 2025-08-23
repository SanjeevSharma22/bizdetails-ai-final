import React, { useState } from "react";
import { CompanyTable } from "./CompanyTable";
import { FilterPanel } from "./FilterPanel";

export function Dashboard() {
  const [filters, setFilters] = useState({});

  return (
    <div className="bg-black p-4 rounded border border-green-500">
      <div className="flex flex-col md:flex-row">
        <FilterPanel onApply={setFilters} onClear={() => setFilters({})} />
        <div className="flex-1">
          <CompanyTable filters={filters} />
        </div>
      </div>
    </div>
  );
}
