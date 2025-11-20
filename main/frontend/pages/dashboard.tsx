import { useState, useEffect, useRef } from 'react';
import { useUser, useAuth } from '@clerk/nextjs';
import Layout from '@/components/Layout';
import Head from 'next/head';
import FileUpload from '@/components/FileUpload';
import JobProgress from '@/components/JobProgress';
import ComplianceDashboard from '@/components/ComplianceDashboard';

type JobStatus = 'IDLE' | 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';

export default function Dashboard() {
  const { user, isLoaded } = useUser();
  const { getToken } = useAuth();
  const [status, setStatus] = useState<JobStatus>('IDLE');
  const [jobId, setJobId] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [results, setResults] = useState<any>(null);
  const [jobs, setJobs] = useState<any[]>([]);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Derive display name
  const displayName = user?.fullName ??
    user?.firstName ??
    user?.primaryEmailAddress?.emailAddress ??
    'User';

  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const fetchJobs = async () => {
    if (!isLoaded || !user) return;
    try {
      const token = await getToken();
      const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8080';
      const response = await fetch(`${apiUrl}/jobs`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setJobs(data);
      }
    } catch (error) {
      console.error("Failed to fetch jobs:", error);
    }
  };

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  useEffect(() => {
    fetchJobs();
  }, [isLoaded, user]);

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
  };

  const handleGenerate = async () => {
    if (!selectedFile) return;
    
    setStatus('PENDING');
    setLogs(['Initializing upload...', 'Validating file format...', 'Checking GAMP-5 compliance requirements...']);
    
    try {
      const token = await getToken();
      const formData = new FormData();
      formData.append('file', selectedFile);

      const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8080';
      
      setLogs(prev => [...prev, `Connecting to secure API at ${apiUrl}...`]);

      const response = await fetch(`${apiUrl}/jobs`, { 
        method: 'POST', 
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData 
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `API Error: ${response.statusText}`);
      }

      const data = await response.json();
      setJobId(data.job_id);
      setStatus('PROCESSING');
      setLogs(prev => [...prev, `Job submitted successfully (ID: ${data.job_id}). Starting processing...`]);
      
      // Start polling
      pollJobStatus(data.job_id, token, apiUrl);

    } catch (error) {
      console.error('Upload failed:', error);
      setStatus('FAILED');
      setLogs(prev => [...prev, `ERROR: ${error instanceof Error ? error.message : 'Upload failed'}`]);
    }
  };

  const pollJobStatus = (id: string, token: string | null, apiUrl: string) => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);

    pollIntervalRef.current = setInterval(async () => {
      try {
        const response = await fetch(`${apiUrl}/jobs/${id}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (!response.ok) {
           throw new Error(`Polling error: ${response.statusText}`);
        }

        const data = await response.json();
        
        if (data.status === 'COMPLETED') {
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
          
          setLogs(prev => [...prev, 'Job completed. Retrieving results...']);
          
          // Fetch the JSON result for dashboard
          try {
            const resultResponse = await fetch(`${apiUrl}/jobs/${id}/result`, {
              headers: { 'Authorization': `Bearer ${token}` }
            });
            if (resultResponse.ok) {
              const resultData = await resultResponse.json();
              setResults(resultData);
              setStatus('COMPLETED');
              setLogs(prev => [...prev, 'Results retrieved successfully.']);
              fetchJobs(); // Refresh history
            } else {
              throw new Error('Failed to retrieve results');
            }
          } catch (err) {
            console.error("Error fetching results:", err);
            setStatus('FAILED');
            setLogs(prev => [...prev, 'ERROR: Failed to retrieve result data.']);
          }

        } else if (data.status === 'FAILED') {
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
          setStatus('FAILED');
          setLogs(prev => [...prev, `Job failed: ${data.error_message || 'Unknown error'}`]);
        } else {
          // Still processing
          // We can add "heartbeat" logs occasionally or just wait
          // setLogs(prev => [...prev, `Processing... (${new Date().toLocaleTimeString()})`]);
        }

      } catch (e) {
        console.error("Polling failed:", e);
        // Don't fail immediately on one polling error, but maybe log it
      }
    }, 2000);
  };

  const handleDownload = async () => {
    if (!jobId) return;
    const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8080';
    const url = `${apiUrl}/jobs/${jobId}/download`;
    
    try {
      const token = await getToken();
      const response = await fetch(url, {
          headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Download failed');
      
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `test_suite_${jobId}.yaml`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(downloadUrl);
      document.body.removeChild(a);
    } catch (e) {
        console.error("Download error:", e);
        alert("Failed to download file");
    }
  };

  const handleHistoryDownload = async (job: any) => {
    const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8080';
    const url = `${apiUrl}/jobs/${job.job_id}/download`;
    
    try {
      const token = await getToken();
      const response = await fetch(url, {
          headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Download failed');
      
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `test_suite_${job.job_id}.yaml`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(downloadUrl);
      document.body.removeChild(a);
    } catch (e) {
        console.error("Download error:", e);
        alert("Failed to download file");
    }
  };

  const resetDashboard = () => {
    setStatus('IDLE');
    setJobId(null);
    setLogs([]);
    setResults(null);
    setSelectedFile(null);
  };

  if (!isLoaded) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="animate-pulse flex flex-col items-center">
            <div className="h-12 w-12 bg-blue-600/20 rounded-full mb-4 animate-ping"></div>
            <div className="text-slate-400">Loading secure environment...</div>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <>
      <Head>
        <title>Dashboard - PharmaGen AI</title>
        <meta name="description" content="GAMP-5 compliant pharmaceutical test generation dashboard" />
      </Head>
      <Layout>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
          
          {/* Welcome Section */}
          <div className="flex justify-between items-end">
            <div>
              <h1 className="text-3xl font-bold text-white">
                Welcome, <span className="text-blue-400">{displayName}</span>
              </h1>
              <p className="mt-2 text-slate-400">
                Manage your pharmaceutical test generation workflows
              </p>
            </div>
            {status !== 'IDLE' && (
              <button 
                onClick={resetDashboard}
                className="text-sm text-slate-400 hover:text-white transition-colors flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Start New Job
              </button>
            )}
          </div>

          {/* Main Content Area */}
          <div className="min-h-[500px]">
            {status === 'IDLE' && (
              <div className="animate-fade-in space-y-8">
                {!selectedFile ? (
                  <FileUpload onFileSelect={handleFileSelect} isUploading={false} />
                ) : (
                  <div className="max-w-2xl mx-auto">
                    <div className="bg-slate-800/50 border border-blue-500/30 rounded-xl p-8 text-center space-y-6">
                      <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto">
                        <svg className="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </div>
                      <div>
                        <h3 className="text-xl font-medium text-white mb-2">Ready to Generate</h3>
                        <p className="text-slate-400">
                          Selected file: <span className="text-blue-400 font-mono">{selectedFile.name}</span>
                        </p>
                        <p className="text-xs text-slate-500 mt-2">
                          {(selectedFile.size / 1024).toFixed(2)} KB
                        </p>
                      </div>
                      
                      <div className="flex gap-4 justify-center">
                        <button 
                          onClick={() => setSelectedFile(null)}
                          className="px-6 py-3 rounded-lg border border-slate-600 text-slate-300 hover:bg-slate-800 transition-colors"
                        >
                          Cancel
                        </button>
                        <button 
                          onClick={handleGenerate}
                          className="btn-primary flex items-center gap-2"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                          </svg>
                          Generate Test Suite
                        </button>
                      </div>
                    </div>
                  </div>
                )}
                
                <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
                  <FeatureCard 
                    title="GAMP-5 Compliant" 
                    description="Automated categorization and validation logic aligned with ISPE GAMP 5 guidelines."
                    icon="shield"
                  />
                  <FeatureCard 
                    title="AI-Powered Analysis" 
                    description="Advanced LLM processing to extract requirements and generate precise test cases."
                    icon="chip"
                  />
                  <FeatureCard 
                    title="Audit Ready" 
                    description="Full ALCOA+ traceability with immutable logs and user attribution."
                    icon="document"
                  />
                </div>
              </div>
            )}

            {(status === 'PENDING' || status === 'PROCESSING') && (
              <div className="animate-fade-in">
                <JobProgress status={status} logs={logs} />
              </div>
            )}

            {status === 'COMPLETED' && results && (
              <ComplianceDashboard results={results} onDownload={handleDownload} />
            )}

            {status === 'FAILED' && (
              <div className="text-center py-12 animate-fade-in">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-500/10 mb-4">
                  <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-xl font-medium text-white mb-2">Generation Failed</h3>
                <p className="text-slate-400 mb-6">An error occurred while processing your request.</p>
                <button onClick={resetDashboard} className="btn-primary">Try Again</button>
                
                <div className="mt-8 max-w-2xl mx-auto text-left">
                  <div className="bg-slate-900/50 rounded-lg p-4 border border-red-500/20 font-mono text-sm text-red-400">
                    {logs[logs.length - 1]}
                  </div>
                </div>
              </div>
            )}

            {/* History Section */}
            <div className="mt-12 border-t border-slate-800 pt-8">
              <h2 className="text-2xl font-bold text-white mb-6">Recent Workflows</h2>
              <div className="bg-slate-800/50 rounded-xl overflow-hidden border border-slate-700">
                 {jobs.length === 0 ? (
                   <div className="p-8 text-center text-slate-400">No history available.</div>
                 ) : (
                   <table className="w-full text-left text-sm text-slate-400">
                     <thead className="bg-slate-900/50 text-slate-200 uppercase font-mono text-xs">
                       <tr>
                         <th className="px-6 py-4">Job ID</th>
                         <th className="px-6 py-4">File</th>
                         <th className="px-6 py-4">Status</th>
                         <th className="px-6 py-4">Date</th>
                         <th className="px-6 py-4">Actions</th>
                       </tr>
                     </thead>
                     <tbody className="divide-y divide-slate-700">
                       {jobs.map(job => (
                         <tr key={job.job_id} className="hover:bg-slate-700/30 transition-colors">
                           <td className="px-6 py-4 font-mono text-xs">{job.job_id.substring(0, 8)}...</td>
                           <td className="px-6 py-4">{job.urs_filename}</td>
                           <td className="px-6 py-4">
                             <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                               job.status === 'COMPLETED' ? 'bg-emerald-500/10 text-emerald-400' :
                               job.status === 'FAILED' ? 'bg-red-500/10 text-red-400' :
                               'bg-blue-500/10 text-blue-400'
                             }`}>
                               {job.status}
                             </span>
                           </td>
                           <td className="px-6 py-4">{new Date(job.created_at).toLocaleDateString()} {new Date(job.created_at).toLocaleTimeString()}</td>
                           <td className="px-6 py-4">
                             {job.status === 'COMPLETED' && (
                               <button 
                                 onClick={() => handleHistoryDownload(job)}
                                 className="text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1"
                               >
                                 <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                 </svg>
                                 Download
                               </button>
                             )}
                           </td>
                         </tr>
                       ))}
                     </tbody>
                   </table>
                 )}
              </div>
            </div>
          </div>
        </div>
      </Layout>
    </>
  );
}

function FeatureCard({ title, description, icon }: { title: string, description: string, icon: string }) {
  return (
    <div className="card hover:bg-slate-800/80 transition-colors group">
      <div className="w-12 h-12 bg-blue-500/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-blue-500/20 transition-colors">
        {icon === 'shield' && (
          <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        )}
        {icon === 'chip' && (
          <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
        )}
        {icon === 'document' && (
          <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        )}
      </div>
      <h3 className="text-lg font-medium text-white mb-2">{title}</h3>
      <p className="text-slate-400 text-sm">{description}</p>
    </div>
  );
}
