import { motion } from 'framer-motion';
import {
  CpuChipIcon,
  ArrowPathIcon,
  BookOpenIcon,
  UserCircleIcon,
} from '@heroicons/react/24/outline';
import type { ComponentType, SVGProps } from 'react';

type HeroIcon = ComponentType<SVGProps<SVGSVGElement>>;

interface Pillar {
  key: string;
  label: string;
  shortLabel: string;
  description: string;
  icon: HeroIcon;
  color: string;
}

const PILLARS: Pillar[] = [
  {
    key: 'deterministic-ml',
    label: 'Deterministic ML',
    shortLabel: 'ML',
    description: 'Predictable classify, route, and validate behavior with transparent evidence.',
    icon: CpuChipIcon,
    color: 'blue',
  },
  {
    key: 'agentic-orchestration',
    label: 'Agentic Orchestration',
    shortLabel: 'Agentic',
    description: 'Staged pipeline execution with reasoning at every step.',
    icon: ArrowPathIcon,
    color: 'violet',
  },
  {
    key: 'standards-rag',
    label: 'Standards RAG',
    shortLabel: 'RAG',
    description: 'Suggestions grounded in pharmacopeial reference standards.',
    icon: BookOpenIcon,
    color: 'cyan',
  },
  {
    key: 'hitl',
    label: 'Human-in-the-Loop',
    shortLabel: 'HITL',
    description: 'SME review and final approval authority at every critical gate.',
    icon: UserCircleIcon,
    color: 'emerald',
  },
];

const PILLAR_CLASSES: Record<string, { bg: string; chip: string }> = {
  blue: {
    bg: 'bg-blue-500/15 border-blue-500/25',
    chip: 'bg-blue-500/15 border-blue-500/25 text-blue-400',
  },
  violet: {
    bg: 'bg-violet-500/15 border-violet-500/25',
    chip: 'bg-violet-500/15 border-violet-500/25 text-violet-400',
  },
  cyan: {
    bg: 'bg-cyan-500/15 border-cyan-500/25',
    chip: 'bg-cyan-500/15 border-cyan-500/25 text-cyan-400',
  },
  emerald: {
    bg: 'bg-emerald-500/15 border-emerald-500/25',
    chip: 'bg-emerald-500/15 border-emerald-500/25 text-emerald-400',
  },
};

const ICON_CLASSES: Record<string, string> = {
  blue: 'text-blue-400',
  violet: 'text-violet-400',
  cyan: 'text-cyan-400',
  emerald: 'text-emerald-400',
};

interface PlatformPillarsProps {
  variant: 'full' | 'compact';
}

export default function PlatformPillars({ variant }: PlatformPillarsProps) {
  if (variant === 'compact') {
    return (
      <div className="flex items-center gap-2">
        {PILLARS.map((pillar) => {
          const Icon = pillar.icon;
          return (
            <span
              key={pillar.key}
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium border ${PILLAR_CLASSES[pillar.color].chip}`}
            >
              <Icon className="w-3 h-3" />
              {pillar.shortLabel}
            </span>
          );
        })}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {PILLARS.map((pillar, index) => {
        const Icon = pillar.icon;
        return (
          <motion.div
            key={pillar.key}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: index * 0.1, ease: 'easeOut' }}
            className="rounded-xl bg-slate-800/50 border border-slate-700/50 p-4 space-y-3"
          >
            <div className={`w-9 h-9 rounded-lg border flex items-center justify-center ${PILLAR_CLASSES[pillar.color].bg}`}>
              <Icon className={`w-4.5 h-4.5 ${ICON_CLASSES[pillar.color]}`} />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-100">{pillar.label}</p>
              <p className="text-xs text-slate-400 mt-1 leading-relaxed">{pillar.description}</p>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
