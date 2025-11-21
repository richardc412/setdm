"use client";

import { useAuth } from "@/contexts/AuthContext";
import ProtectedRoute from "@/components/ProtectedRoute";
import AppHeader from "@/components/AppHeader";
import { useRouter } from "next/navigation";

export default function DashboardPage() {
  const { user } = useAuth();
  const router = useRouter();

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-zinc-50 dark:bg-black flex flex-col diagonal-bg">
        <AppHeader />

        {/* Main Content */}
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Welcome Card */}
          <div className="bg-white dark:bg-zinc-900 rounded-xl shadow-sm border border-zinc-200 dark:border-zinc-800 p-6 mb-6">
            <h2 className="text-xl font-semibold text-zinc-900 dark:text-white mb-2">
              Welcome back, {user?.full_name || user?.username}! 👋
            </h2>
            <p className="text-zinc-600 dark:text-zinc-400">
              You&apos;re successfully logged in to your SetDM account.
            </p>
          </div>

          {/* User Information Card */}
          <div className="bg-white dark:bg-zinc-900 rounded-xl shadow-sm border border-zinc-200 dark:border-zinc-800 p-6 mb-6">
            <h3 className="text-lg font-semibold text-zinc-900 dark:text-white mb-4">
              Your Profile
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between py-3 border-b border-zinc-200 dark:border-zinc-800">
                <span className="text-sm font-medium text-zinc-600 dark:text-zinc-400">
                  Username
                </span>
                <span className="text-sm text-zinc-900 dark:text-white font-mono">
                  {user?.username}
                </span>
              </div>
              <div className="flex items-center justify-between py-3 border-b border-zinc-200 dark:border-zinc-800">
                <span className="text-sm font-medium text-zinc-600 dark:text-zinc-400">
                  Email
                </span>
                <span className="text-sm text-zinc-900 dark:text-white">
                  {user?.email}
                </span>
              </div>
              {user?.full_name && (
                <div className="flex items-center justify-between py-3 border-b border-zinc-200 dark:border-zinc-800">
                  <span className="text-sm font-medium text-zinc-600 dark:text-zinc-400">
                    Full Name
                  </span>
                  <span className="text-sm text-zinc-900 dark:text-white">
                    {user.full_name}
                  </span>
                </div>
              )}
              <div className="flex items-center justify-between py-3">
                <span className="text-sm font-medium text-zinc-600 dark:text-zinc-400">
                  Account Status
                </span>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200">
                  {user?.disabled ? "Disabled" : "Active"}
                </span>
              </div>
            </div>
          </div>

          {/* Quick Actions Card */}
          <div className="bg-white dark:bg-zinc-900 rounded-xl shadow-sm border border-zinc-200 dark:border-zinc-800 p-6">
            <h3 className="text-lg font-semibold text-zinc-900 dark:text-white mb-4">
              Quick Actions
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <button
                onClick={() => router.push("/chats")}
                className="flex items-center justify-center px-4 py-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 font-medium hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors"
              >
                <span>📷 Instagram DMs</span>
              </button>
              <button className="flex items-center justify-center px-4 py-3 rounded-lg bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300 font-medium hover:bg-purple-100 dark:hover:bg-purple-900/30 transition-colors">
                <span>⚙️ Settings</span>
              </button>
              <button className="flex items-center justify-center px-4 py-3 rounded-lg bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300 font-medium hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors">
                <span>📊 Analytics</span>
              </button>
              <button className="flex items-center justify-center px-4 py-3 rounded-lg bg-orange-50 dark:bg-orange-900/20 text-orange-700 dark:text-orange-300 font-medium hover:bg-orange-100 dark:hover:bg-orange-900/30 transition-colors">
                <span>📝 New Campaign</span>
              </button>
            </div>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}
