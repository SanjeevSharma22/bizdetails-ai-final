import React from 'react';

export function Badge({ children, className = '', ...props }) {
  return (
    <span className={`px-2 py-1 text-xs rounded ${className}`} {...props}>
      {children}
    </span>
  );
}
