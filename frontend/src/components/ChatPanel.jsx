import React, { useState } from 'react';
import { Button } from './ui/button';

export function ChatPanel({ onClose }) {
  const [message, setMessage] = useState('');

  return (
    <div className="bg-white border h-full w-full flex flex-col rounded-none sm:rounded">
      <div className="flex justify-between items-center p-2 border-b">
        <span className="font-semibold">AI Assistant</span>
        <Button onClick={onClose}>Close</Button>
      </div>
      <div className="flex-1 p-2 overflow-auto">
        <p className="text-sm text-gray-500">Chat functionality not implemented.</p>
      </div>
      <div className="p-2 border-t flex gap-2">
        <input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          className="flex-1 border px-2 py-1 rounded"
          placeholder="Ask a question..."
        />
        <Button onClick={() => setMessage('')}>Send</Button>
      </div>
    </div>
  );
}
