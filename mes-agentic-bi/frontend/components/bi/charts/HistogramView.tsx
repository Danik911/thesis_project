import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import type { BIHistogramBin } from '@/types/bi';

interface HistogramViewProps {
  data: BIHistogramBin[];
  xLabel: string;
}

export default function HistogramView({ data, xLabel }: HistogramViewProps) {
  const formatted = data.map((bin) => ({
    ...bin,
    label: `${bin.bin_start.toFixed(1)}-${bin.bin_end.toFixed(1)}`,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={formatted} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis
          dataKey="label"
          tick={{ fill: '#94a3b8', fontSize: 9 }}
          axisLine={{ stroke: '#475569' }}
          label={{ value: xLabel, position: 'insideBottom', offset: -4, fill: '#94a3b8', fontSize: 11 }}
          interval={Math.max(0, Math.floor(formatted.length / 8) - 1)}
        />
        <YAxis
          tick={{ fill: '#94a3b8', fontSize: 11 }}
          axisLine={{ stroke: '#475569' }}
          label={{ value: 'Count', angle: -90, position: 'insideLeft', fill: '#94a3b8', fontSize: 11 }}
        />
        <Tooltip
          contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
          labelStyle={{ color: '#94a3b8' }}
          itemStyle={{ color: '#67e8f9' }}
          formatter={(value) => [value ?? 0, 'Count']}
        />
        <Bar dataKey="count" fill="#14b8a6" radius={[2, 2, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
