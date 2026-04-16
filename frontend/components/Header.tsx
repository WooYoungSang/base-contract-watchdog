import Link from "next/link";

export function Header() {
  return (
    <header className="border-b border-gray-800 bg-gray-950">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
        <Link href="/" className="flex items-center gap-2 text-white font-bold text-lg">
          <span className="text-red-500">⬡</span>
          <span>Contract Watchdog</span>
        </Link>
        <nav className="flex gap-6 text-sm text-gray-400">
          <Link href="/events" className="hover:text-white transition-colors">Events</Link>
          <Link href="/stats" className="hover:text-white transition-colors">Stats</Link>
        </nav>
      </div>
    </header>
  );
}
