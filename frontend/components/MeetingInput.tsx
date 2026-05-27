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
  placeholder = "输入你的问题，开始圆桌讨论…",
}: MeetingInputProps) {
  return (
    <form
      className="mx-auto flex w-full max-w-2xl gap-3"
      onSubmit={(e) => {
        e.preventDefault();
        if (!disabled && value.trim()) onSubmit();
      }}
    >
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        placeholder={placeholder}
        className="flex-1 rounded-2xl border border-violet-100 bg-white/90 px-5 py-3 text-sm text-slate-800 shadow-inner outline-none transition focus:border-violet-300 focus:ring-2 focus:ring-violet-200 disabled:opacity-60"
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        className="rounded-2xl bg-gradient-to-r from-violet-500 to-fuchsia-400 px-6 py-3 text-sm font-semibold text-white shadow-md transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-50"
      >
        开始讨论
      </button>
    </form>
  );
}
