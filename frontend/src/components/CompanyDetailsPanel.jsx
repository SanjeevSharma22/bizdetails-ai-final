import React from 'react';

export function CompanyDetailsPanel({ company, onClose }) {
  return (
    <div
      className={`fixed top-0 right-0 h-full w-80 bg-gray-900 text-green-400 shadow-lg transform transition-transform duration-300 border-l border-green-500 ${
        company ? 'translate-x-0' : 'translate-x-full'
      }`}
    >
      <div className="p-4 border-b border-green-500 flex justify-between items-center">
        <h2 className="text-lg">Details</h2>
        <button
          onClick={onClose}
          className="text-green-400 hover:text-green-200"
        >
          ✕
        </button>
      </div>
      {company && (
        <div className="p-4 space-y-2 text-sm">
          <p>
            <strong>Name:</strong> {company.name || 'N/A'}
          </p>
          <p>
            <strong>Domain:</strong> {company.domain}
          </p>
          <p>
            <strong>Headquarters:</strong> {company.hq || 'N/A'}
          </p>
          <p>
            <strong>Industry:</strong> {company.industry || 'N/A'}
          </p>
          <p>
            <strong>LinkedIn:</strong>{' '}
            {company.linkedin_url ? (
              <a
                href={company.linkedin_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:underline"
              >
                {company.linkedin_url}
              </a>
            ) : (
              'N/A'
            )}
          </p>
        </div>
      )}
    </div>
  );
}
