"use client";

type MeetingInputProps = {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
  placeholder?: string;
};

export function MeetingInput({
  value,
  onChange,
  onSubmit,
  disabled = false,
  placeholder = "输入议题，例如：需求评审会要不要引入 AI 辅助？",
}: MeetingInputProps) {
  return (
    <form
      className="mx-auto w-full max-w-2xl"
      onSubmit={(e) => {
        e.preventDefault();
        if (!disabled && value.trim()) onSubmit();
      }}
    >
      <div className="glass-panel-strong rounded-2xl p-2 shadow-lg shadow-violet-200/30 sm:rounded-3xl sm:p-2.5">
        <div className="flex flex-col gap-2 sm:flex-row sm:gap-3">
          <input
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            placeholder={placeholder}
            className="flex-1 rounded-xl border-0 bg-violet-50/50 px-4 py-3.5 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:bg-white focus:ring-2 focus:ring-violet-200 disabled:opacity-60 sm:rounded-2xl sm:px-5 sm:text-base"
          />
          <button
            type="submit"
            disabled={disabled || !value.trim()}
            className="rounded-xl bg-gradient-to-r from-violet-600 via-violet-500 to-fuchsia-500 px-8 py-3.5 text-sm font-semibold text-white shadow-md shadow-violet-300/40 transition hover:shadow-lg hover:shadow-violet-300/50 hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-50 sm:rounded-2xl sm:px-10"
          >
            开始讨论
          </button>
        </div>
      </div>
      <p className="mt-3 text-center text-xs text-slate-500">
        四位 AI 专家将围绕你的议题展开圆桌讨论
      </p>
    </form>
  );
}
