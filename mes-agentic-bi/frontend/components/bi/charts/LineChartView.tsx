import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import type { BIChartDataPoint } from '@/types/bi';

const COLORS = ['#06b6d4', '#14b8a6', '#67e8f9', '#5eead4', '#0e7490'];

interface LineChartViewProps {
  data: BIChartDataPoint[];
  xLabel: string;
  yLabel: string;
  groups?: string[];
}

export default function LineChartView({ data, xLabel, yLabel, groups }: LineChartViewProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
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
              <Line
                key={group}
                type="monotone"
                dataKey={group}
                stroke={COLORS[i % COLORS.length]}
                strokeWidth={2}
                dot={{ r: 3, fill: COLORS[i % COLORS.length] }}
                activeDot={{ r: 5 }}
              />
            ))}
          </>
        ) : (
          <Line
            type="monotone"
            dataKey="y"
            stroke="#06b6d4"
            strokeWidth={2}
            dot={{ r: 3, fill: '#06b6d4' }}
            activeDot={{ r: 5 }}
            name={yLabel}
          />
        )}
      </LineChart>
    </ResponsiveContainer>
  );
}
