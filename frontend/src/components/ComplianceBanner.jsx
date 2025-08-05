import React from 'react';
import { Button } from './ui/button';

export function ComplianceBanner({ onDismiss }) {
  return (
    <div className="bg-yellow-100 text-yellow-900 p-2 text-center text-sm flex items-center justify-center gap-4">
      <span>This is a demo. Data may be incomplete.</span>
      <Button onClick={onDismiss}>Dismiss</Button>
    </div>
  );
}
