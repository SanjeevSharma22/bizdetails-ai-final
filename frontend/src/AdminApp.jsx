import React, { useState } from 'react';

// Allow relative URLs if VITE_API_BASE isn't configured
const API = import.meta.env.VITE_API_BASE || '';

export default function AdminApp() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [token, setToken] = useState(null);
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setMessage('');
    try {
      const res = await fetch(`${API}/api/auth/signin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (res.ok) {
        const data = await res.json();
        setToken(data.access_token);
      } else {
        setMessage('Login failed');
      }
    } catch (err) {
      setMessage('Login error');
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setMessage('');
    try {
      const form = new FormData();
      form.append('file', file);
      const res = await fetch(`${API}/api/admin/company-updated/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: form,
      });
      if (res.ok) {
        setMessage('Upload successful');
        setFile(null);
      } else {
        setMessage('Upload failed');
      }
    } catch (err) {
      setMessage('Upload error');
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <form onSubmit={handleLogin} className="bg-white p-6 rounded shadow w-80 space-y-4">
          <h1 className="text-xl font-semibold text-center">Admin Login</h1>
          <input
            type="email"
            placeholder="Email"
            className="w-full border px-3 py-2 rounded"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <input
            type="password"
            placeholder="Password"
            className="w-full border px-3 py-2 rounded"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button
            type="submit"
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700"
          >
            Sign In
          </button>
          {message && <p className="text-red-500 text-sm text-center">{message}</p>}
        </form>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white p-6 rounded shadow w-96 space-y-4 text-center">
        <h1 className="text-xl font-semibold">Upload Company CSV</h1>
        <input
          type="file"
          accept=".csv"
          onChange={(e) => setFile(e.target.files[0])}
          className="w-full"
        />
        <button
          onClick={handleUpload}
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          disabled={!file}
        >
          Upload
        </button>
        {message && <p className="text-sm text-center">{message}</p>}
      </div>
    </div>
  );
}

