import { Message } from "@/lib/api";

interface MessageListProps {
  messages: Message[];
  loading: boolean;
}

export function MessageList({ messages, loading }: MessageListProps) {
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  };

  const formatDateHeader = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();

    if (isToday) {
      return "Today";
    }

    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);
    const isYesterday = date.toDateString() === yesterday.toDateString();

    if (isYesterday) {
      return "Yesterday";
    }

    // For older dates, show the full date
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: date.getFullYear() !== now.getFullYear() ? "numeric" : undefined,
    });
  };

  const getDateKey = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toDateString();
  };

  // Group messages by date
  const groupedMessages = messages.reduce((groups, message) => {
    const dateKey = getDateKey(message.timestamp);
    if (!groups[dateKey]) {
      groups[dateKey] = [];
    }
    groups[dateKey].push(message);
    return groups;
  }, {} as Record<string, Message[]>);

  const renderAttachment = (attachment: any, index: number) => {
    if (!attachment || !attachment.type) return null;

    const type = attachment.type;

    switch (type) {
      case "img":
        return (
          <div key={index} className="mt-2">
            {attachment.url && !attachment.unavailable ? (
              <img
                src={attachment.url}
                alt="Image attachment"
                className="max-w-xs rounded-lg"
              />
            ) : (
              <div className="px-3 py-2 bg-zinc-100 dark:bg-zinc-800 rounded-lg text-sm text-zinc-600 dark:text-zinc-400">
                🖼️ Image {attachment.unavailable ? "(unavailable)" : ""}
              </div>
            )}
          </div>
        );
      case "video":
        return (
          <div key={index} className="mt-2">
            {attachment.url && !attachment.unavailable ? (
              <video
                src={attachment.url}
                controls
                className="max-w-xs rounded-lg"
              />
            ) : (
              <div className="px-3 py-2 bg-zinc-100 dark:bg-zinc-800 rounded-lg text-sm text-zinc-600 dark:text-zinc-400">
                🎥 Video {attachment.gif ? "(GIF) " : ""}
                {attachment.unavailable ? "(unavailable)" : ""}
              </div>
            )}
          </div>
        );
      case "audio":
        return (
          <div key={index} className="mt-2">
            {attachment.url && !attachment.unavailable ? (
              <audio src={attachment.url} controls className="max-w-xs" />
            ) : (
              <div className="px-3 py-2 bg-zinc-100 dark:bg-zinc-800 rounded-lg text-sm text-zinc-600 dark:text-zinc-400">
                🎵 {attachment.voice_note ? "Voice note" : "Audio"}{" "}
                {attachment.unavailable ? "(unavailable)" : ""}
              </div>
            )}
          </div>
        );
      case "file":
        return (
          <div key={index} className="mt-2">
            <div className="px-3 py-2 bg-zinc-100 dark:bg-zinc-800 rounded-lg text-sm text-zinc-600 dark:text-zinc-400">
              📎 {attachment.file_name || "File"}{" "}
              {attachment.unavailable ? "(unavailable)" : ""}
            </div>
          </div>
        );
      default:
        return (
          <div key={index} className="mt-2">
            <div className="px-3 py-2 bg-zinc-100 dark:bg-zinc-800 rounded-lg text-sm text-zinc-600 dark:text-zinc-400">
              📎 {type} attachment
            </div>
          </div>
        );
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-3 border-slate-700 border-t-transparent mx-auto mb-3"></div>
          <p className="text-sm text-zinc-600 dark:text-zinc-400 font-medium">
            Loading messages...
          </p>
        </div>
      </div>
    );
  }

  if (messages.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center p-8">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-slate-700 flex items-center justify-center shadow-lg">
            <span className="text-3xl">💬</span>
          </div>
          <p className="text-sm text-zinc-600 dark:text-zinc-400 font-medium">
            No messages yet
          </p>
          <p className="text-xs text-zinc-500 dark:text-zinc-500 mt-1">
            Start the conversation!
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4">
      {Object.entries(groupedMessages).map(
        ([dateKey, dateMessages], groupIndex) => (
          <div key={dateKey} className={groupIndex > 0 ? "mt-8" : ""}>
            {/* Date separator */}
            <div className="flex items-center gap-3 mb-4">
              <div className="text-sm font-semibold text-zinc-700 dark:text-zinc-300">
                {formatDateHeader(dateMessages[0].timestamp)}
              </div>
              <div className="flex-1 h-px bg-zinc-300 dark:bg-zinc-700"></div>
            </div>

            {/* Messages for this date */}
            <div className="space-y-3">
              {dateMessages.map((message) => {
                const isSender = message.is_sender === 1;

                return (
                  <div
                    key={message.id}
                    className={`flex items-end gap-2 ${
                      isSender ? "justify-end" : "justify-start"
                    }`}
                  >
                    {/* Timestamp on left for received messages */}
                    {!isSender && (
                      <div className="text-[11px] text-zinc-500 dark:text-zinc-400 whitespace-nowrap mb-1">
                        {formatTime(message.timestamp)}
                        {message.edited === 1 && (
                          <span className="block text-[10px]">Edited</span>
                        )}
                      </div>
                    )}

                    <div
                      className={`relative max-w-[75%] ${
                        isSender
                          ? "bg-slate-700 text-white"
                          : "bg-white dark:bg-zinc-800 text-zinc-900 dark:text-white border border-zinc-200 dark:border-zinc-700"
                      } rounded-2xl px-4 py-2.5 shadow-md`}
                    >
                      {/* Message text */}
                      {message.text && (
                        <p className="text-[15px] leading-snug whitespace-pre-wrap break-words">
                          {message.text}
                        </p>
                      )}

                      {/* Attachments */}
                      {message.attachments &&
                        message.attachments.length > 0 && (
                          <div>
                            {message.attachments.map((attachment, index) =>
                              renderAttachment(attachment, index)
                            )}
                          </div>
                        )}

                      {/* Reactions */}
                      {message.reactions && message.reactions.length > 0 && (
                        <div className="flex gap-1 mt-1.5">
                          {message.reactions.map((reaction, index) => (
                            <span
                              key={index}
                              className="text-xs bg-white/20 dark:bg-black/20 rounded-full px-2 py-0.5"
                            >
                              {reaction.value}
                            </span>
                          ))}
                        </div>
                      )}
                      {isSender && message.sent_by_autopilot && (
                        <div className="absolute -bottom-3 -right-3 w-7 h-7 bg-white dark:bg-zinc-900 rounded-full flex items-center justify-center shadow-md border-2 border-white dark:border-zinc-900">
                          <img
                            src="/paper_airplane.svg"
                            alt="Autopilot"
                            className="w-4 h-4"
                          />
                        </div>
                      )}
                    </div>

                    {/* Timestamp on right for sent messages */}
                    {isSender && (
                      <div className="text-[11px] text-zinc-500 dark:text-zinc-400 whitespace-nowrap mb-1">
                        {formatTime(message.timestamp)}
                        {message.edited === 1 && (
                          <span className="block text-[10px]">Edited</span>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )
      )}
    </div>
  );
}
