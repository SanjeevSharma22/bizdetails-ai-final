import React, { useState, useEffect } from "react";
import { Database, Globe, Brain, Building2, Check } from "lucide-react";

export function LandingPage({ onSignIn }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [username, setUsername] = useState("");
  const [role, setRole] = useState("");
  const [isSignUp, setIsSignUp] = useState(false);

  // Keep the URL hash in sync so navigating to `#signup` opens the sign-up form
  useEffect(() => {
    const updateFromHash = () => {
      setIsSignUp(window.location.hash === "#signup");
    };
    updateFromHash();
    window.addEventListener("hashchange", updateFromHash);
    return () => window.removeEventListener("hashchange", updateFromHash);
  }, []);

  // Allow the component to work without an explicit VITE_API_BASE by
  // falling back to relative URLs so the frontend can communicate with the
  // backend in development environments where the variable isn't set.
  const API = import.meta.env.VITE_API_BASE || "";

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      let res;
      if (isSignUp) {
        res = await fetch(`${API}/api/auth/signup`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email,
            password,
            username,
            role,
            fullName: username || email,
          }),
        });
        if (!res.ok) throw new Error("Auth failed");
      } else {
        // First try to sign in. If that fails (e.g. user doesn't exist),
        // automatically attempt to sign them up.
        res = await fetch(`${API}/api/auth/signin`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });
        if (!res.ok) {
          res = await fetch(`${API}/api/auth/signup`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password, fullName: email }),
          });
          if (!res.ok) throw new Error("Auth failed");
        }
      }
      const { access_token } = await res.json();
      onSignIn({ email, name: username || email, token: access_token });
    } catch (err) {
      alert("Failed to sign in. Please try again.");
    }
  };

  const tags = [
    "B2B Sales Lead Generation",
    "Marketing Campaign Targeting",
    "Data Enrichment & Cleansing",
    "Competitive Intelligence",
    "Account-Based Marketing",
    "CRM Data Enhancement",
  ];

  const features = [
    {
      icon: Database,
      color: "text-blue-600",
      title: "Precise Domain Mapping",
      description:
        "AI-powered matching of company names to their verified business websites with 95%+ accuracy.",
    },
    {
      icon: Brain,
      color: "text-purple-600",
      title: "Context-Aware Intelligence",
      description:
        "Leverages industry, location, and company details for intelligent data enhancement.",
    },
    {
      icon: Globe,
      color: "text-blue-600",
      title: "Global Data Enrichment",
      description:
        "Identify regional domains, subsidiaries, and international business presence.",
    },
    {
      icon: Building2,
      color: "text-purple-600",
      title: "Complete Business Profiles",
      description:
        "Build comprehensive company profiles with verified domains and business details.",
    },
  ];

  return (
    <div className="min-h-screen bg-white text-gray-900 flex flex-col">
      <header className="w-full border-b border-gray-200">
        <div className="max-w-7xl 2xl:max-w-none mx-auto flex items-center justify-between py-4 px-6 2xl:px-16">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-md flex items-center justify-center">
              <Database className="w-6 h-6 text-white" />
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
        <div className="max-w-7xl 2xl:max-w-none mx-auto px-6 2xl:px-16 py-16 grid gap-12 md:grid-cols-2 items-center">
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
              intelligence. Map domains, validate details, and enrich your
              database with AI-powered accuracy.
            </p>
            <div className="grid sm:grid-cols-2 gap-6 mb-8">
              {features.map((f) => (
                <div key={f.title} className="flex items-start space-x-3">
                  <f.icon className={`w-6 h-6 ${f.color} mt-1`} />
                  <div>
                    <h4 className="font-semibold">{f.title}</h4>
                    <p className="text-sm text-gray-600">{f.description}</p>
                  </div>
                </div>
              ))}
            </div>
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
            <h2 className="text-xl font-semibold mb-6 text-center">
              Get Started – Access the most comprehensive business data
              enrichment platform
            </h2>
            <div className="space-y-4">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email Address"
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {isSignUp && (
                <>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="Username"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <input
                    type="text"
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    placeholder="Role"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </>
              )}
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                type="submit"
                className="w-full py-3 rounded-md text-white font-medium bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 transition shadow"
              >
                {isSignUp ? "Sign up" : "Login"}
              </button>
              <p className="text-sm text-center">
                {isSignUp ? (
                  <>
                    Already have an account?{" "}
                    <button
                      type="button"
                      onClick={() => {
                        setIsSignUp(false);
                        window.location.hash = "";
                      }}
                      className="text-blue-600 hover:underline"
                    >
                      Login
                    </button>
                  </>
                ) : (
                  <>
                    Don't have an account?{" "}
                    <button
                      type="button"
                      onClick={() => {
                        setIsSignUp(true);
                        window.location.hash = "signup";
                      }}
                      className="text-blue-600 hover:underline"
                    >
                      Sign up
                    </button>
                  </>
                )}
              </p>
            </div>
            <ul className="mt-6 space-y-1 text-sm text-gray-600">
              <li className="flex items-center">
                <Check className="w-5 h-5 text-green-500 mr-2" /> GDPR & CCPA
                Compliant
              </li>
              <li className="flex items-center">
                <Check className="w-5 h-5 text-green-500 mr-2" />{" "}
                Enterprise-Grade Security
              </li>
              <li className="flex items-center">
                <Check className="w-5 h-5 text-green-500 mr-2" /> No Credit Card
                Required
              </li>
            </ul>
          </form>
        </div>
      </main>
    </div>
  );
}
