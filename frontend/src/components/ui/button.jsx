import React from 'react';

export function Button({ children, className = '', ...props }) {
  return (
    <button
      className={`px-3 py-1 rounded border border-gray-300 bg-white hover:bg-gray-50 ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
