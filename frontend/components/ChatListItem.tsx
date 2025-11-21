import { Chat } from "@/lib/api";

interface ChatListItemProps {
  chat: Chat;
  isSelected: boolean;
  onClick: () => void;
}

export function ChatListItem({ chat, isSelected, onClick }: ChatListItemProps) {
  const getPlatformEmoji = () => {
    return "📷"; // Instagram only
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
    <button
      onClick={onClick}
      className={`w-full p-4 border-b border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors text-left ${
        isSelected ? "bg-blue-50 dark:bg-blue-900/20" : ""
      }`}
    >
      <div className="flex items-start gap-3">
        <div className="text-2xl flex-shrink-0">
          {getPlatformEmoji()}
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
  );
}

