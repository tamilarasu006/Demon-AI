import React, { useState, useEffect, useRef } from 'react';
import { Mail, KeyRound, User, Github, Command, Check, X, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router';
import { registerUser, loginUser, forgotPassword, verifyOtp, getBase } from '../lib/api';

// OpenDemon - an autonomous, self-hosted AI agent framework for complex reasoning and workflow automation.

type FlowState = 'login' | 'register' | 'forgot' | 'otp';

interface StatusMessage {
  text: string;
  type: 'idle' | 'active' | 'success' | 'error';
}

export function AuthFlow() {
  const navigate = useNavigate();
  const [flow, setFlow] = useState<FlowState>('login');
  const [focusedField, setFocusedField] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Form states
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  
  // Refs for OTP auto-advance
  const otpRefs = useRef<(HTMLInputElement | null)[]>([]);

  // Derived state for live feedback
  const getPasswordStrength = (pass: string) => {
    if (!pass) return 0;
    let strength = 0;
    if (pass.length >= 8) strength += 25;
    if (/[A-Z]/.test(pass)) strength += 25;
    if (/[0-9]/.test(pass)) strength += 25;
    if (/[^A-Za-z0-9]/.test(pass)) strength += 25;
    return strength;
  };

  const getEmailStatus = (email: string): StatusMessage => {
    if (!email && focusedField !== 'email') return { text: 'ready for input', type: 'idle' };
    if (!email) return { text: 'awaiting signal...', type: 'active' };
    if (!email.includes('@')) return { text: 'malformed address structure', type: 'error' };
    return { text: 'address format verified', type: 'success' };
  };

  const getPasswordStatus = (pass: string, isRegister: boolean): StatusMessage => {
    if (!pass && focusedField !== 'password') return { text: 'encrypted channel closed', type: 'idle' };
    if (!pass) return { text: 'initializing handshake...', type: 'active' };
    
    if (isRegister) {
      const strength = getPasswordStrength(pass);
      if (strength < 50) return { text: 'encryption key too weak', type: 'error' };
      if (strength < 100) return { text: 'key strength acceptable', type: 'active' };
      return { text: 'key strength optimal', type: 'success' };
    }
    
    return { text: 'key received, awaiting authorization', type: 'active' };
  };

  const handleOtpChange = (index: number, value: string) => {
    if (value.length > 1) value = value[value.length - 1]; // Only take last char
    if (!/^[0-9]*$/.test(value)) return; // Only numbers

    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);

    // Auto-advance
    if (value && index < 5) {
      otpRefs.current[index + 1]?.focus();
    }
  };

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      otpRefs.current[index - 1]?.focus();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    try {
      if (flow === 'register') {
        await registerUser({ name, email, password });
        setFlow('login');
        setErrorMsg('Operative deployed. Please initiate connection.');
      } else if (flow === 'login') {
        await loginUser({ email, password });
        navigate('/'); // Redirect to main app
      } else if (flow === 'forgot') {
        await forgotPassword(email);
        setFlow('otp');
      } else if (flow === 'otp') {
        await verifyOtp(otp.join(''));
        setFlow('login');
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Transmission failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-screen max-h-screen w-full flex flex-col md:flex-row font-sans overflow-hidden" style={{ backgroundColor: '#0B0E14', color: '#E8EDF4' }}>
      
      {/* 55% Left Panel - Signal Board */}
      <div className="hidden md:flex md:w-[55%] relative overflow-hidden flex-col justify-between p-12 border-r border-[#1F2733]">
        {/* Dynamic Trace Background */}
        <div className="absolute inset-0 z-0 opacity-40 mix-blend-screen pointer-events-none transition-all duration-700 ease-out">
           <svg width="100%" height="100%" className="opacity-30">
              <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1F2733" strokeWidth="1"/>
              </pattern>
              <rect width="100%" height="100%" fill="url(#grid)" />
           </svg>
           {/* Active Trace Line indicating Focus */}
           {focusedField && (
             <div className="absolute left-0 top-1/2 w-full h-[1px] bg-[#00E5FF] shadow-[0_0_8px_#00E5FF] transition-all duration-500 transform -translate-y-1/2">
                <div className="absolute right-0 top-1/2 w-2 h-2 rounded-full bg-[#00E5FF] transform -translate-y-1/2 shadow-[0_0_12px_#00E5FF] animate-pulse" />
             </div>
           )}
        </div>

        <div className="z-10 mt-12">
          <h1 className="text-5xl font-bold tracking-tight text-[#E8EDF4]" style={{ fontFamily: '"Chakra Petch", sans-serif' }}>
            OpenDemon
          </h1>
          <p className="mt-4 max-w-md text-lg text-[#7C8798] leading-relaxed">
            Autonomous agent infrastructure for complex reasoning and workflow automation.
          </p>
        </div>

        <div className="z-10 font-mono text-xs text-[#7C8798] tracking-widest uppercase flex items-center gap-4">
          <span className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#39FF88] shadow-[0_0_8px_#39FF88]" />
            Systems Nominal
          </span>
          <span>v2.4.1_b</span>
        </div>
      </div>

      {/* Mobile Header (replaces 55% panel) */}
      <div className="md:hidden flex flex-col p-6 border-b border-[#1F2733] relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-[2px] bg-[#00E5FF] shadow-[0_0_8px_#00E5FF] animate-pulse" />
        <h1 className="text-3xl font-bold text-[#E8EDF4]" style={{ fontFamily: '"Chakra Petch", sans-serif' }}>
          OpenDemon
        </h1>
      </div>

      {/* 45% Right Panel - Form Area */}
      <div className="flex-1 flex flex-col p-8 md:p-16 lg:p-24 bg-[#121722] overflow-y-auto min-h-0 h-full">
        <div className="max-w-md w-full mx-auto my-auto space-y-10 py-4">
          
          <div className="space-y-2">
            <h2 className="text-3xl font-semibold" style={{ fontFamily: '"Chakra Petch", sans-serif' }}>
              {flow === 'login' && 'Establish Connection'}
              {flow === 'register' && 'Initialize Operative'}
              {flow === 'forgot' && 'Reset Sequence'}
              {flow === 'otp' && 'Verify Identity'}
            </h2>
            <p className="text-[#7C8798]">
              {flow === 'login' && "Enter your credentials to access the control plane."}
              {flow === 'register' && "Create a new authorization profile."}
              {flow === 'forgot' && "Provide the transmission address to receive a recovery signal."}
              {flow === 'otp' && "Enter the 6-digit transmission code sent to your terminal."}
            </p>
          </div>

          {/* TOP TABS */}
          {['login', 'register'].includes(flow) && (
            <div className="flex border-b border-[#1F2733]/50">
              <button
                type="button"
                onClick={() => setFlow('login')}
                className={`flex-1 pb-3 text-sm font-mono uppercase tracking-wide transition-colors relative ${flow === 'login' ? 'text-[#00E5FF]' : 'text-[#7C8798] hover:text-[#E8EDF4]'}`}
              >
                Login
                {flow === 'login' && <div className="absolute bottom-[-1px] left-0 w-full h-[2px] bg-[#00E5FF] shadow-[0_0_8px_#00E5FF]" />}
              </button>
              <button
                type="button"
                onClick={() => setFlow('register')}
                className={`flex-1 pb-3 text-sm font-mono uppercase tracking-wide transition-colors relative ${flow === 'register' ? 'text-[#00E5FF]' : 'text-[#7C8798] hover:text-[#E8EDF4]'}`}
              >
                Register
                {flow === 'register' && <div className="absolute bottom-[-1px] left-0 w-full h-[2px] bg-[#00E5FF] shadow-[0_0_8px_#00E5FF]" />}
              </button>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            
            {errorMsg && (
              <div className="text-xs font-mono text-[#FF3D8A] bg-[#FF3D8A]/10 border border-[#FF3D8A]/20 rounded-[4px] p-3 flex items-start gap-2">
                <X size={14} className="shrink-0 mt-0.5" />
                <span>{errorMsg}</span>
              </div>
            )}

            {/* REGISTER FIELDS */}
            {flow === 'register' && (
              <div className="space-y-2">
                <label className="text-xs font-mono uppercase tracking-wider text-[#7C8798]">Operative ID (Name)</label>
                <div className="relative group">
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    onFocus={() => setFocusedField('name')}
                    onBlur={() => setFocusedField(null)}
                    className="w-full bg-[#0B0E14] border border-[#1F2733] rounded-[4px] px-4 py-3 text-[#E8EDF4] font-mono focus:outline-none focus:border-[#00E5FF] transition-colors"
                    placeholder="e.g. John Doe"
                  />
                  {focusedField === 'name' && <div className="absolute top-0 left-0 h-full w-[2px] bg-[#00E5FF] animate-scanline" />}
                </div>
              </div>
            )}

            {/* EMAIL / IDENTIFIER (Used in login, register, forgot) */}
            {['login', 'register', 'forgot'].includes(flow) && (
              <div className="space-y-2">
                <label className="text-xs font-mono uppercase tracking-wider text-[#7C8798]">Transmission Address</label>
                <div className="relative group">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <Mail size={16} className={focusedField === 'email' ? 'text-[#00E5FF]' : 'text-[#7C8798]'} />
                  </div>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    onFocus={() => setFocusedField('email')}
                    onBlur={() => setFocusedField(null)}
                    className="w-full bg-[#0B0E14] border border-[#1F2733] rounded-[4px] pl-11 pr-4 py-3 text-[#E8EDF4] font-mono focus:outline-none focus:border-[#00E5FF] transition-colors"
                    placeholder="user@domain.com"
                  />
                  {focusedField === 'email' && <div className="absolute top-0 left-0 h-full w-[2px] bg-[#00E5FF] shadow-[0_0_8px_#00E5FF] overflow-hidden"><div className="w-full h-[20%] bg-white absolute top-[-20%] animate-scan-vertical mix-blend-overlay" /></div>}
                </div>
                {/* Live Status Line */}
                <div className={`text-[10px] font-mono tracking-wide flex items-center gap-2 
                  ${getEmailStatus(email).type === 'active' ? 'text-[#00E5FF]' : ''}
                  ${getEmailStatus(email).type === 'error' ? 'text-[#FF3D8A]' : ''}
                  ${getEmailStatus(email).type === 'success' ? 'text-[#39FF88]' : ''}
                  ${getEmailStatus(email).type === 'idle' ? 'text-[#7C8798]' : ''}
                `}>
                  {getEmailStatus(email).type === 'success' && <Check size={12} />}
                  {getEmailStatus(email).type === 'error' && <X size={12} />}
                  {'> ' + getEmailStatus(email).text}
                </div>
              </div>
            )}

            {/* PASSWORD FIELD (Login, Register) */}
            {['login', 'register'].includes(flow) && (
              <div className="space-y-2">
                <div className="flex justify-between items-end">
                  <label className="text-xs font-mono uppercase tracking-wider text-[#7C8798]">Encryption Key</label>
                  {flow === 'login' && (
                    <button type="button" onClick={() => setFlow('forgot')} className="text-xs font-mono text-[#7C8798] hover:text-[#00E5FF] transition-colors">
                      [ Bypas Key ]
                    </button>
                  )}
                </div>
                <div className="relative group">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <KeyRound size={16} className={focusedField === 'password' ? 'text-[#00E5FF]' : 'text-[#7C8798]'} />
                  </div>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    onFocus={() => setFocusedField('password')}
                    onBlur={() => setFocusedField(null)}
                    className="w-full bg-[#0B0E14] border border-[#1F2733] rounded-[4px] pl-11 pr-4 py-3 text-[#E8EDF4] font-mono focus:outline-none focus:border-[#00E5FF] transition-colors tracking-widest"
                    placeholder="••••••••"
                  />
                  {focusedField === 'password' && <div className="absolute top-0 left-0 h-full w-[2px] bg-[#00E5FF] shadow-[0_0_8px_#00E5FF] overflow-hidden"><div className="w-full h-[20%] bg-white absolute top-[-20%] animate-scan-vertical mix-blend-overlay" /></div>}
                </div>
                
                {/* Live Status / Strength Meter */}
                <div className="flex flex-col gap-1.5">
                  <div className={`text-[10px] font-mono tracking-wide flex items-center gap-2 
                    ${getPasswordStatus(password, flow === 'register').type === 'active' ? 'text-[#00E5FF]' : ''}
                    ${getPasswordStatus(password, flow === 'register').type === 'error' ? 'text-[#FF3D8A]' : ''}
                    ${getPasswordStatus(password, flow === 'register').type === 'success' ? 'text-[#39FF88]' : ''}
                    ${getPasswordStatus(password, flow === 'register').type === 'idle' ? 'text-[#7C8798]' : ''}
                  `}>
                    {getPasswordStatus(password, flow === 'register').type === 'success' && <Check size={12} />}
                    {getPasswordStatus(password, flow === 'register').type === 'error' && <X size={12} />}
                    {'> ' + getPasswordStatus(password, flow === 'register').text}
                  </div>
                  
                  {flow === 'register' && password.length > 0 && (
                    <div className="h-1 w-full bg-[#0B0E14] border border-[#1F2733] rounded-[2px] overflow-hidden flex gap-[1px]">
                      {[25, 50, 75, 100].map((step) => (
                        <div 
                          key={step} 
                          className={`flex-1 transition-all duration-300 ${
                            getPasswordStrength(password) >= step 
                              ? (getPasswordStrength(password) === 100 ? 'bg-[#39FF88] shadow-[0_0_5px_#39FF88]' : getPasswordStrength(password) <= 25 ? 'bg-[#FF3D8A] shadow-[0_0_5px_#FF3D8A]' : 'bg-[#00E5FF] shadow-[0_0_5px_#00E5FF]')
                              : 'bg-transparent'
                          }`}
                        />
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* OTP GRID */}
            {flow === 'otp' && (
              <div className="space-y-4">
                <label className="text-xs font-mono uppercase tracking-wider text-[#7C8798]">Verification Sequence</label>
                <div className="flex justify-between gap-2">
                  {otp.map((digit, i) => (
                    <input
                      key={i}
                      ref={el => otpRefs.current[i] = el}
                      type="text"
                      inputMode="numeric"
                      value={digit}
                      onChange={(e) => handleOtpChange(i, e.target.value)}
                      onKeyDown={(e) => handleOtpKeyDown(i, e)}
                      onFocus={() => setFocusedField(`otp-${i}`)}
                      onBlur={() => setFocusedField(null)}
                      className="w-12 h-14 bg-[#0B0E14] border border-[#1F2733] rounded-[4px] text-center text-xl text-[#E8EDF4] font-mono focus:outline-none focus:border-[#00E5FF] transition-colors"
                      placeholder="0"
                    />
                  ))}
                </div>
                <div className="text-[10px] font-mono tracking-wide text-[#7C8798] flex justify-between items-center">
                  <span>{'> intercepting transmission...'}</span>
                  <button type="button" className="text-[#00E5FF] hover:underline">Resend Signal</button>
                </div>
              </div>
            )}

            {/* ACTION BUTTON */}
            <button
              type="submit"
              disabled={loading}
              className={`w-full group relative overflow-hidden rounded-[4px] py-4 px-6 border ${
                flow === 'forgot' ? 'border-[#00E5FF] bg-transparent hover:bg-[#00E5FF]/10 text-[#00E5FF]' : 'border-transparent bg-[#00E5FF] text-[#0B0E14] hover:bg-[#39FF88] hover:text-[#0B0E14]'
              } font-mono font-bold tracking-wide transition-all duration-300 disabled:opacity-50`}
            >
              <div className="relative z-10 flex items-center justify-center gap-3 uppercase text-sm">
                {loading ? (
                  <>
                    <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    {flow === 'login' && 'Initiate Connection'}
                    {flow === 'register' && 'Deploy Operative'}
                    {flow === 'forgot' && 'Transmit Recovery Signal'}
                    {flow === 'otp' && 'Confirm Sequence'}
                    <ArrowRight size={16} className="transform group-hover:translate-x-1 transition-transform" />
                  </>
                )}
              </div>
              
              {/* Button active scan effect */}
              <div className="absolute inset-0 z-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:animate-shimmer" />
            </button>
            
          </form>

          {/* SOCIAL / SEPARATOR (Login & Register only) */}
          {['login', 'register'].includes(flow) && (
            <div className="space-y-6 pt-6 border-t border-[#1F2733]/50">
              <div className="flex items-center gap-4">
                <div className="flex-1 h-[1px] bg-[#1F2733]" />
                <span className="text-[10px] font-mono uppercase tracking-widest text-[#7C8798]">Or Dock Via</span>
                <div className="flex-1 h-[1px] bg-[#1F2733]" />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <button type="button" onClick={() => window.location.href = `${getBase()}/v1/auth/github/login`} className="flex items-center justify-center gap-3 py-3 px-4 bg-[#0B0E14] border border-[#1F2733] rounded-[4px] hover:border-[#00E5FF] hover:text-[#00E5FF] transition-colors font-mono text-xs uppercase tracking-wide text-[#E8EDF4] group">
                  <Github size={16} className="group-hover:text-[#00E5FF] transition-colors" />
                  GitHub
                </button>
                <button type="button" onClick={() => window.location.href = `${getBase()}/v1/auth/google/login`} className="flex items-center justify-center gap-3 py-3 px-4 bg-[#0B0E14] border border-[#1F2733] rounded-[4px] hover:border-[#00E5FF] hover:text-[#00E5FF] transition-colors font-mono text-xs uppercase tracking-wide text-[#E8EDF4] group">
                  <Command size={16} className="group-hover:text-[#00E5FF] transition-colors" />
                  Google
                </button>
              </div>
            </div>
          )}

          {/* FOOTER SWITCH */}
          <div className="pt-8 text-center text-xs font-mono text-[#7C8798]">
            {['forgot', 'otp'].includes(flow) && (
              <button onClick={() => setFlow('login')} className="text-[#00E5FF] hover:underline uppercase tracking-wide flex items-center justify-center gap-2 w-full">
                <ArrowRight size={14} className="transform rotate-180" /> Abort Sequence
              </button>
            )}
          </div>

        </div>
      </div>
      
      {/* Inline styles for custom animations that don't need tailwind.config mutation */}
      <style>{`
        @keyframes scanline {
          0% { top: 0; height: 0%; opacity: 0; }
          20% { opacity: 1; }
          80% { top: 100%; height: 2px; opacity: 0; }
          100% { top: 100%; opacity: 0; }
        }
        @keyframes scan-vertical {
          0% { top: -20%; }
          100% { top: 100%; }
        }
        @keyframes shimmer {
          100% { transform: translateX(100%); }
        }
        .animate-scanline {
          animation: scanline 2s cubic-bezier(0.4, 0, 0.2, 1) infinite;
        }
        .animate-scan-vertical {
          animation: scan-vertical 1.5s linear infinite;
        }
        .animate-shimmer {
          animation: shimmer 2s infinite;
        }
        @media (prefers-reduced-motion: reduce) {
          .animate-scanline, .animate-scan-vertical, .animate-shimmer, .animate-pulse {
            animation: none;
          }
        }
      `}</style>
    </div>
  );
}

export default AuthFlow;
