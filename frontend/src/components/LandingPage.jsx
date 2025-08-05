import React, { useState } from 'react';
import { Button } from './ui/button';

export function LandingPage({ onSignIn }) {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSignIn(email, name || 'User');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-purple-50">
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded shadow w-80 space-y-4">
        <h2 className="text-xl font-semibold text-center">Sign In</h2>
        <input
          type="email"
          required
          placeholder="Email"
          className="w-full border px-2 py-1 rounded"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <input
          type="text"
          placeholder="Name"
          className="w-full border px-2 py-1 rounded"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <Button type="submit" className="w-full">Sign In</Button>
      </form>
    </div>
  );
}
