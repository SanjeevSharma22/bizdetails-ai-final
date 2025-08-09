import React from 'react';
import { CompanyTable } from './CompanyTable';

export function Dashboard() {
  return (
    <div className="bg-black p-4 rounded border border-green-500">
      <CompanyTable />
    </div>
  );
}
