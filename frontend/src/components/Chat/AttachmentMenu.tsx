import { useState, useRef, useEffect } from 'react';
import { Plus, Paperclip, Camera, Github, BookOpen, Blocks, Zap, Globe, Check } from 'lucide-react';
import { uploadFiles } from '../../lib/api';
import { toast } from 'sonner';
import { useNavigate } from 'react-router';

interface AttachmentMenuProps {
  deepResearch: boolean;
  setDeepResearch: (val: boolean) => void;
}

export function AttachmentMenu({ deepResearch, setDeepResearch }: AttachmentMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    
    setIsOpen(false);
    setIsUploading(true);
    
    try {
      const res = await uploadFiles(files);
      toast.success(`Successfully uploaded ${files.length} file(s) and ingested ${res.chunks_added} chunks into knowledge.`);
    } catch (err: any) {
      toast.error(err.message || 'Failed to upload files');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleStubClick = (featureName: string) => {
    setIsOpen(false);
    toast.info(`${featureName} is not yet implemented.`);
  };

  const handleNavigate = (path: string) => {
    setIsOpen(false);
    navigate(path);
  };

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isUploading}
        className="flex items-center justify-center p-2 rounded-full transition-colors cursor-pointer hover:bg-white/10 disabled:opacity-50"
        title="Attachments"
      >
        <Plus size={20} style={{ color: 'var(--color-text-secondary)' }} />
      </button>

      {isOpen && (
        <div
          className="absolute left-0 bottom-full mb-2 w-64 rounded-xl shadow-lg border overflow-hidden z-50"
          style={{
            background: 'var(--color-bg-secondary)',
            borderColor: 'var(--color-border)',
            boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
          }}
        >
          <div className="flex flex-col py-1">
            <button
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center gap-3 px-4 py-2 text-sm text-left hover:bg-white/5 transition-colors"
              style={{ color: 'var(--color-text)' }}
            >
              <Paperclip size={16} />
              <span>Add files or photos</span>
              <span className="ml-auto text-xs opacity-50">Ctrl+U</span>
            </button>
            <button
              onClick={() => handleStubClick('Take a screenshot')}
              className="flex items-center gap-3 px-4 py-2 text-sm text-left hover:bg-white/5 transition-colors"
              style={{ color: 'var(--color-text)' }}
            >
              <Camera size={16} />
              <span>Take a screenshot</span>
            </button>
            <button
              onClick={() => handleStubClick('Add from GitHub')}
              className="flex items-center gap-3 px-4 py-2 text-sm text-left hover:bg-white/5 transition-colors"
              style={{ color: 'var(--color-text)' }}
            >
              <Github size={16} />
              <span>Add from GitHub</span>
            </button>

            <div className="h-px my-1" style={{ background: 'var(--color-border)' }} />

            <button
              onClick={() => handleNavigate('/data-sources')}
              className="flex items-center justify-between px-4 py-2 text-sm text-left hover:bg-white/5 transition-colors"
              style={{ color: 'var(--color-text)' }}
            >
              <div className="flex items-center gap-3">
                <BookOpen size={16} />
                <span>Skills</span>
              </div>
              <span className="text-xs opacity-50">&gt;</span>
            </button>
            <button
              onClick={() => handleNavigate('/data-sources')}
              className="flex items-center justify-between px-4 py-2 text-sm text-left hover:bg-white/5 transition-colors"
              style={{ color: 'var(--color-text)' }}
            >
              <div className="flex items-center gap-3">
                <Blocks size={16} />
                <span>Add connector</span>
              </div>
              <span className="text-xs opacity-50">&gt;</span>
            </button>
            <button
              onClick={() => handleNavigate('/data-sources')}
              className="flex items-center justify-between px-4 py-2 text-sm text-left hover:bg-white/5 transition-colors"
              style={{ color: 'var(--color-text)' }}
            >
              <div className="flex items-center gap-3">
                <Zap size={16} />
                <span>Add plugins...</span>
              </div>
            </button>

            <div className="h-px my-1" style={{ background: 'var(--color-border)' }} />

            <button
              onClick={() => {
                setDeepResearch(!deepResearch);
                setIsOpen(false);
              }}
              className="flex items-center justify-between px-4 py-2 text-sm text-left hover:bg-white/5 transition-colors"
              style={{ color: 'var(--color-text)' }}
            >
              <div className="flex items-center gap-3">
                <Globe size={16} />
                <span>Web search</span>
              </div>
              {deepResearch && (
                <Check size={14} style={{ color: 'var(--color-accent)' }} />
              )}
            </button>
          </div>
        </div>
      )}

      {/* Hidden file input */}
      <input
        type="file"
        multiple
        ref={fileInputRef}
        onChange={handleFileUpload}
        style={{ display: 'none' }}
        accept=".txt,.md,.csv,.pdf,.docx"
      />
    </div>
  );
}

