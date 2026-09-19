import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { CalibrationPoint } from "../types/facial";

interface ProbabilityChartProps {
  data: CalibrationPoint[];
  umbral: number;
}

export default function ProbabilityChart({
  data,
  umbral,
}: ProbabilityChartProps) {
  const puntos = data.map((punto) => ({
    similitud: Number((punto.similitud * 100).toFixed(1)),
    probabilidad: Number((punto.probabilidad * 100).toFixed(1)),
  }));

  return (
    <ResponsiveContainer width="100%" height={230}>
      <LineChart
        data={puntos}
        margin={{ top: 10, right: 12, bottom: 0, left: -12 }}
      >
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="var(--border)"
        />

        <XAxis
          dataKey="similitud"
          tick={{ fontSize: 11, fill: "var(--text-muted)" }}
          tickFormatter={(valor: number) => `${valor}%`}
          label={{
            value: "Similitud",
            position: "insideBottom",
            offset: -4,
            fontSize: 11,
            fill: "var(--text-muted)",
          }}
        />

        <YAxis
          domain={[0, 100]}
          tick={{ fontSize: 11, fill: "var(--text-muted)" }}
          tickFormatter={(valor: number) => `${valor}%`}
        />

        <Tooltip
          formatter={(valor: number) => [`${valor}%`, "Probabilidad"]}
          labelFormatter={(valor: number) => `Similitud ${valor}%`}
          contentStyle={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 12,
          }}
        />

        <ReferenceLine
          x={Number((umbral * 100).toFixed(1))}
          stroke="var(--warning)"
          strokeDasharray="4 4"
          label={{
            value: "Umbral",
            fontSize: 10,
            fill: "var(--warning)",
            position: "top",
          }}
        />

        <Line
          type="monotone"
          dataKey="probabilidad"
          stroke="var(--primary)"
          strokeWidth={2.5}
          dot={false}
          activeDot={{ r: 4 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
