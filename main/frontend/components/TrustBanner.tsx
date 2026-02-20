import { motion } from 'framer-motion';
import { ShieldCheckIcon } from '@heroicons/react/24/outline';

interface TrustBannerProps {
  className?: string;
}

export default function TrustBanner({ className }: TrustBannerProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.8, delay: 0.4 }}
      className={`flex items-center justify-center gap-3 py-2.5 ${className ?? ''}`}
    >
      <ShieldCheckIcon className="w-4 h-4 text-emerald-400/60" />
      <span className="text-xs font-medium text-emerald-400/80">AI-assisted</span>
      <span className="text-slate-600">·</span>
      <span className="text-xs font-medium text-blue-400/80">Human-approved</span>
      <span className="text-slate-600">·</span>
      <span className="text-xs font-medium text-violet-400/80">Audit-ready</span>
    </motion.div>
  );
}
