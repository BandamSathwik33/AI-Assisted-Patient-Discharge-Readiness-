import React from 'react';
import { AlertTriangle, ShieldCheck } from 'lucide-react';

interface SafetyBannerProps {
  isPatientView?: boolean;
}

export const SafetyBanner: React.FC<SafetyBannerProps> = ({ isPatientView = false }) => {
  if (isPatientView) {
    return (
      <div className="bg-sky-950/80 border-b border-sky-800/50 text-sky-200 px-4 py-2 text-xs flex items-center justify-center gap-2 shadow-sm font-medium">
        <ShieldCheck className="w-4 h-4 text-sky-400 shrink-0" />
        <span>
          AI-Generated Clinical Decision Support. All recommendations require verification by a licensed healthcare provider prior to patient discharge.
        </span>
      </div>
    );
  }

  return (
    <div className="bg-rose-950/90 border-b border-rose-800/80 text-rose-100 px-4 py-2 text-xs font-semibold flex items-center justify-center gap-2 shadow-md backdrop-blur-sm sticky top-0 z-50 tracking-wide uppercase">
      <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 animate-pulse" />
      <span>
        AI-Generated Clinical Decision Support. All recommendations require verification by a licensed healthcare provider prior to patient discharge.
      </span>
    </div>
  );
};
