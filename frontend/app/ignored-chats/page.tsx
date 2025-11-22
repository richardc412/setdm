"use client";

import ProtectedRoute from "@/components/ProtectedRoute";
import AppHeader from "@/components/AppHeader";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  getIgnoredChats,
  Chat,
  unignoreChat,
  getChatAttendee,
} from "@/lib/api";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { MoreVertical, ArrowLeft } from "lucide-react";

export default function IgnoredChatsPage() {
  const router = useRouter();
  const [chats, setChats] = useState<Chat[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Profile picture cache
  const [profilePictures, setProfilePictures] = useState<
    Record<string, string>
  >({});

  const loadIgnoredChats = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await getIgnoredChats({ limit: 100, offset: 0 });
      setChats(response.items);
      fetchProfilePictures(response.items);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load ignored chats"
      );
      console.error("Error loading ignored chats:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchProfilePictures = async (chatsToFetch: Chat[]) => {
    // Fetch profile pictures for chats (in background, don't block UI)
    for (const chat of chatsToFetch) {
      // Skip if already cached
      if (profilePictures[chat.provider_id]) continue;

      try {
        const attendee = await getChatAttendee(chat.id, chat.provider_id);
        if (attendee.picture_url) {
          setProfilePictures((prev) => ({
            ...prev,
            [chat.provider_id]: attendee.picture_url!,
          }));
        }
      } catch (err) {
        // Silently fail - will use fallback avatar
        console.log(`Could not fetch profile picture for ${chat.provider_id}`);
      }
    }
  };

  const handleUnignoreChat = async (
    chatId: string,
    event: React.MouseEvent
  ) => {
    event.stopPropagation();

    try {
      await unignoreChat(chatId);
      // Remove the chat from the list
      setChats((prevChats) => prevChats.filter((c) => c.id !== chatId));
    } catch (err) {
      console.error("Failed to unignore chat:", err);
      alert("Failed to unignore chat. Please try again.");
    }
  };

  const formatTimestamp = (timestamp: string | null) => {
    if (!timestamp) return "No messages";
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m`;
    if (diffHours < 24) return `${diffHours}h`;
    if (diffDays < 7) return `${diffDays}d`;
    return date.toLocaleDateString();
  };

  useEffect(() => {
    loadIgnoredChats();
  }, []);

  return (
    <ProtectedRoute>
      <div className="h-screen bg-gradient-to-br from-zinc-50 to-zinc-100 dark:from-zinc-950 dark:to-black flex flex-col overflow-hidden diagonal-bg">
        <AppHeader />

        {/* Main Content */}
        <div className="flex-1 flex overflow-hidden w-full">
          {/* Ignored Chats List */}
          <div className="w-96 bg-white dark:bg-zinc-900 border-r border-zinc-200 dark:border-zinc-800 flex flex-col shadow-xl overflow-hidden">
            {/* Header */}
            <div className="p-4 border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/50">
              <div className="flex items-center gap-3">
                <button
                  onClick={() => router.push("/chats")}
                  className="p-2 rounded-lg hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-colors"
                  aria-label="Back to chats"
                >
                  <ArrowLeft className="w-5 h-5 text-zinc-700 dark:text-zinc-300" />
                </button>
                <div>
                  <h1 className="text-xl font-bold text-zinc-900 dark:text-white">
                    Ignored Chats
                  </h1>
                  <p className="text-sm text-zinc-600 dark:text-zinc-400">
                    Manage chats you've ignored
                  </p>
                </div>
              </div>
            </div>

            {/* Chat List */}
            <div className="flex-1 overflow-y-auto min-h-0">
              {loading ? (
                <div className="flex items-center justify-center py-20">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
                    <p className="text-sm text-zinc-600 dark:text-zinc-400">
                      Loading ignored chats...
                    </p>
                  </div>
                </div>
              ) : error ? (
                <div className="flex items-center justify-center py-20 p-4">
                  <div className="text-center">
                    <p className="text-sm text-red-600 dark:text-red-400 mb-2">
                      {error}
                    </p>
                    <button
                      onClick={loadIgnoredChats}
                      className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      Try again
                    </button>
                  </div>
                </div>
              ) : chats.length === 0 ? (
                <div className="flex items-center justify-center py-20 p-4">
                  <div className="text-center">
                    <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center">
                      <span className="text-4xl">🔇</span>
                    </div>
                    <h2 className="text-lg font-semibold text-zinc-900 dark:text-white mb-2">
                      No ignored chats
                    </h2>
                    <p className="text-sm text-zinc-600 dark:text-zinc-400">
                      Chats you ignore will appear here
                    </p>
                  </div>
                </div>
              ) : (
                <>
                  {chats.map((chat) => {
                    const profilePic = profilePictures[chat.provider_id];

                    return (
                      <div
                        key={chat.id}
                        className="w-full border-b border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-all"
                      >
                        <div className="flex items-center">
                          <div className="flex-1 min-w-0 p-4">
                            <div className="flex items-center gap-3 min-w-0">
                              <div className="relative flex-shrink-0">
                                {profilePic ? (
                                  <img
                                    src={profilePic}
                                    alt={chat.name || "Profile"}
                                    className="w-12 h-12 rounded-full object-cover shadow-lg opacity-60"
                                    onError={(e) => {
                                      e.currentTarget.style.display = "none";
                                      const fallback = e.currentTarget
                                        .nextElementSibling as HTMLElement;
                                      if (fallback)
                                        fallback.style.display = "flex";
                                    }}
                                  />
                                ) : null}
                                <div
                                  className="w-12 h-12 rounded-full bg-slate-700 flex items-center justify-center text-white text-xl font-bold shadow-lg opacity-60"
                                  style={{
                                    display: profilePic ? "none" : "flex",
                                  }}
                                >
                                  {chat.name?.charAt(0).toUpperCase() || "?"}
                                </div>
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center justify-between gap-2 mb-1 min-w-0">
                                  <h3 className="font-semibold truncate flex-1 min-w-0 text-zinc-700 dark:text-zinc-300">
                                    {chat.name || "Unnamed Chat"}
                                  </h3>
                                  <span className="text-xs text-zinc-500 dark:text-zinc-400 flex-shrink-0 whitespace-nowrap">
                                    {formatTimestamp(chat.timestamp)}
                                  </span>
                                </div>
                                <p className="text-sm text-zinc-500 dark:text-zinc-400 truncate">
                                  Ignored chat
                                </p>
                              </div>
                            </div>
                          </div>
                          <div className="flex-shrink-0 px-2">
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <button
                                  className="p-2 rounded-lg hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-colors"
                                  aria-label="Chat options"
                                >
                                  <MoreVertical className="w-5 h-5 text-zinc-600 dark:text-zinc-400" />
                                </button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem
                                  onClick={(e) =>
                                    handleUnignoreChat(chat.id, e as any)
                                  }
                                  className="cursor-pointer"
                                >
                                  Unignore Chat
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </>
              )}
            </div>
          </div>

          {/* Info Panel */}
          <div className="flex-1 bg-zinc-50 dark:bg-zinc-950">
            {/* Reserved for future features */}
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
