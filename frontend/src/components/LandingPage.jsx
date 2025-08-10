import React, { useState } from "react";
import { Database, Globe, Brain, Building2, Check } from "lucide-react";

export function LandingPage({ onSignIn }) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    onSignIn({ email, name: fullName || email, token: "demo" });
  };

  const tags = [
    "B2B Sales Lead Generation",
    "Marketing Campaign Targeting",
    "Data Enrichment & Cleansing",
    "Competitive Intelligence",
    "Account-Based Marketing",
    "CRM Data Enhancement",
  ];

  return (
    <div className="min-h-screen bg-white text-gray-900 flex flex-col">
      <header className="w-full border-b border-gray-200">
        <div className="max-w-7xl mx-auto flex items-center justify-between py-4 px-6">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-md flex items-center justify-center">
              <Database className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold">BizDetails AI</h1>
              <p className="text-sm text-gray-500">
                Enriching Business Data with AI Precision
              </p>
            </div>
          </div>
          <button className="px-4 py-2 text-sm text-purple-700 bg-purple-50 rounded-full">
            Beta Access
          </button>
        </div>
      </header>

      <main className="flex-1">
        <div className="max-w-7xl mx-auto px-6 py-16 grid gap-12 md:grid-cols-2 items-center">
          <div>
            <span className="inline-block px-3 py-1 mb-6 text-sm rounded-full bg-purple-100 text-purple-700">
              Powered by Advanced AI
            </span>
            <h2 className="text-4xl font-bold mb-4">
              Enrich Your Business Data with{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-purple-600">
                AI
              </span>{" "}
              Precision
            </h2>
            <p className="text-gray-700 mb-6">
              Transform incomplete company data into comprehensive business
              intelligence.
            </p>
            <ul className="space-y-4 mb-8">
              <li className="flex items-center space-x-3">
                <Globe className="w-5 h-5 text-blue-600" />
                <span>Precise Domain Mapping</span>
              </li>
              <li className="flex items-center space-x-3">
                <Database className="w-5 h-5 text-purple-600" />
                <span>Global Data Enrichment</span>
              </li>
              <li className="flex items-center space-x-3">
                <Brain className="w-5 h-5 text-blue-600" />
                <span>Context-Aware Intelligence</span>
              </li>
              <li className="flex items-center space-x-3">
                <Building2 className="w-5 h-5 text-purple-600" />
                <span>Complete Business Profiles</span>
              </li>
            </ul>
            <div>
              <h3 className="font-semibold mb-2">Perfect for:</h3>
              <div className="flex flex-wrap gap-2">
                {tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-sm"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <form
            onSubmit={handleSubmit}
            className="bg-white p-8 rounded-xl shadow-lg border border-gray-100 w-full max-w-md mx-auto"
          >
            <h2 className="text-2xl font-semibold mb-2 text-center">
              Get Started
            </h2>
            <p className="text-gray-600 mb-6 text-center">
              Create your free account in seconds.
            </p>
            <div className="space-y-4">
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Full Name"
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email Address"
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                type="submit"
                className="w-full py-3 rounded-md text-white font-medium bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 transition"
              >
                Start Enriching Data →
              </button>
            </div>
            <ul className="mt-6 space-y-1 text-sm text-gray-600">
              <li className="flex items-center">
                <Check className="w-4 h-4 text-green-500 mr-2" />
                GDPR & CCPA Compliant
              </li>
              <li className="flex items-center">
                <Check className="w-4 h-4 text-green-500 mr-2" />
                Enterprise-Grade Security
              </li>
              <li className="flex items-center">
                <Check className="w-4 h-4 text-green-500 mr-2" />
                No Credit Card Required
              </li>
            </ul>
          </form>
        </div>
      </main>
    </div>
  );
}
