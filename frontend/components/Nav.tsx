import Link from "next/link";

export function Nav() {
  return (
    <header className="border-b border-slate-200 bg-white/80 backdrop-blur">
      <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-3">
        <Link href="/" className="text-lg font-semibold text-slate-900">
          AI Past Paper Analyzer
        </Link>
        <nav className="flex gap-4 text-sm font-medium text-slate-600">
          <Link href="/" className="hover:text-accent">
            Upload
          </Link>
          <Link href="/dashboard" className="hover:text-accent">
            Dashboard
          </Link>
          <Link href="/planner" className="hover:text-accent">
            Planner
          </Link>
        </nav>
      </div>
    </header>
  );
}
