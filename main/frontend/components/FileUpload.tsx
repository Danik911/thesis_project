import { useState, useRef } from 'react';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  isUploading: boolean;
}

export default function FileUpload({ onFileSelect, isUploading }: FileUploadProps) {
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith('.md')) {
        onFileSelect(file);
      } else {
        alert("Please upload a Markdown (.md) file.");
      }
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0]);
    }
  };

  const onButtonClick = () => {
    inputRef.current?.click();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      if (!isUploading) {
        onButtonClick();
      }
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div 
        role="button"
        tabIndex={0}
        className={`relative flex flex-col items-center justify-center w-full h-64 border-2 border-dashed rounded-xl transition-all duration-300 ease-in-out outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-900
          ${dragActive 
            ? "border-blue-500 bg-blue-500/10 shadow-[0_0_20px_rgba(59,130,246,0.3)]" 
            : "border-slate-600 bg-slate-800/50 hover:border-blue-400/50 hover:bg-slate-800/80"
          }
          ${isUploading ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}
        `}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={!isUploading ? onButtonClick : undefined}
        onKeyDown={handleKeyDown}
      >
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          accept=".md"
          onChange={handleChange}
          disabled={isUploading}
        />

        <div className="flex flex-col items-center justify-center pt-5 pb-6 text-center px-4">
          <div className={`mb-4 p-4 rounded-full bg-slate-700/50 transition-transform duration-300 ${dragActive ? 'scale-110 bg-blue-500/20' : ''}`}>
            <svg className={`w-10 h-10 ${dragActive ? 'text-blue-400' : 'text-slate-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </div>
          
          <p className="mb-2 text-lg font-medium text-slate-200">
            <span className="text-blue-400">Click to upload</span> or drag and drop
          </p>
          <p className="text-sm text-slate-400">
            User Requirement Specification (URS) files (.md)
          </p>
          
          <div className="mt-6 flex items-center gap-2 text-xs text-slate-500 bg-slate-900/50 px-3 py-1.5 rounded-full border border-slate-700">
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            Secure & Encrypted Upload
          </div>
        </div>
      </div>
    </div>
  );
}
