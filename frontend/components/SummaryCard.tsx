"use client";

import { motion } from "framer-motion";
import type { MeetingSummary } from "@/lib/types";

type SummaryCardProps = {
  summary: MeetingSummary;
};

export function SummaryCard({ summary }: SummaryCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 320, damping: 26 }}
      className="mx-auto mt-6 w-full max-w-xl rounded-3xl border border-violet-100 bg-white/90 p-5 shadow-xl shadow-violet-100/50 sm:mt-8 sm:p-6"
    >
      <h2 className="mb-4 text-lg font-bold text-violet-900">🎯 本轮决策</h2>
      <ul className="space-y-3 text-sm text-slate-700">
        <li>
          <span className="font-semibold text-slate-900">当前倾向：</span>
          {summary.direction}
        </li>
        <li>
          <span className="font-semibold text-slate-900">最大分歧：</span>
          {summary.disagreement}
        </li>
        <li>
          <span className="font-semibold text-slate-900">下一步动作：</span>
          {summary.nextStep}
        </li>
      </ul>
    </motion.div>
  );
}
