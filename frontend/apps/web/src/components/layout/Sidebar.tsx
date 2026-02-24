"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuthStore } from "@/store/auth.store";

interface NavItem {
  href: string;
  label: string;
  icon: string; // emoji/text icon for now
}

// Two primary views. The vessel cockpit (/vessel/[id]) embeds the
// sociogram and recruitment panel — no separate routes needed for those.
const NAV_ITEMS: NavItem[] = [
  { href: "/dashboard", label: "Fleet", icon: "◈" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { name, logout } = useAuthStore();

  return (
    <aside className="flex flex-col h-screen w-56 bg-bg-secondary border-r border-bg-border shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-4 h-14 border-b border-bg-border">
        <div className="w-7 h-7 rounded-full bg-brand-primary/20 border border-brand-primary/40
                        flex items-center justify-center">
          <span className="text-brand-primary font-bold text-xs">H</span>
        </div>
        <span className="font-semibold text-text-primary">Harmony</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const active = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                active
                  ? "bg-brand-primary/10 text-brand-primary font-medium"
                  : "text-muted hover:text-text-primary hover:bg-bg-elevated"
              }`}
            >
              <span className="text-base leading-none">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* User */}
      <div className="px-4 py-3 border-t border-bg-border">
        <p className="text-xs text-muted truncate mb-2">{name}</p>
        <button
          onClick={logout}
          className="btn-ghost w-full text-left text-xs py-1.5"
        >
          Sign out
        </button>
      </div>
    </aside>
  );
}
