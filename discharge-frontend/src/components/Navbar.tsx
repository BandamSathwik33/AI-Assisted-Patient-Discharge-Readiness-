import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import type { UserRole } from '../types';
import { Activity, LogOut, UserCheck, LayoutDashboard, ChevronRight, Stethoscope } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, logout, switchRole } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleRoleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    switchRole(e.target.value as UserRole);
  };

  return (
    <header className="bg-slate-950 border-b border-slate-800 text-slate-100 px-4 lg:px-8 py-3 flex items-center justify-between sticky top-[33px] z-40 shadow-xl">
      {/* Brand & Breadcrumbs */}
      <div className="flex items-center gap-3">
        <Link to="/overview" className="flex items-center gap-2.5 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-teal-500 to-emerald-600 flex items-center justify-center shadow-lg shadow-teal-500/20 group-hover:scale-105 transition-transform">
            <Activity className="w-5 h-5 text-slate-950 stroke-[2.5]" />
          </div>
          <div>
            <div className="font-bold text-base text-white leading-none tracking-tight flex items-center gap-1.5">
              PulseIQ Discharge
              <span className="text-[10px] font-mono uppercase bg-teal-500/20 text-teal-300 border border-teal-500/30 px-1.5 py-0.5 rounded">
                Clinical AI
              </span>
            </div>
            <div className="text-[11px] text-slate-400 font-medium">St. Jude Medical Center</div>
          </div>
        </Link>

        {location.pathname.startsWith('/patients/') && (
          <div className="hidden sm:flex items-center text-slate-500 text-xs font-mono pl-2 border-l border-slate-800">
            <ChevronRight className="w-4 h-4 text-slate-600" />
            <span className="text-slate-300 ml-1">Patient Evaluation</span>
          </div>
        )}
      </div>

      {/* Navigation & Role Controls */}
      <div className="flex items-center gap-3 sm:gap-5">
        <Link
          to="/overview"
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
            location.pathname === '/overview'
              ? 'bg-slate-800 text-teal-400 border border-slate-700'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <LayoutDashboard className="w-4 h-4" />
          <span>Hospital Overview</span>
        </Link>

        {/* Quick Role Switcher */}
        {user && (
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-xl px-2.5 py-1 text-xs">
            <div className="flex items-center gap-1.5 text-slate-300">
              <UserCheck className="w-3.5 h-3.5 text-teal-400" />
              <span className="hidden md:inline font-medium">{user.full_name}</span>
            </div>

            <div className="h-4 w-px bg-slate-800 hidden md:block" />

            <div className="flex items-center gap-1">
              <Stethoscope className="w-3.5 h-3.5 text-slate-400 hidden sm:inline" />
              <select
                value={user.role}
                onChange={handleRoleChange}
                className="bg-slate-800 text-teal-300 text-xs font-semibold rounded px-2 py-1 border border-slate-700 focus:outline-none focus:ring-1 focus:ring-teal-500 cursor-pointer"
                title="Switch demo role for testing role-gated permissions"
              >
                <option value="Physician">Physician</option>
                <option value="Nurse">Nurse</option>
                <option value="Pharmacist">Pharmacist</option>
                <option value="Case_Manager">Case Manager</option>
                <option value="Admin">Admin</option>
              </select>
            </div>
          </div>
        )}

        {/* Logout */}
        <button
          onClick={() => {
            logout();
            navigate('/login');
          }}
          className="p-2 text-slate-400 hover:text-rose-400 hover:bg-slate-900 rounded-lg transition-colors"
          title="Sign out"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
