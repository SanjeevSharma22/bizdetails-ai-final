import React, { useState } from "react";
import {
  Upload,
  Database,
  MessageCircle,
  BarChart3,
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

export default function App() {
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState("upload");
  const [uploadStep, setUploadStep] = useState("upload");
import React, { useState } from 'react';
import { Upload, Database, MessageCircle, BarChart3, FileText, Settings, User, LogOut } from 'lucide-react';
import { Button } from './components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Badge } from './components/ui/badge';
import { UploadScreen } from './components/UploadScreen';
import { ColumnMappingScreen } from './components/ColumnMappingScreen';
import { ResultsView } from './components/ResultsView';
import { Dashboard } from './components/Dashboard';
import { ChatPanel } from './components/ChatPanel';
import { ComplianceBanner } from './components/ComplianceBanner';
import { LandingPage } from './components/LandingPage';

export default function App() {
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState('upload');
  const [uploadStep, setUploadStep] = useState('upload');
 main
  const [showChat, setShowChat] = useState(false);
  const [showCompliance, setShowCompliance] = useState(true);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [processedResults, setProcessedResults] = useState(null);

  const handleSignIn = (email, name) => {
    setUser({ email, name });
  };

  const handleSignOut = () => {
    setUser(null);
    setActiveTab("upload");
    setUploadStep("upload");
    setActiveTab('upload');
    setUploadStep('upload');
 main
    setUploadedFile(null);
    setProcessedResults(null);
  };

  const handleFileUploaded = (fileData) => {
    setUploadedFile(fileData);
    setUploadStep("mapping");
  };

  const handleColumnMappingComplete = (mappedData) => {
    setUploadStep("processing");
    setTimeout(() => {
      setProcessedResults(generateMockResults(mappedData));
      setActiveTab("results");
      setUploadStep("upload");
    setUploadStep('mapping');
  };

  const handleColumnMappingComplete = (mappedData) => {
    setUploadStep('processing');
    setTimeout(() => {
      setProcessedResults(generateMockResults(mappedData));
      setActiveTab('results');
      setUploadStep('upload');
 main
    }, 2000);
  };

  const handleBackToUpload = () => {
    setUploadStep("upload");
    setUploadStep('upload');
 main
    setUploadedFile(null);
  };

  const generateMockResults = (data) => {
    return data.map((row, index) => ({
      id: index + 1,
      companyName: row["Company Name"] || `Company ${index + 1}`,
      originalData: row,
      domain: generateMockDomain(row["Company Name"] || `Company ${index + 1}`),
      confidence: ["High", "Medium", "Low"][Math.floor(Math.random() * 3)],
      matchType: ["Exact", "Contextual", "Reverse", "Manual"][
        Math.floor(Math.random() * 4)
      ],
      notes: Math.random() > 0.7 ? "Fuzzy match applied" : null,
      country: row.Country || "US",
      industry: row.Industry || "Technology",
      companyName: row['Company Name'] || `Company ${index + 1}`,
      originalData: row,
      domain: generateMockDomain(row['Company Name'] || `Company ${index + 1}`),
      confidence: ['High', 'Medium', 'Low'][Math.floor(Math.random() * 3)],
      matchType: ['Exact', 'Contextual', 'Reverse', 'Manual'][Math.floor(Math.random() * 4)],
      notes: Math.random() > 0.7 ? 'Fuzzy match applied' : null,
      country: row.Country || 'US',
      industry: row.Industry || 'Technology'
 main
    }));
  };

  const generateMockDomain = (companyName) => {
    const cleanName = companyName.toLowerCase().replace(/[^a-z0-9]/g, "");
    const domains = [".com", ".io", ".co", ".net"];
    const cleanName = companyName.toLowerCase().replace(/[^a-z0-9]/g, '');
    const domains = ['.com', '.io', '.co', '.net'];
\ main
    return `${cleanName}${domains[Math.floor(Math.random() * domains.length)]}`;
  };

  const getUploadTabContent = () => {
    switch (uploadStep) {
      case "upload":
        return <UploadScreen onFileUploaded={handleFileUploaded} />;
      case "mapping":
      case 'upload':
        return <UploadScreen onFileUploaded={handleFileUploaded} />;
      case 'mapping':
 main
        return (
          <ColumnMappingScreen
            uploadedFile={uploadedFile}
            onMappingComplete={handleColumnMappingComplete}
            onBack={handleBackToUpload}
          />
        );
      case "processing":
      case 'processing':
 main
        return (
          <div className="flex items-center justify-center py-24">
            <div className="text-center space-y-4">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto animate-pulse">
                <Database className="w-8 h-8 text-blue-600" />
              </div>
              <div>
                <h3 className="text-xl mb-2">Processing Your Data</h3>
                <p className="text-gray-500">
                  Mapping companies to domains using AI...
                </p>
                <p className="text-gray-500">Mapping companies to domains using AI...</p>
 main
              </div>
            </div>
          </div>
        );
      default:
        return <UploadScreen onFileUploaded={handleFileUploaded} />;
    }
  };

  if (!user) {
    return <LandingPage onSignIn={handleSignIn} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {showCompliance && (
        <ComplianceBanner onDismiss={() => setShowCompliance(false)} />
      )}

      <header className="bg-white border-b border-blue-100 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <Database className="w-5 h-5 text-white" />
              </div>
              <h1 className="text-xl text-gray-900">BizDetails AI</h1>
              <Badge
                variant="secondary"
                className="bg-purple-100 text-purple-700"
              >
              <Badge variant="secondary" className="bg-purple-100 text-purple-700">
 main
                AI-Powered
              </Badge>
            </div>
            <div className="flex items-center gap-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowChat(!showChat)}
                className="flex items-center gap-2"
              >
                <MessageCircle className="w-4 h-4" />
                AI Assistant
              </Button>
              <div className="flex items-center gap-2">
                <User className="w-4 h-4 text-gray-500" />
                <span className="text-sm text-gray-700">{user.name}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleSignOut}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <LogOut className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-6">
          <div
            className={`flex-1 transition-all duration-300 ${showChat ? "mr-80" : ""}`}
          >
            <Tabs
              value={activeTab}
              onValueChange={setActiveTab}
              className="w-full"
            >
              <TabsList className="grid w-full grid-cols-3 mb-8">
                <TabsTrigger value="upload" className="flex items-center gap-2">
                  {uploadStep === "mapping" ? (

          <div className={`flex-1 transition-all duration-300 ${showChat ? 'mr-80' : ''}`}>
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-3 mb-8">
                <TabsTrigger value="upload" className="flex items-center gap-2">
                  {uploadStep === 'mapping' ? (
 main
                    <Settings className="w-4 h-4" />
                  ) : (
                    <Upload className="w-4 h-4" />
                  )}
                  {uploadStep === "mapping" ? "Column Mapping" : "Upload & Map"}
                </TabsTrigger>
                <TabsTrigger
                  value="results"
                  className="flex items-center gap-2"
                >
                  <FileText className="w-4 h-4" />
                  Results
                </TabsTrigger>
                <TabsTrigger
                  value="dashboard"
                  className="flex items-center gap-2"
                >

                  {uploadStep === 'mapping' ? 'Column Mapping' : 'Upload & Map'}
                </TabsTrigger>
                <TabsTrigger value="results" className="flex items-center gap-2">
                  <FileText className="w-4 h-4" />
                  Results
                </TabsTrigger>
                <TabsTrigger value="dashboard" className="flex items-center gap-2">
 main
                  <BarChart3 className="w-4 h-4" />
                  Dashboard
                </TabsTrigger>
              </TabsList>

              <TabsContent value="upload" className="space-y-6">
                {getUploadTabContent()}
              </TabsContent>

              <TabsContent value="results" className="space-y-6">
                <ResultsView results={processedResults} />
              </TabsContent>

              <TabsContent value="dashboard" className="space-y-6">
                <Dashboard />
              </TabsContent>
            </Tabs>
          </div>

          {showChat && (
            <div className="fixed right-6 top-24 bottom-6 w-80">
              <ChatPanel onClose={() => setShowChat(false)} />
            </div>
          )}
        </div>
      </div>


import React from 'react';

export default function App() {
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold">BizDetails AI</h1>
      <p>Frontend scaffold not yet implemented.</p>
 main
    </div>
  );
}
