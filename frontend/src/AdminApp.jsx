import React, { useState } from 'react';

// Allow relative URLs if VITE_API_BASE isn't configured
const API = import.meta.env.VITE_API_BASE || '';

export default function AdminApp() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [token, setToken] = useState(null);
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState('');
  const [mode, setMode] = useState('override');
  const [errors, setErrors] = useState([]);
  const [headers, setHeaders] = useState([]);
  const [columnMap, setColumnMap] = useState({});

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

  const FIELDS = [
    'domain',
    'name',
    'countries',
    'hq',
    'industry',
    'subindustry',
    'keywords_cntxt',
    'size',
    'linkedin_url',
    'slug',
    'original_name',
    'legal_name',
  ];

  const handleFileChange = async (e) => {
    const f = e.target.files[0];
    setFile(f);
    setMessage('');
    setHeaders([]);
    setColumnMap({});
    if (f) {
      const text = await f.text();
      const firstLine = text.split(/\r?\n/)[0] || '';
      const cols = firstLine.split(',').map((c) => c.trim()).filter(Boolean);
      setHeaders(cols);
      const initial = {};
      FIELDS.forEach((field) => {
        if (cols.includes(field)) initial[field] = field;
      });
      setColumnMap(initial);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setMessage('Processing...');
    setErrors([]);
    try {
      const form = new FormData();
      form.append('file', file);
      form.append('mode', mode);
      const mapped = {};
      Object.entries(columnMap).forEach(([field, col]) => {
        if (col && col !== field) mapped[field] = col;
      });
      if (Object.keys(mapped).length > 0) {
        form.append('column_map', JSON.stringify(mapped));
      }
      const res = await fetch(`${API}/api/admin/company-updated/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: form,
      });
      if (res.ok) {
        const data = await res.json();
        setMessage(`Created ${data.created}, Updated ${data.updated}`);
        setErrors(data.errors || []);
        setFile(null);
        setHeaders([]);
        setColumnMap({});
      } else {
        let msg = 'Upload failed';
        try {
          const data = await res.json();
          msg = data.detail || data.message || msg;
          if (data.errors) setErrors(data.errors);
        } catch (_) {
          const text = await res.text();
          if (text) msg = text;
        }
        setMessage(msg);
      }
    } catch (err) {
      setMessage(`Upload error: ${err.message}`);
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
          onChange={handleFileChange}
          className="w-full"
        />
        {headers.length > 0 && (
          <div className="text-left space-y-2">
            <p className="font-semibold">Match columns</p>
            {FIELDS.map((field) => (
              <div key={field} className="flex items-center space-x-2">
                <label className="w-32 capitalize">{field}</label>
                <select
                  className="flex-1 border px-2 py-1"
                  value={columnMap[field] || ''}
                  onChange={(e) =>
                    setColumnMap({ ...columnMap, [field]: e.target.value })
                  }
                >
                  <option value="">--</option>
                  {headers.map((h) => (
                    <option key={h} value={h}>
                      {h}
                    </option>
                  ))}
                </select>
              </div>
            ))}
          </div>
        )}
        <div className="flex flex-col items-start space-y-2 text-left">
          <label className="flex items-center space-x-2">
            <input
              type="radio"
              value="override"
              checked={mode === 'override'}
              onChange={() => setMode('override')}
            />
            <span>Override with new data</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              type="radio"
              value="missing"
              checked={mode === 'missing'}
              onChange={() => setMode('missing')}
            />
            <span>Update only missing fields</span>
          </label>
        </div>
        <button
          onClick={handleUpload}
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          disabled={!file}
        >
          Upload
        </button>
        {message && <p className="text-sm text-center">{message}</p>}
        {errors.length > 0 && (
          <div className="text-left text-sm max-h-40 overflow-y-auto">
            <p className="font-semibold">Errors:</p>
            <ul className="list-disc pl-5 space-y-1">
              {errors.map((e, idx) => (
                <li key={idx}>
                  Row {e.row}: {e.error}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

