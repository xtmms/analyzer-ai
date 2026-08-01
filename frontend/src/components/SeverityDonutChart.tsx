import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { SEVERITY_COLORS } from "../lib/types";

export function SeverityDonutChart({ severityCounts }: { severityCounts: Record<string, number> }) {
  const data = Object.entries(severityCounts)
    .filter(([, count]) => count > 0)
    .map(([name, value]) => ({ name, value }));

  if (data.length === 0) {
    return <p className="text-sm text-text-muted">Nessuna severità rilevata nel file di log.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="name" innerRadius={60} outerRadius={95} paddingAngle={2}>
          {data.map((entry) => (
            <Cell key={entry.name} fill={SEVERITY_COLORS[entry.name] ?? "#94a3b8"} stroke="none" />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{ background: "#131826", border: "1px solid #ffffff1a", borderRadius: 8 }}
          itemStyle={{ color: "#e2e8f0" }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
