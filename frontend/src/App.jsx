import React, { useState } from 'react';
import {
  Upload,
  Database,
  MessageCircle,
  BarChart3,
  FileText,
  Settings,
  User,
  LogOut,
} from 'lucide-react';
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

const API = import.meta.env.VITE_API_BASE;

export default function App() {
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState('upload');
  const [uploadStep, setUploadStep] = useState('upload');
  const [showChat, setShowChat] = useState(false);
  const [showCompliance, setShowCompliance] = useState(true);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [processedResults, setProcessedResults] = useState(null);

  const handleSignIn = ({ email, name, token }) => {
    setUser({ email, name, token });
  };

  const handleSignOut = () => {
    setUser(null);
    setActiveTab('upload');
    setUploadStep('upload');
    setUploadedFile(null);
    setProcessedResults(null);
  };

  const handleFileUploaded = (fileData) => {
    setUploadedFile(fileData);
    setUploadStep('mapping');
  };

  const handleColumnMappingComplete = async (mappedData) => {
    setUploadStep('processing');
    setTimeout(() => {
      setProcessedResults(generateMockResults(mappedData));
      setActiveTab('results');
      setUploadStep('upload');
    }, 2000);
  };

  const handleBackToUpload = () => {
    setUploadStep('upload');
    setUploadedFile(null);
  };

  const generateMockDomain = (companyName) => {
    const cleanName = companyName.toLowerCase().replace(/[^a-z0-9]/g, '');
    const domains = ['.com', '.io', '.co', '.net'];
    return `${cleanName}${domains[Math.floor(Math.random() * domains.length)]}`;
  };

  const generateMockResults = (data) =>
    data.map((row, index) => ({
      id: index + 1,
      companyName: row['Company Name'] || `Company ${index + 1}`,
      originalData: row,
      domain: generateMockDomain(row['Company Name'] || `Company ${index + 1}`),
      confidence: ['High', 'Medium', 'Low'][Math.floor(Math.random() * 3)],
      matchType: ['Exact', 'Contextual', 'Reverse', 'Manual'][Math.floor(Math.random() * 4)],
      notes: Math.random() > 0.7 ? 'Fuzzy match applied' : null,
      country: row.Country || 'US',
      industry: row.Industry || 'Technology',
    }));

  const getUploadTabContent = () => {
    switch (uploadStep) {
      case 'mapping':
        return (
          <ColumnMappingScreen
            uploadedFile={uploadedFile}
            onMappingComplete={handleColumnMappingComplete}
            onBack={handleBackToUpload}
          />
        );
      case 'processing':
        return (
          <div className="flex items-center justify-center py-24">
            <div className="text-center space-y-4">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto animate-pulse">
                <Database className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="text-xl mb-2">Processing Your Data</h3>
              <p className="text-gray-500">Mapping companies to domains using AI...</p>
            </div>
          </div>
        );
      case 'upload':
      default:
        return <UploadScreen onFileUploaded={handleFileUploaded} />;
    }
  };

  if (!user) {
    return <LandingPage onSignIn={handleSignIn} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {showCompliance && <ComplianceBanner onDismiss={() => setShowCompliance(false)} />}
      <header className="bg-white border-b border-blue-100 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <Database className="w-5 h-5 text-white" />
              </div>
              <h1 className="text-xl text-gray-900">BizDetails AI</h1>
              <Badge variant="secondary" className="bg-purple-100 text-purple-700">
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
                <Button variant="ghost" size="sm" onClick={handleSignOut} className="text-gray-500 hover:text-gray-700">
                  <LogOut className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-6">
          <div className={`flex-1 transition-all duration-300 ${showChat ? 'mr-80' : ''}`}>
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-3 mb-8">
                <TabsTrigger value="upload" className="flex items-center gap-2">
                  {uploadStep === 'mapping' ? <Settings className="w-4 h-4" /> : <Upload className="w-4 h-4" />}
                  {uploadStep === 'mapping' ? 'Column Mapping' : 'Data Enrichment (CSV Upload)'}
                </TabsTrigger>
                <TabsTrigger value="results" className="flex items-center gap-2">
                  <FileText className="w-4 h-4" />
                  Results
                </TabsTrigger>
                <TabsTrigger value="dashboard" className="flex items-center gap-2">
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
    </div>
  );
}
