"use client";

import { motion } from "framer-motion";
import type { MeetingSummary } from "@/lib/types";

type SummaryCardProps = {
  summary: MeetingSummary;
};

const ITEMS = [
  {
    key: "direction" as const,
    label: "当前倾向",
    icon: "🎯",
    accent: "from-violet-500/10 to-violet-500/5 border-violet-200/80",
    labelColor: "text-violet-700",
  },
  {
    key: "disagreement" as const,
    label: "最大分歧",
    icon: "⚡",
    accent: "from-amber-500/10 to-amber-500/5 border-amber-200/80",
    labelColor: "text-amber-700",
  },
  {
    key: "nextStep" as const,
    label: "下一步",
    icon: "🚀",
    accent: "from-emerald-500/10 to-emerald-500/5 border-emerald-200/80",
    labelColor: "text-emerald-700",
  },
];

export function SummaryCard({ summary }: SummaryCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 300, damping: 28 }}
      className="mx-auto w-full max-w-3xl"
    >
      <div className="mb-3 flex items-center justify-center gap-2">
        <span className="h-px w-8 bg-gradient-to-r from-transparent to-violet-300" />
        <h2 className="text-sm font-bold tracking-wide text-violet-900 sm:text-base">
          本轮决策小结
        </h2>
        <span className="h-px w-8 bg-gradient-to-l from-transparent to-violet-300" />
      </div>

      <div className="grid gap-3 sm:grid-cols-3 sm:gap-4">
        {ITEMS.map(({ key, label, icon, accent, labelColor }, i) => (
          <motion.div
            key={key}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08, type: "spring", stiffness: 320, damping: 26 }}
            className={`glass-panel-strong rounded-2xl border bg-gradient-to-br p-4 ${accent}`}
          >
            <div className="mb-2 flex items-center gap-2">
              <span className="text-lg" aria-hidden>
                {icon}
              </span>
              <span className={`text-xs font-bold uppercase tracking-wider ${labelColor}`}>
                {label}
              </span>
            </div>
            <p className="text-sm leading-relaxed text-slate-700">{summary[key]}</p>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
