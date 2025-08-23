import React, { useState, useEffect } from "react";
import {
  Upload,
  Database,
  MessageCircle,
  FileText,
  Settings,
  User,
  LogOut,
} from "lucide-react";
import { Button } from "./components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Badge } from "./components/ui/badge";
import { UploadScreen } from "./components/UploadScreen";
import { ColumnMappingScreen } from "./components/ColumnMappingScreen";
import { ResultsView } from "./components/ResultsView";
import { Dashboard } from "./components/Dashboard";
import { ChatPanel } from "./components/ChatPanel";
import { ComplianceBanner } from "./components/ComplianceBanner";
import { LandingPage } from "./components/LandingPage";

// Allow the app to work even if VITE_API_BASE isn't configured by falling back
// to relative URLs. This prevents "Failed to fetch" network errors when the
// environment variable is missing and the resulting URL would be invalid.
const API = import.meta.env.VITE_API_BASE || "";

export default function App() {
  const [user, setUser] = useState(null);
  const [authChecking, setAuthChecking] = useState(true);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [uploadStep, setUploadStep] = useState("upload");
  const [showChat, setShowChat] = useState(false);
  const [showCompliance, setShowCompliance] = useState(true);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [processedResults, setProcessedResults] = useState(null);
  const [progress, setProgress] = useState(0);

  const isTokenExpired = (token) => {
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      return payload.exp ? payload.exp * 1000 < Date.now() : false;
    } catch {
      return true;
    }
  };

  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      const parsed = JSON.parse(storedUser);
      if (!isTokenExpired(parsed.token)) {
        fetch(`${API}/api/auth/verify`, {
          headers: { Authorization: `Bearer ${parsed.token}` },
        })
          .then((res) => {
            if (res.ok) {
              setUser(parsed);
              const savedTab = localStorage.getItem("activeTab");
              if (savedTab) setActiveTab(savedTab);
            } else {
              localStorage.removeItem("user");
              localStorage.removeItem("activeTab");
            }
          })
          .catch(() => {
            localStorage.removeItem("user");
            localStorage.removeItem("activeTab");
          })
          .finally(() => setAuthChecking(false));
        return;
      } else {
        localStorage.removeItem("user");
        localStorage.removeItem("activeTab");
      }
    }
    setAuthChecking(false);
  }, []);

  useEffect(() => {
    if (user) {
      localStorage.setItem("activeTab", activeTab);
    }
  }, [activeTab, user]);

  const handleSignIn = ({ email, name, token }) => {
    const newUser = { email, name, token };
    setUser(newUser);
    localStorage.setItem("user", JSON.stringify(newUser));
  };

  const handleSignOut = () => {
    setUser(null);
    setActiveTab("dashboard");
    setUploadStep("upload");
    setUploadedFile(null);
    setProcessedResults(null);
    localStorage.removeItem("user");
    localStorage.removeItem("activeTab");
  };

  const handleFileUploaded = (fileData) => {
    setUploadedFile(fileData);
    setUploadStep("mapping");
  };

  const handleColumnMappingComplete = async (mappedData) => {
    setUploadStep("processing");
    setProgress(0);
    try {
      const res = await fetch(`${API}/api/process`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(user?.token ? { Authorization: `Bearer ${user.token}` } : {}),
        },
        body: JSON.stringify({ data: mappedData }),
      });
      if (!res.ok) {
        throw new Error("Failed to process data");
      }
      const { task_id } = await res.json();
      let done = false;
      const interval = setInterval(async () => {
        setProgress((p) => (p < 90 ? p + 10 : p));
        const statusRes = await fetch(`${API}/api/results/${task_id}/status`);
        const { status } = await statusRes.json();
        if (status === "completed") {
          clearInterval(interval);
          setProgress(100);
          const res2 = await fetch(`${API}/api/results?task_id=${task_id}`);
          if (!res2.ok) {
            throw new Error("Failed to fetch results");
          }
          const { results } = await res2.json();
          setProcessedResults(results);
          setActiveTab("results");
          setUploadStep("upload");
          done = true;
        }
      }, 500);
      // Safety timeout in case status never completes
      setTimeout(() => {
        if (!done) {
          clearInterval(interval);
          setProgress(100);
        }
      }, 10000);
    } catch (err) {
      console.error(err);
      alert(err.message || "An error occurred while processing your data.");
      setUploadStep("mapping");
    }
  };

  const handleBackToUpload = () => {
    setUploadStep("upload");
    setUploadedFile(null);
  };

  const getUploadTabContent = () => {
    switch (uploadStep) {
      case "mapping":
        return (
          <ColumnMappingScreen
            uploadedFile={uploadedFile}
            onMappingComplete={handleColumnMappingComplete}
            onBack={handleBackToUpload}
          />
        );
      case "processing":
        return (
          <div className="flex flex-col items-center justify-center py-24 space-y-4">
            <div className="w-64 bg-gray-800 h-2 rounded">
              <div
                className="h-full bg-green-500 transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-green-400">{progress}%</p>
          </div>
        );
      default:
        return <UploadScreen onFileUploaded={handleFileUploaded} />;
    }
  };

  if (authChecking) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!user) {
    return <LandingPage onSignIn={handleSignIn} />;
  }

  return (
    <div className="min-h-screen bg-black text-green-400 font-mono">
      {showCompliance && (
        <ComplianceBanner onDismiss={() => setShowCompliance(false)} />
      )}
      <header className="bg-gray-900 border-b border-green-500 shadow-sm">
        <div className="max-w-7xl 2xl:max-w-none mx-auto px-4 sm:px-6 lg:px-8 2xl:px-16">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-blue-500 rounded-lg flex items-center justify-center">
                <Database className="w-5 h-5 text-black" />
              </div>
              <h1 className="text-xl">BizDetails AI</h1>
              <Badge variant="secondary" className="bg-gray-800 text-green-400">
                AI-Powered
              </Badge>
            </div>
            <div className="flex items-center gap-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowChat(!showChat)}
                className="flex items-center gap-2 border-green-500 text-green-400"
              >
                <MessageCircle className="w-4 h-4" />
                AI Assistant
              </Button>
              <div className="flex items-center gap-2">
                <User className="w-4 h-4" />
                <span className="text-sm">{user.name}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleSignOut}
                  className="text-green-400 hover:text-green-200"
                >
                  <LogOut className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl 2xl:max-w-none mx-auto px-4 sm:px-6 lg:px-8 2xl:px-16 py-8">
        <div className="flex flex-col lg:flex-row gap-6">
          <div className="flex-1 transition-all duration-300">
            <Tabs
              value={activeTab}
              onValueChange={setActiveTab}
              className="w-full"
            >
              <TabsList className="grid w-full grid-cols-1 sm:grid-cols-3 mb-8">
                <TabsTrigger
                  value="dashboard"
                  className="flex items-center gap-2"
                >
                  <Database className="w-4 h-4" />
                  Company Data
                </TabsTrigger>
                <TabsTrigger value="upload" className="flex items-center gap-2">
                  {uploadStep === "mapping" ? (
                    <Settings className="w-4 h-4" />
                  ) : (
                    <Upload className="w-4 h-4" />
                  )}
                  {uploadStep === "mapping"
                    ? "Column Mapping"
                    : "Data Enrichment (CSV Upload)"}
                </TabsTrigger>
                <TabsTrigger
                  value="results"
                  className="flex items-center gap-2"
                >
                  <FileText className="w-4 h-4" />
                  Results
                </TabsTrigger>
              </TabsList>
              <TabsContent value="dashboard" className="space-y-6">
                <Dashboard />
              </TabsContent>
              <TabsContent value="upload" className="space-y-6">
                {getUploadTabContent()}
              </TabsContent>
              <TabsContent value="results" className="space-y-6">
                <ResultsView results={processedResults} />
              </TabsContent>
            </Tabs>
          </div>

          {showChat && (
            <div className="fixed inset-0 w-full z-50 sm:inset-auto sm:right-6 sm:top-24 sm:bottom-6 sm:w-80">
              <ChatPanel onClose={() => setShowChat(false)} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
