import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from 'recharts';

import type { BIChartDataPoint } from '@/types/bi';

interface ScatterChartViewProps {
  data: BIChartDataPoint[];
  xLabel: string;
  yLabel: string;
  sampled?: boolean;
  sampleSize?: number;
}

export default function ScatterChartView({ data, xLabel, yLabel, sampled, sampleSize }: ScatterChartViewProps) {
  return (
    <div>
      <ResponsiveContainer width="100%" height={300}>
        <ScatterChart margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis
            dataKey="x"
            type="number"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={{ stroke: '#475569' }}
            label={{ value: xLabel, position: 'insideBottom', offset: -4, fill: '#94a3b8', fontSize: 11 }}
            name={xLabel}
          />
          <YAxis
            dataKey="y"
            type="number"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={{ stroke: '#475569' }}
            label={{ value: yLabel, angle: -90, position: 'insideLeft', fill: '#94a3b8', fontSize: 11 }}
            name={yLabel}
          />
          <ZAxis range={[20, 20]} />
          <Tooltip
            contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
            labelStyle={{ color: '#94a3b8' }}
            itemStyle={{ color: '#67e8f9' }}
            cursor={{ strokeDasharray: '3 3', stroke: '#475569' }}
          />
          <Scatter data={data} fill="#06b6d4" fillOpacity={0.5} />
        </ScatterChart>
      </ResponsiveContainer>
      {sampled && (
        <p className="text-xs text-slate-500 text-center mt-1">
          Sampled to {sampleSize} points for performance
        </p>
      )}
    </div>
  );
}
