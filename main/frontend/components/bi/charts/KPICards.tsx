import type { BIKPICard } from '@/types/bi';

interface KPICardsProps {
  cards: BIKPICard[];
}

function formatNumber(val: number | null): string {
  if (val === null || val === undefined) return '-';
  if (Math.abs(val) >= 1_000_000) return `${(val / 1_000_000).toFixed(1)}M`;
  if (Math.abs(val) >= 1_000) return `${(val / 1_000).toFixed(1)}K`;
  return val % 1 === 0 ? val.toFixed(0) : val.toFixed(2);
}

export default function KPICards({ cards }: KPICardsProps) {
  if (cards.length === 0) return null;

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3 mb-6">
      {cards.map((card) => (
        <div
          key={card.column}
          className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-3"
        >
          <p className="text-xs text-slate-400 truncate mb-2" title={card.column}>
            {card.column}
          </p>
          <p className="text-lg font-semibold text-cyan-300">{formatNumber(card.mean)}</p>
          <p className="text-xs text-slate-500 mb-2">avg</p>
          <div className="flex items-center gap-3 text-xs">
            <span className="text-slate-400">
              Min <span className="text-slate-300">{formatNumber(card.min)}</span>
            </span>
            <span className="text-slate-400">
              Max <span className="text-slate-300">{formatNumber(card.max)}</span>
            </span>
          </div>
          <div className="flex items-center gap-3 text-xs mt-1">
            <span className="text-slate-400">
              Count <span className="text-slate-300">{formatNumber(card.count)}</span>
            </span>
            {card.sum !== null && (
              <span className="text-slate-400">
                Sum <span className="text-slate-300">{formatNumber(card.sum)}</span>
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
