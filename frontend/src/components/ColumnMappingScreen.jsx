import React from 'react';
import { Button } from './ui/button';

export function ColumnMappingScreen({ uploadedFile, onMappingComplete, onBack }) {
  return (
    <div className="space-y-4">
      <p>Column mapping for <strong>{uploadedFile.file.name}</strong></p>
      <div className="flex gap-2">
        <Button onClick={() => onMappingComplete(uploadedFile.data)}>
          Finish Mapping
        </Button>
        <Button onClick={onBack} variant="outline">
          Back
        </Button>
      </div>
    </div>
  );
}
