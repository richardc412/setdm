"use client";

import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { ReactNode } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";

export type AppHeaderProps = {
  title?: string;
  subtitle?: string;
  actions?: ReactNode;
  hideAuthActions?: boolean;
};

export default function AppHeader({
  title,
  subtitle,
  actions,
  hideAuthActions = false,
}: AppHeaderProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error("Failed to logout:", error);
    } finally {
      router.push("/login");
    }
  };

  const isActive = (path: string) => pathname === path;

  return (
    <header className="sticky top-0 z-40 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-xl border-b border-zinc-200 dark:border-zinc-800 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4 min-w-0">
          <Link
            href="/dashboard"
            className="flex items-center text-4xl text-zinc-900 dark:text-white whitespace-nowrap italic"
          >
            <img
              src="/paper_airplane.svg"
              alt="SetDM Logo"
              className="w-8 h-8"
            />
            SetDM
          </Link>

          {/* Visual Divider */}
          <div
            className="h-8 w-px bg-zinc-300 dark:bg-zinc-700"
            aria-hidden="true"
          />

          {/* Navigation Links */}
          <nav className="flex items-center gap-2">
            <Button
              variant={isActive("/dashboard") ? "slate" : "ghost"}
              size="sm"
              asChild
            >
              <Link href="/dashboard">Dashboard</Link>
            </Button>
            <Button
              variant={isActive("/chats") ? "slate" : "ghost"}
              size="sm"
              asChild
            >
              <Link href="/chats">Messages</Link>
            </Button>
          </nav>
        </div>
        <div className="flex items-center gap-3 flex-wrap justify-end">
          {actions}
          {!hideAuthActions && (
            <>
              <span className="text-sm text-zinc-600 dark:text-zinc-400 hidden sm:inline-flex">
                {user?.username ?? "Guest"}
              </span>
              <Button variant="slate" size="sm" onClick={handleLogout}>
                Logout
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
