import React, { useState } from 'react';
import { Button } from './ui/button';

export function ColumnMappingScreen({ uploadedFile, onMappingComplete, onBack }) {
  const [showModal, setShowModal] = useState(false);
  const [mapping, setMapping] = useState({
    domain: '',
    'Company Name': '',
    country: '',
    industry: '',
    subindustry: '',
    size: '',
    keywords: '',
  });

  const handleSubmit = () => {
    if (!mapping.domain && !mapping['Company Name']) {
      return;
    }

    const backendKeyMap = {
      domain: 'Domain',
      'Company Name': 'Company Name',
      country: 'Country',
      industry: 'Industry',
      subindustry: 'Subindustry',
      size: 'Company Size',
      keywords: 'Keywords',
    };

    const mapped = uploadedFile.data.map((row) => {
      const result = {};
      Object.entries(mapping).forEach(([key, column]) => {
        if (column) {
          const backendKey = backendKeyMap[key] || key;
          result[backendKey] = row[column];
        }
      });
      return result;
    });

    onMappingComplete(mapped);
    setShowModal(false);
  };

  const renderSelect = (label, key, required = false) => (
    <div>
      <label className="block text-sm font-medium mb-1">
        {label}
        {required && <span className="text-red-500">*</span>}
      </label>
      <select
        value={mapping[key]}
        onChange={(e) => setMapping({ ...mapping, [key]: e.target.value })}
        className="w-full border rounded p-2"
      >
        <option value="">Select column</option>
        {uploadedFile.columns.map((col) => (
          <option key={col} value={col}>
            {col}
          </option>
        ))}
      </select>
      {!required && <span className="text-xs text-gray-500">Optional</span>}
    </div>
  );

  return (
    <div className="space-y-4">
      <p>
        Column mapping for <strong>{uploadedFile.file.name}</strong>
      </p>
      <div className="flex gap-2">
        <Button onClick={() => setShowModal(true)}>Finish Mapping</Button>
        <Button onClick={onBack} variant="outline">
          Back
        </Button>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded shadow-md w-full max-w-md space-y-4">
            <h2 className="text-lg font-semibold">Map Columns</h2>
            <div className="space-y-4 max-h-[60vh] overflow-y-auto">
              {renderSelect('Domain', 'domain', true)}
              {renderSelect('Company Name', 'Company Name', true)}
              <p className="text-xs text-gray-500 -mt-2">Domain or Company Name is required.</p>
              {renderSelect('Company Country', 'country')}
              {renderSelect('Company Industry', 'industry')}
              {renderSelect('Company Subindustry', 'subindustry')}
              {renderSelect('Company Size', 'size')}
              {renderSelect('Company Keywords (Context)', 'keywords')}
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setShowModal(false)}>
                Cancel
              </Button>
              <Button onClick={handleSubmit} disabled={!mapping.domain && !mapping['Company Name']}>
                Submit
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
