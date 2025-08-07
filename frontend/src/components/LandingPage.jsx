import React, { useState } from "react";
import { Database } from "lucide-react";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";

export function LandingPage({ onSignIn }) {
  const [fullName, setFullName] = useState("");
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isSignup, setIsSignup] = useState(false);
  const [errors, setErrors] = useState({});
  const API = import.meta.env.VITE_API_BASE;

  const validate = (field, value) => {
    let message = "";
    switch (field) {
      case "fullName":
        if (!value.trim()) message = "Full name is required";
        break;
      case "company":
        if (!value.trim()) message = "Company name is required";
        break;
      case "email":
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value))
          message = "Please enter a valid email address";
        break;
      case "password":
        const pwdRegex =
          /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+{}\[\]:;<>,.?~\-]).{8,64}$/;
        if (!pwdRegex.test(value))
          message =
            "Password must be 8-64 chars and include upper, lower, number, and special";
        break;
      case "confirmPassword":
        if (value !== password) message = "Passwords do not match";
        break;
      default:
        break;
    }
    setErrors((prev) => ({ ...prev, [field]: message }));
    return !message;
  };

  const inputClass = (field, value) =>
    `w-full border px-3 py-2 rounded-md focus:outline-none focus:ring-2 ${
      errors[field]
        ? "border-red-500 focus:ring-red-500"
        : value
          ? "border-green-500 focus:ring-green-500"
          : "border-gray-300 focus:ring-blue-500"
    }`;

  const isSignupValid =
    fullName &&
    company &&
    email &&
    password &&
    confirmPassword &&
    !errors.fullName &&
    !errors.company &&
    !errors.email &&
    !errors.password &&
    !errors.confirmPassword;

  const isSigninValid = email && password && !errors.email;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isSignup && !isSignupValid) {
      validate("fullName", fullName);
      validate("company", company);
      validate("email", email);
      validate("password", password);
      validate("confirmPassword", confirmPassword);
      return;
    }
    try {
      const endpoint = isSignup ? "signup" : "signin";
      const payload = { email, password };
      if (isSignup) {
        payload.name = fullName;
        payload.company = company;
        if (role) payload.role = role;
      }
      const res = await fetch(`${API}/api/auth/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const data = await res.json();
        onSignIn({
          email,
          name: isSignup ? fullName : email,
          token: data.access_token,
          role: data.role,
        });
      }
    } catch (err) {
      console.error(`Sign ${isSignup ? "up" : "in"} failed`, err);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex flex-col">
      <header className="bg-white border-b border-blue-100 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center h-16 space-x-3">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
              <Database className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-xl text-gray-900">BizDetails AI</h1>
            <Badge
              variant="secondary"
              className="bg-purple-100 text-purple-700"
            >
              AI-Powered
            </Badge>
          </div>
        </div>
      </header>
      <main className="flex-1 flex items-center justify-center p-6">
        <div className="max-w-5xl w-full mx-auto grid md:grid-cols-2 gap-12 items-center">
          <div className="space-y-6">
            <div>
              <h1 className="text-4xl font-bold text-gray-900">
                BizDetails AI
              </h1>
              <p className="text-lg text-gray-700">
                Enriching Business Data with AI Precision
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <span className="px-3 py-1 bg-purple-100 text-purple-700 text-sm rounded-full">
                Beta Access
              </span>
              <span className="text-sm text-gray-600">
                Powered by Advanced AI
              </span>
            </div>
            <p className="text-gray-700">
              Enrich Your Business Data with AI Precision. Transform incomplete
              company data into comprehensive business intelligence. Map
              domains, validate details, and enrich your database with
              AI-powered accuracy.
            </p>
            <ul className="space-y-2 text-gray-700">
              <li>
                <strong>Precise Domain Mapping</strong> – AI-powered matching of
                company names to their verified business websites with 95%+
                accuracy
              </li>
              <li>
                <strong>Global Data Enrichment</strong> – Identify regional
                domains, subsidiaries, and international business presence
              </li>
              <li>
                <strong>Context-Aware Intelligence</strong> – Leverages
                industry, location, and company details for intelligent data
                enhancement
              </li>
              <li>
                <strong>Complete Business Profiles</strong> – Build
                comprehensive company profiles with verified domains and
                business details
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
            className="bg-white/90 backdrop-blur-sm p-8 rounded-xl shadow-lg w-full space-y-6 border border-gray-100"
          >
            <h2 className="text-2xl font-semibold text-center">
              {isSignup ? "Sign Up" : "Sign In"}
            </h2>
            {isSignup && (
              <>
                <input
                  type="text"
                  placeholder="Enter your full name"
                  className={inputClass("fullName", fullName)}
                  value={fullName}
                  onChange={(e) => {
                    setFullName(e.target.value);
                    validate("fullName", e.target.value);
                  }}
                />
                {errors.fullName && (
                  <p className="text-red-500 text-sm">{errors.fullName}</p>
                )}
                <input
                  type="text"
                  placeholder="Enter your company name"
                  className={inputClass("company", company)}
                  value={company}
                  onChange={(e) => {
                    setCompany(e.target.value);
                    validate("company", e.target.value);
                  }}
                />
                {errors.company && (
                  <p className="text-red-500 text-sm">{errors.company}</p>
                )}
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className={inputClass("role", role)}
                >
                  <option value="" disabled>
                    Select your role (Optional)
                  </option>
                  <option>Analyst</option>
                  <option>Marketing</option>
                  <option>Sales</option>
                  <option>Operations</option>
                  <option>Others</option>
                  <option value="superadmin">Superadmin</option>
                </select>
              </>
            )}
            <input
              type="email"
              placeholder="Enter your email address"
              className={inputClass("email", email)}
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                validate("email", e.target.value);
              }}
            />
            {errors.email && (
              <p className="text-red-500 text-sm">{errors.email}</p>
            )}
            <input
              type="password"
              placeholder="Enter your password"
              className={inputClass("password", password)}
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                if (isSignup) {
                  validate("password", e.target.value);
                  validate("confirmPassword", confirmPassword);
                }
              }}
            />
            {isSignup && errors.password && (
              <p className="text-red-500 text-sm">{errors.password}</p>
            )}
            {isSignup && (
              <>
                <input
                  type="password"
                  placeholder="Confirm your password"
                  className={inputClass("confirmPassword", confirmPassword)}
                  value={confirmPassword}
                  onChange={(e) => {
                    setConfirmPassword(e.target.value);
                    validate("confirmPassword", e.target.value);
                  }}
                />
                {errors.confirmPassword && (
                  <p className="text-red-500 text-sm">
                    {errors.confirmPassword}
                  </p>
                )}
              </>
            )}
            <Button
              type="submit"
              className="w-full disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isSignup ? !isSignupValid : !isSigninValid}
            >
              {isSignup ? "Sign Up" : "Sign In"}
            </Button>
            <div className="text-xs text-gray-500 text-center">
              GDPR & CCPA Compliant • Enterprise-Grade Security • No Credit Card
              Required
            </div>
            <div className="text-sm text-center">
              {isSignup ? (
                <>
                  Already have an account?{" "}
                  <button
                    type="button"
                    className="text-blue-600 underline"
                    onClick={() => {
                      setIsSignup(false);
                      setErrors({});
                    }}
                  >
                    Sign In
                  </button>
                </>
              ) : (
                <>
                  Need an account?{" "}
                  <button
                    type="button"
                    className="text-blue-600 underline"
                    onClick={() => {
                      setIsSignup(true);
                      setErrors({});
                    }}
                  >
                    Sign Up
                  </button>
                </>
              )}
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}
