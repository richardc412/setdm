"use client";

import ProtectedRoute from "@/components/ProtectedRoute";
import AppHeader from "@/components/AppHeader";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import {
  getChats,
  Chat,
  ChatFilters,
  getChatMessages,
  Message,
  markChatAsRead,
  getChatAttendee,
  Attendee,
  sendMessage,
} from "@/lib/api";
import { realtimeClient, MessageEventPayload } from "@/lib/realtime";
import { MessageList } from "@/components/MessageList";
import { MessageInput } from "@/components/MessageInput";

const sortChatsByPriority = (items: Chat[]) => {
  return [...items].sort((a, b) => {
    if (a.is_read !== b.is_read) {
      return a.is_read ? 1 : -1;
    }
    const timeA = a.timestamp ? new Date(a.timestamp).getTime() : 0;
    const timeB = b.timestamp ? new Date(b.timestamp).getTime() : 0;
    return timeB - timeA;
  });
};

export default function ChatsPage() {
  const router = useRouter();
  const [chats, setChats] = useState<Chat[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedChat, setSelectedChat] = useState<Chat | null>(null);
  const [filters, setFilters] = useState<ChatFilters>({
    limit: 50,
    offset: 0,
  });
  const [hasMore, setHasMore] = useState(false);

  // Message state
  const [messages, setMessages] = useState<Message[]>([]);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [messagesError, setMessagesError] = useState<string | null>(null);

  // Profile picture cache
  const [profilePictures, setProfilePictures] = useState<
    Record<string, string>
  >({});

  const selectedChatRef = useRef<Chat | null>(null);
  const loadChatsRef = useRef<((loadMore?: boolean) => Promise<void>) | null>(
    null
  );

  const scrollMessagesToBottom = () => {
    if (typeof window === "undefined") return;

    window.setTimeout(() => {
      const messagesContainer = document.getElementById("messages-container");
      if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
      }
    }, 100);
  };

  const normalizeRealtimeMessage = (payload: MessageEventPayload): Message =>
    ({
      ...payload,
    } as Message);

  const loadChats = async (loadMore = false) => {
    try {
      setLoading(true);
      setError(null);

      const offset = loadMore ? chats.length : 0;
      const filterParams = { ...filters, offset };
      const response = await getChats(filterParams);

      if (loadMore) {
        setChats((prev) => sortChatsByPriority([...prev, ...response.items]));
      } else {
        const sortedChats = sortChatsByPriority(response.items);
        setChats(sortedChats);
        fetchProfilePictures(sortedChats);
      }

      // Always fetch profile pictures for newly loaded chats
      if (loadMore) {
        fetchProfilePictures(response.items);
      }

      // Check if there are more chats to load
      const limit = filters.limit ?? 50;
      setHasMore(response.items.length === limit);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load chats");
      console.error("Error loading chats:", err);
    } finally {
      setLoading(false);
    }
  };

  loadChatsRef.current = loadChats;

  useEffect(() => {
    selectedChatRef.current = selectedChat;
  }, [selectedChat]);

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

  const loadMessages = async (chatId: string) => {
    try {
      setMessagesLoading(true);
      setMessagesError(null);

      const response = await getChatMessages(chatId, {
        limit: 100,
        order_desc: false, // Get oldest first for better UX
      });

      setMessages(response.items);

      scrollMessagesToBottom();
    } catch (err) {
      setMessagesError(
        err instanceof Error ? err.message : "Failed to load messages"
      );
      console.error("Error loading messages:", err);
    } finally {
      setMessagesLoading(false);
    }
  };

  const handleChatSelect = async (chat: Chat) => {
    setSelectedChat(chat);
    loadMessages(chat.id);

    // Mark chat as read if it's unread
    if (!chat.is_read) {
      try {
        await markChatAsRead(chat.id);
        // Update the chat in the local state
        setChats((prevChats) =>
          prevChats.map((c) => (c.id === chat.id ? { ...c, is_read: true } : c))
        );
      } catch (err) {
        console.error("Failed to mark chat as read:", err);
        // Don't show error to user, this is a background operation
      }
    }
  };

  const handleSendMessage = async (text: string, attachments: File[]) => {
    if (!selectedChat) return;

    try {
      // Send message via Unipile API
      const response = await sendMessage(selectedChat.id, {
        text,
        attachments: attachments.length > 0 ? attachments : undefined,
      });

      // Optimistically add the message to local state immediately (201 response)
      const optimisticMessage: Message = {
        object: "Message",
        id: response.message_id || `temp-${Date.now()}`,
        account_id: selectedChat.account_id,
        chat_id: selectedChat.id,
        chat_provider_id: selectedChat.provider_id,
        provider_id: response.message_id || `temp-${Date.now()}`,
        sender_id: "self",
        sender_attendee_id: "self",
        text: text || null,
        timestamp: new Date().toISOString(),
        is_sender: 1,
        attachments:
          attachments.length > 0
            ? attachments.map((file) => ({
                type: "file",
                file_name: file.name,
                file_size: file.size,
                mimetype: file.type,
              }))
            : [],
        reactions: [],
        seen: 0,
        seen_by: {},
        hidden: 0,
        deleted: 0,
        edited: 0,
        is_event: 0,
        delivered: 1,
        behavior: null,
        original: text || "",
      };

      // Add message to local state
      setMessages((prev) => [...prev, optimisticMessage]);

      // Scroll to bottom to show the new message
      scrollMessagesToBottom();

      // Reload messages in background to sync with server
      // Wait longer for backend sync to complete (it triggers immediately after send)
      const sentMessageId = response.message_id;
      setTimeout(async () => {
        try {
          const messagesResponse = await getChatMessages(selectedChat.id, {
            limit: 100,
            order_desc: false,
          });

          // Check if our sent message is in the synced messages
          const hasOurMessage = messagesResponse.items.some(
            (msg) =>
              msg.id === sentMessageId ||
              (msg.text === text &&
                msg.is_sender === 1 &&
                Math.abs(new Date(msg.timestamp).getTime() - Date.now()) <
                  10000)
          );

          if (hasOurMessage) {
            // Message is synced, replace with server data
            setMessages(messagesResponse.items);
          } else {
            // Message not synced yet, merge optimistic with synced messages
            // Remove duplicates and keep optimistic message
            const messageIds = new Set(messagesResponse.items.map((m) => m.id));
            if (!messageIds.has(optimisticMessage.id)) {
              setMessages([...messagesResponse.items, optimisticMessage]);
            } else {
              setMessages(messagesResponse.items);
            }
          }

          // Scroll to bottom after reloading
          scrollMessagesToBottom();

          // Also refresh the chat list
          loadChats();
        } catch (error) {
          console.error("Failed to sync messages:", error);
          // On error, keep the optimistic message
        }
      }, 2000); // Increased to 2 seconds to give backend sync time to complete
    } catch (err) {
      console.error("Failed to send message:", err);
      throw err; // Let the MessageInput component handle the error
    }
  };

  useEffect(() => {
    loadChats();
  }, [filters.is_read]);

  useEffect(() => {
    if (typeof window === "undefined") return;

    realtimeClient.connect();
    const unsubscribe = realtimeClient.on<MessageEventPayload>(
      "message:new",
      (payload) => {
        let chatFound = false;
        setChats((prevChats) => {
          const idx = prevChats.findIndex(
            (chat) => chat.id === payload.chat_id
          );
          if (idx === -1) {
            return prevChats;
          }
          chatFound = true;
          const chat = prevChats[idx];
          const isActive = selectedChatRef.current?.id === payload.chat_id;
          const updatedChat: Chat = {
            ...chat,
            timestamp: payload.timestamp,
            is_read: isActive ? true : false,
            unread_count: isActive
              ? 0
              : (typeof chat.unread_count === "number"
                  ? chat.unread_count
                  : 0) + 1,
          };
          const next = [...prevChats];
          next[idx] = updatedChat;
          return sortChatsByPriority(next);
        });

        if (!chatFound) {
          loadChatsRef.current?.();
        }

        if (selectedChatRef.current?.id === payload.chat_id) {
          setSelectedChat((prev) =>
            prev
              ? { ...prev, timestamp: payload.timestamp, is_read: true }
              : prev
          );
          setMessages((prev) => {
            if (prev.some((msg) => msg.id === payload.id)) {
              return prev;
            }
            return [...prev, normalizeRealtimeMessage(payload)];
          });
          scrollMessagesToBottom();
        }
      }
    );

    return () => {
      unsubscribe();
    };
  }, []);

  const handleFilterChange = (key: keyof ChatFilters, value: any) => {
    setFilters((prev) => ({ ...prev, [key]: value, offset: 0 }));
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
    if (diffMins < 60) return `${diffMins}m`;
    if (diffHours < 24) return `${diffHours}h`;
    if (diffDays < 7) return `${diffDays}d`;
    return date.toLocaleDateString();
  };

  const getLastMessagePreview = (chat: Chat) => {
    // Try to get the last message for this chat from our loaded messages
    // For now, we'll just show a placeholder
    // In a real app, you'd fetch this from the API or cache
    return "Tap to view messages";
  };

  return (
    <ProtectedRoute>
      <div className="h-screen bg-gradient-to-br from-zinc-50 to-zinc-100 dark:from-zinc-950 dark:to-black flex flex-col overflow-hidden diagonal-bg">
        <AppHeader />

        {/* Main Content */}
        <div className="flex-1 flex overflow-hidden max-w-7xl mx-auto w-full">
          {/* Sidebar - Chat List */}
          <aside className="w-96 bg-white dark:bg-zinc-900 border-r border-zinc-200 dark:border-zinc-800 flex flex-col shadow-xl overflow-hidden">
            {/* Filters */}
            <div className="p-3 border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/50">
              <div className="flex gap-2">
                <button
                  onClick={() => handleFilterChange("is_read", undefined)}
                  className={`flex-1 px-3 py-2 rounded-lg text-sm font-semibold transition-all ${
                    filters.is_read === undefined
                      ? "bg-blue-600 text-white shadow-md"
                      : "bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200 dark:hover:bg-zinc-700"
                  }`}
                >
                  All
                </button>
                <button
                  onClick={() => handleFilterChange("is_read", false)}
                  className={`flex-1 px-3 py-2 rounded-lg text-sm font-semibold transition-all ${
                    filters.is_read === false
                      ? "bg-blue-600 text-white shadow-md"
                      : "bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200 dark:hover:bg-zinc-700"
                  }`}
                >
                  Unread
                </button>
              </div>
            </div>

            {/* Chat List */}
            <div className="flex-1 overflow-y-auto min-h-0">
              {loading && chats.length === 0 ? (
                <div className="flex items-center justify-center py-20">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
                    <p className="text-sm text-zinc-600 dark:text-zinc-400">
                      Loading chats...
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
                      onClick={() => loadChats()}
                      className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      Try again
                    </button>
                  </div>
                </div>
              ) : chats.length === 0 ? (
                <div className="flex items-center justify-center py-20 p-4">
                  <p className="text-sm text-zinc-600 dark:text-zinc-400 text-center">
                    No chats found
                  </p>
                </div>
              ) : (
                <>
                  {chats.map((chat) => {
                    const profilePic = profilePictures[chat.provider_id];

                    return (
                      <button
                        key={chat.id}
                        onClick={() => handleChatSelect(chat)}
                        className={`w-full p-4 border-b border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-all text-left ${
                          selectedChat?.id === chat.id
                            ? "bg-blue-50 dark:bg-blue-900/20 border-l-4 border-l-blue-600"
                            : ""
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <div className="relative flex-shrink-0">
                            {profilePic ? (
                              <img
                                src={profilePic}
                                alt={chat.name || "Profile"}
                                className="w-12 h-12 rounded-full object-cover shadow-lg"
                                onError={(e) => {
                                  // Fallback to gradient avatar if image fails to load
                                  e.currentTarget.style.display = "none";
                                  const fallback = e.currentTarget
                                    .nextElementSibling as HTMLElement;
                                  if (fallback) fallback.style.display = "flex";
                                }}
                              />
                            ) : null}
                            <div
                              className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white text-xl font-bold shadow-lg"
                              style={{ display: profilePic ? "none" : "flex" }}
                            >
                              {chat.name?.charAt(0).toUpperCase() || "?"}
                            </div>
                            {!chat.is_read && (
                              <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-blue-600 border-2 border-white dark:border-zinc-900"></span>
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between gap-2 mb-1">
                              <h3
                                className={`font-semibold truncate ${
                                  !chat.is_read
                                    ? "text-zinc-900 dark:text-white"
                                    : "text-zinc-700 dark:text-zinc-300"
                                }`}
                              >
                                {chat.name || "Unnamed Chat"}
                              </h3>
                              <span className="text-xs text-zinc-500 dark:text-zinc-400 flex-shrink-0">
                                {formatTimestamp(chat.timestamp)}
                              </span>
                            </div>
                            <p
                              className={`text-sm truncate ${
                                !chat.is_read
                                  ? "text-zinc-600 dark:text-zinc-300 font-medium"
                                  : "text-zinc-500 dark:text-zinc-400"
                              }`}
                            >
                              {getLastMessagePreview(chat)}
                            </p>
                          </div>
                        </div>
                      </button>
                    );
                  })}
                  {hasMore && (
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
          <main className="flex-1 flex items-center justify-center bg-zinc-100 dark:bg-zinc-950 p-4 overflow-hidden">
            {selectedChat ? (
              <div className="w-full max-w-md h-full max-h-full flex flex-col bg-white dark:bg-zinc-900 rounded-2xl shadow-2xl overflow-hidden border border-zinc-200 dark:border-zinc-800">
                {/* Chat Header */}
                <div className="bg-gradient-to-r from-purple-600 to-pink-600 px-4 py-3 shadow-lg">
                  <div className="flex items-center gap-3">
                    {profilePictures[selectedChat.provider_id] ? (
                      <img
                        src={profilePictures[selectedChat.provider_id]}
                        alt={selectedChat.name || "Profile"}
                        className="w-10 h-10 rounded-full object-cover border-2 border-white/30 shadow-md"
                        onError={(e) => {
                          e.currentTarget.style.display = "none";
                          const fallback = e.currentTarget
                            .nextElementSibling as HTMLElement;
                          if (fallback) fallback.style.display = "flex";
                        }}
                      />
                    ) : null}
                    <div
                      className="w-10 h-10 rounded-full bg-white/20 backdrop-blur-lg flex items-center justify-center text-white text-lg font-bold"
                      style={{
                        display: profilePictures[selectedChat.provider_id]
                          ? "none"
                          : "flex",
                      }}
                    >
                      {selectedChat.name?.charAt(0).toUpperCase() || "?"}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h2 className="text-base font-bold text-white truncate">
                        {selectedChat.name || "Unnamed Chat"}
                      </h2>
                      <p className="text-xs text-white/80">Instagram</p>
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
                  <>
                    <div
                      id="messages-container"
                      className="flex-1 overflow-y-auto bg-zinc-50 dark:bg-zinc-900"
                    >
                      <MessageList
                        messages={messages}
                        loading={messagesLoading}
                      />
                    </div>

                    {/* Message Input */}
                    <MessageInput
                      onSendMessage={handleSendMessage}
                      disabled={messagesLoading}
                    />
                  </>
                )}
              </div>
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center max-w-md p-8">
                  <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center shadow-2xl">
                    <span className="text-5xl">💬</span>
                  </div>
                  <h2 className="text-2xl font-bold text-zinc-900 dark:text-white mb-2">
                    Select a chat
                  </h2>
                  <p className="text-zinc-600 dark:text-zinc-400">
                    Choose a conversation to start messaging
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
