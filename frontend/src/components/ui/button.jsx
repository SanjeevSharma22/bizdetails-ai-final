import React from 'react';

export function Button({ children, variant = 'primary', className = '', size, ...props }) {
  const variants = {
    primary: 'btn btn-primary',
    outline: 'btn btn-secondary',
    ghost: 'btn btn-ghost',
  };
  const variantClass = variants[variant] || variants.primary;

  return (
    <button className={`${variantClass} ${className}`} {...props}>
      {children}
    </button>
  );
}
