import React, { useState } from 'react';
import { Button } from './ui/button';

export function LandingPage({ onSignIn }) {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [isSignup, setIsSignup] = useState(false);
  const API = import.meta.env.VITE_API_BASE;

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const endpoint = isSignup ? 'signup' : 'signin';
      const res = await fetch(`${API}/api/auth/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (res.ok) {
        const data = await res.json();
        onSignIn({ email, name: name || 'User', token: data.access_token });
      }
    } catch (err) {
      console.error(`Sign ${isSignup ? 'up' : 'in'} failed`, err);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-purple-50">
      <form
        onSubmit={handleSubmit}
        className="bg-white p-8 rounded shadow w-80 space-y-4"
      >
        <h2 className="text-xl font-semibold text-center">
          {isSignup ? 'Sign Up' : 'Sign In'}
        </h2>
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
        <input
          type="password"
          required
          placeholder="Password"
          className="w-full border px-2 py-1 rounded"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <Button type="submit" className="w-full">
          {isSignup ? 'Sign Up' : 'Sign In'}
        </Button>
        <div className="text-sm text-center">
          {isSignup ? (
            <>
              Already have an account?{' '}
              <button
                type="button"
                className="text-blue-600 underline"
                onClick={() => setIsSignup(false)}
              >
                Sign In
              </button>
            </>
          ) : (
            <>
              Need an account?{' '}
              <button
                type="button"
                className="text-blue-600 underline"
                onClick={() => setIsSignup(true)}
              >
                Sign Up
              </button>
            </>
          )}
        </div>
      </form>
    </div>
  );
}
