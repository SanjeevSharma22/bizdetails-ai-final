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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center p-6">
      <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-12 items-center">
        <div className="space-y-6">
          <div>
            <h1 className="text-4xl font-bold text-gray-900">BizDetails AI</h1>
            <p className="text-lg text-gray-700">Enriching Business Data with AI Precision</p>
          </div>
          <div className="flex items-center space-x-3">
            <span className="px-3 py-1 bg-purple-100 text-purple-700 text-sm rounded-full">Beta Access</span>
            <span className="text-sm text-gray-600">Powered by Advanced AI</span>
          </div>
          <p className="text-gray-700">
            Enrich Your Business Data with AI Precision. Transform incomplete company
            data into comprehensive business intelligence. Map domains, validate details,
            and enrich your database with AI-powered accuracy.
          </p>
          <ul className="space-y-2 text-gray-700">
            <li>
              <strong>Precise Domain Mapping</strong> – AI-powered matching of company
              names to their verified business websites with 95%+ accuracy
            </li>
            <li>
              <strong>Global Data Enrichment</strong> – Identify regional domains,
              subsidiaries, and international business presence
            </li>
            <li>
              <strong>Context-Aware Intelligence</strong> – Leverages industry,
              location, and company details for intelligent data enhancement
            </li>
            <li>
              <strong>Complete Business Profiles</strong> – Build comprehensive company
              profiles with verified domains and business details
            </li>
          </ul>
          <div>
            <h3 className="font-semibold">Perfect for:</h3>
            <ul className="grid grid-cols-2 gap-1 text-gray-700 text-sm">
              <li>B2B Sales Lead Generation</li>
              <li>Marketing Campaign Targeting</li>
              <li>Data Enrichment & Cleansing</li>
              <li>Competitive Intelligence</li>
              <li>Account-Based Marketing</li>
              <li>CRM Data Enhancement</li>
            </ul>
          </div>
          <div className="flex gap-6 text-center">
            <div>
              <p className="text-2xl font-bold">95%</p>
              <p className="text-xs text-gray-500">Accuracy Rate</p>
            </div>
            <div>
              <p className="text-2xl font-bold">2.3s</p>
              <p className="text-xs text-gray-500">Avg Processing</p>
            </div>
            <div>
              <p className="text-2xl font-bold">150+</p>
              <p className="text-xs text-gray-500">Countries</p>
            </div>
          </div>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-white p-8 rounded shadow w-full space-y-4"
        >
          <h2 className="text-xl font-semibold text-center">
            {isSignup ? 'Sign Up' : 'Sign In'}
          </h2>
          <input
            type="text"
            placeholder="Enter your full name"
            className="w-full border px-2 py-1 rounded"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <input
            type="email"
            required
            placeholder="Enter your email"
            className="w-full border px-2 py-1 rounded"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
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
            {isSignup ? 'Start Enriching Data' : 'Sign In'}
          </Button>
          <div className="text-xs text-gray-500 text-center">
            GDPR & CCPA Compliant • Enterprise-Grade Security • No Credit Card Required
          </div>
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
    </div>
  );
}
