import { markdownToHtml } from "../lib/markdown";
import type { LogAnalysisReport } from "../lib/types";

export function ReportCards({ report }: { report: LogAnalysisReport }) {
  const points = [report.problem_summary, report.root_cause_analysis, report.recommendations];
  const accents = ["border-l-[#a78bfa]", "border-l-[#38bdf8]", "border-l-[#50fa7b]"];

  return (
    <div className="space-y-4">
      {points.map((point, idx) => (
        <div key={point.title} className={`glass-card border-l-4 p-6 ${accents[idx % accents.length]}`}>
          <h4 className="mb-2 text-base font-semibold text-text">{point.title}</h4>
          <div
            className="space-y-2 text-sm leading-relaxed text-text-muted [&_code]:rounded [&_code]:bg-black/30 [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:text-accent [&_pre]:overflow-auto [&_pre]:rounded-lg [&_pre]:bg-black/40 [&_pre]:p-3 [&_ul]:list-disc [&_ul]:space-y-1 [&_ul]:pl-5"
            dangerouslySetInnerHTML={{ __html: markdownToHtml(point.content) }}
          />
        </div>
      ))}
    </div>
  );
}
