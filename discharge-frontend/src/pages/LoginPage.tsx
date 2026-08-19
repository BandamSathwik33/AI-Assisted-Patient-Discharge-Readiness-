import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { DEMO_USERS } from '../mock/mockData';
import { Activity, Stethoscope, UserCheck, KeyRound, ArrowRight, ShieldAlert } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { quickLogin, login } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleQuickLogin = async (userKey: string) => {
    setSubmitting(true);
    setError(null);
    try {
      await quickLogin(userKey);
      navigate('/overview');
    } catch (err: any) {
      setError(err.message || 'Quick login failed');
    } finally {
      setSubmitting(false);
    }
  };

  const handleManualLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username) return;
    setSubmitting(true);
    setError(null);
    try {
      await login(username, password);
      navigate('/overview');
    } catch (err: any) {
      setError(err.message || 'Login failed. Please check credentials.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center p-4 relative overflow-hidden font-sans">
      {/* Background Decorative Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-[300px] h-[300px] bg-rose-500/5 rounded-full blur-2xl pointer-events-none" />

      <div className="max-w-xl w-full bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl z-10 space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-teal-500 to-emerald-600 shadow-xl shadow-teal-500/20 mb-1">
            <Activity className="w-8 h-8 text-slate-950 stroke-[2.5]" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            PulseIQ Discharge Planner
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 font-medium">
            AI-Assisted Patient Discharge Readiness & Follow-Up System
          </p>
        </div>

        {/* Clinical Disclaimer Chip */}
        <div className="bg-rose-950/60 border border-rose-800/80 rounded-xl p-3 text-center text-rose-200 text-xs font-semibold flex items-center justify-center gap-2">
          <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0" />
          <span>Clinical Decision Support System — Authorized Personnel Only</span>
        </div>

        {error && (
          <div className="bg-rose-950 text-rose-200 border border-rose-800 text-xs p-3 rounded-xl">
            {error}
          </div>
        )}

        {/* DEMO QUICK-LOGIN BUTTONS (ONE-CLICK JUDGE DEMO) */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-teal-400 uppercase tracking-wider flex items-center gap-1.5">
              <Stethoscope className="w-4 h-4" />
              One-Click Judge Demo Users
            </span>
            <span className="text-[11px] text-slate-500 font-mono">Select Role to Login</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {Object.entries(DEMO_USERS).map(([key, demoUser]) => (
              <button
                key={key}
                onClick={() => handleQuickLogin(key)}
                disabled={submitting}
                className="bg-slate-950 hover:bg-slate-800 border border-slate-700/80 hover:border-teal-500 rounded-xl p-3 text-left transition-all group flex items-center justify-between shadow-sm active:scale-98"
              >
                <div>
                  <div className="text-xs font-bold text-slate-200 group-hover:text-teal-300">
                    {demoUser.full_name}
                  </div>
                  <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                    Role: <strong className="text-teal-400">{demoUser.role.replace('_', ' ')}</strong>
                  </div>
                </div>
                <div className="w-7 h-7 rounded-lg bg-slate-800 group-hover:bg-teal-600 text-slate-400 group-hover:text-white flex items-center justify-center transition-colors">
                  <ArrowRight className="w-4 h-4" />
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="relative flex items-center justify-center">
          <div className="border-t border-slate-800 w-full" />
          <span className="bg-slate-900 px-3 text-[11px] font-mono text-slate-500 uppercase">Or Manual Entry</span>
        </div>

        {/* Manual Login Form */}
        <form onSubmit={handleManualLogin} className="space-y-3">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Username / Network ID
            </label>
            <div className="relative">
              <UserCheck className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. dr.smith or custom user"
                className="w-full bg-slate-950 border border-slate-800 text-slate-100 text-xs rounded-xl pl-9 pr-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Password
            </label>
            <div className="relative">
              <KeyRound className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Any password for demo"
                className="w-full bg-slate-950 border border-slate-800 text-slate-100 text-xs rounded-xl pl-9 pr-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-teal-600 hover:bg-teal-500 text-white font-bold text-xs py-3 rounded-xl shadow-lg shadow-teal-950/50 transition-all active:scale-98"
          >
            {submitting ? 'Authenticating...' : 'Sign In to Clinical Portal'}
          </button>
        </form>
      </div>
    </div>
  );
};
