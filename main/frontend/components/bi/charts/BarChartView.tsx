import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import type { BIChartDataPoint } from '@/types/bi';

const COLORS = ['#06b6d4', '#14b8a6', '#67e8f9', '#5eead4', '#0e7490'];

interface BarChartViewProps {
  data: BIChartDataPoint[];
  xLabel: string;
  yLabel: string;
  groups?: string[];
}

export default function BarChartView({ data, xLabel, yLabel, groups }: BarChartViewProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis
          dataKey="x"
          tick={{ fill: '#94a3b8', fontSize: 11 }}
          axisLine={{ stroke: '#475569' }}
          label={{ value: xLabel, position: 'insideBottom', offset: -4, fill: '#94a3b8', fontSize: 11 }}
        />
        <YAxis
          tick={{ fill: '#94a3b8', fontSize: 11 }}
          axisLine={{ stroke: '#475569' }}
          label={{ value: yLabel, angle: -90, position: 'insideLeft', fill: '#94a3b8', fontSize: 11 }}
        />
        <Tooltip
          contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
          labelStyle={{ color: '#94a3b8' }}
          itemStyle={{ color: '#67e8f9' }}
        />
        {groups && groups.length > 0 ? (
          <>
            <Legend wrapperStyle={{ color: '#94a3b8', fontSize: 11 }} />
            {groups.map((group, i) => (
              <Bar key={group} dataKey={group} fill={COLORS[i % COLORS.length]} radius={[2, 2, 0, 0]} />
            ))}
          </>
        ) : (
          <Bar dataKey="y" fill="#06b6d4" radius={[2, 2, 0, 0]} name={yLabel} />
        )}
      </BarChart>
    </ResponsiveContainer>
  );
}
