"use client";

import { useAuth } from "@/contexts/AuthContext";
import ProtectedRoute from "@/components/ProtectedRoute";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getChats, Chat, ChatFilters, getChatMessages, Message } from "@/lib/api";
import { MessageList } from "@/components/MessageList";

export default function ChatsPage() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [chats, setChats] = useState<Chat[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedChat, setSelectedChat] = useState<Chat | null>(null);
  const [filters, setFilters] = useState<ChatFilters>({
    limit: 50,
    account_type: "INSTAGRAM", // Only Instagram messages
  });
  const [cursor, setCursor] = useState<string | null>(null);
  
  // Message state
  const [messages, setMessages] = useState<Message[]>([]);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [messagesError, setMessagesError] = useState<string | null>(null);

  const loadChats = async (loadMore = false) => {
    try {
      setLoading(true);
      setError(null);
      
      const filterParams = loadMore && cursor ? { ...filters, cursor } : filters;
      const response = await getChats(filterParams);
      
      if (loadMore) {
        setChats((prev) => [...prev, ...response.items]);
      } else {
        setChats(response.items);
      }
      
      setCursor(response.cursor);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load chats");
      console.error("Error loading chats:", err);
    } finally {
      setLoading(false);
    }
  };

  const loadMessages = async (chatId: string) => {
    try {
      setMessagesLoading(true);
      setMessagesError(null);
      
      const response = await getChatMessages(chatId, { limit: 20 });
      
      // Reverse to show oldest first (messages come in descending order)
      setMessages(response.items.reverse());
    } catch (err) {
      setMessagesError(err instanceof Error ? err.message : "Failed to load messages");
      console.error("Error loading messages:", err);
    } finally {
      setMessagesLoading(false);
    }
  };

  const handleChatSelect = (chat: Chat) => {
    setSelectedChat(chat);
    loadMessages(chat.id);
  };

  useEffect(() => {
    loadChats();
  }, [filters.unread]);

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  const handleFilterChange = (key: keyof ChatFilters, value: any) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setSelectedChat(null);
  };

  const getPlatformEmoji = (accountType: string) => {
    return accountType === "INSTAGRAM" ? "📷" : "💬";
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
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-zinc-50 dark:bg-black flex flex-col">
        {/* Sticky Header */}
        <header className="sticky top-0 z-50 bg-white dark:bg-zinc-900 border-b border-zinc-200 dark:border-zinc-800 shadow-sm">
          <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <button
                  onClick={() => router.push("/dashboard")}
                  className="text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors"
                >
                  ← Back
                </button>
                <div className="flex items-center gap-2">
                  <span className="text-2xl">📷</span>
                  <h1 className="text-2xl font-bold text-zinc-900 dark:text-white">
                    Instagram DMs
                  </h1>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-sm text-zinc-600 dark:text-zinc-400">
                  {user?.username}
                </span>
                <button
                  onClick={handleLogout}
                  className="px-4 py-2 rounded-lg bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-900 dark:text-white font-medium transition-colors"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Sidebar - Chat List */}
          <aside className="w-80 bg-white dark:bg-zinc-900 border-r border-zinc-200 dark:border-zinc-800 flex flex-col">
            {/* Filters */}
            <div className="p-4 border-b border-zinc-200 dark:border-zinc-800">
              <div className="flex gap-2">
                <button
                  onClick={() => handleFilterChange("unread", undefined)}
                  className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    filters.unread === undefined
                      ? "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
                      : "bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200 dark:hover:bg-zinc-700"
                  }`}
                >
                  All
                </button>
                <button
                  onClick={() => handleFilterChange("unread", true)}
                  className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    filters.unread === true
                      ? "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
                      : "bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200 dark:hover:bg-zinc-700"
                  }`}
                >
                  Unread
                </button>
              </div>
            </div>

            {/* Chat List */}
            <div className="flex-1 overflow-y-auto">
              {loading && chats.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
                    <p className="text-sm text-zinc-600 dark:text-zinc-400">
                      Loading chats...
                    </p>
                  </div>
                </div>
              ) : error ? (
                <div className="flex items-center justify-center h-full p-4">
                  <div className="text-center">
                    <p className="text-sm text-red-600 dark:text-red-400 mb-2">
                      {error}
                    </p>
                    <button
                      onClick={() => loadChats()}
                      className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      Try again
                    </button>
                  </div>
                </div>
              ) : chats.length === 0 ? (
                <div className="flex items-center justify-center h-full p-4">
                  <p className="text-sm text-zinc-600 dark:text-zinc-400 text-center">
                    No chats found
                  </p>
                </div>
              ) : (
                <>
                  {chats.map((chat) => (
                    <button
                      key={chat.id}
                      onClick={() => handleChatSelect(chat)}
                      className={`w-full p-4 border-b border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors text-left ${
                        selectedChat?.id === chat.id
                          ? "bg-blue-50 dark:bg-blue-900/20"
                          : ""
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <div className="text-2xl flex-shrink-0">
                          {getPlatformEmoji(chat.account_type)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-2 mb-1">
                            <h3
                              className={`font-medium truncate ${
                                chat.unread_count > 0
                                  ? "text-zinc-900 dark:text-white"
                                  : "text-zinc-700 dark:text-zinc-300"
                              }`}
                            >
                              {chat.name || "Unnamed Chat"}
                            </h3>
                            {chat.unread_count > 0 && (
                              <span className="flex-shrink-0 inline-flex items-center justify-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-600 text-white min-w-[20px]">
                                {chat.unread_count}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center justify-end">
                            <span className="text-xs text-zinc-500 dark:text-zinc-500">
                              {formatTimestamp(chat.timestamp)}
                            </span>
                          </div>
                        </div>
                      </div>
                    </button>
                  ))}
                  {cursor && (
                    <div className="p-4 border-t border-zinc-200 dark:border-zinc-800">
                      <button
                        onClick={() => loadChats(true)}
                        disabled={loading}
                        className="w-full px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-400 text-white font-medium transition-colors"
                      >
                        {loading ? "Loading..." : "Load More"}
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          </aside>

          {/* Main Chat Area */}
          <main className="flex-1 bg-zinc-50 dark:bg-black flex flex-col">
            {selectedChat ? (
              <>
                {/* Chat Header */}
                <div className="bg-white dark:bg-zinc-900 border-b border-zinc-200 dark:border-zinc-800 px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="text-2xl">
                      {getPlatformEmoji(selectedChat.account_type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h2 className="text-lg font-semibold text-zinc-900 dark:text-white truncate">
                        {selectedChat.name || "Unnamed Chat"}
                      </h2>
                      <p className="text-sm text-zinc-600 dark:text-zinc-400">
                        {selectedChat.account_type}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Messages Area */}
                {messagesError ? (
                  <div className="flex-1 flex items-center justify-center p-4">
                    <div className="text-center">
                      <p className="text-sm text-red-600 dark:text-red-400 mb-2">
                        {messagesError}
                      </p>
                      <button
                        onClick={() => loadMessages(selectedChat.id)}
                        className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                      >
                        Try again
                      </button>
                    </div>
                  </div>
                ) : (
                  <MessageList messages={messages} loading={messagesLoading} />
                )}
              </>
            ) : (
              <div className="h-full flex items-center justify-center">
                <div className="text-center max-w-md p-8">
                  <div className="text-6xl mb-4">💬</div>
                  <h2 className="text-2xl font-bold text-zinc-900 dark:text-white mb-2">
                    Select a chat
                  </h2>
                  <p className="text-zinc-600 dark:text-zinc-400">
                    Choose a conversation from the sidebar to view messages
                  </p>
                </div>
              </div>
            )}
          </main>
        </div>
      </div>
    </ProtectedRoute>
  );
}

