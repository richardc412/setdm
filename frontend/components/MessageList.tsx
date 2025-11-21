import { Message } from "@/lib/api";

interface MessageListProps {
  messages: Message[];
  loading: boolean;
}

export function MessageList({ messages, loading }: MessageListProps) {
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();
    
    if (isToday) {
      return date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
      });
    }
    
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);
    const isYesterday = date.toDateString() === yesterday.toDateString();
    
    if (isYesterday) {
      return `Yesterday ${date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
      })}`;
    }
    
    return date.toLocaleString('en-US', { 
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  const renderAttachment = (attachment: any, index: number) => {
    if (!attachment || !attachment.type) return null;

    const type = attachment.type;

    switch (type) {
      case 'img':
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
                🖼️ Image {attachment.unavailable ? '(unavailable)' : ''}
              </div>
            )}
          </div>
        );
      case 'video':
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
                🎥 Video {attachment.gif ? '(GIF) ' : ''}{attachment.unavailable ? '(unavailable)' : ''}
              </div>
            )}
          </div>
        );
      case 'audio':
        return (
          <div key={index} className="mt-2">
            {attachment.url && !attachment.unavailable ? (
              <audio src={attachment.url} controls className="max-w-xs" />
            ) : (
              <div className="px-3 py-2 bg-zinc-100 dark:bg-zinc-800 rounded-lg text-sm text-zinc-600 dark:text-zinc-400">
                🎵 {attachment.voice_note ? 'Voice note' : 'Audio'} {attachment.unavailable ? '(unavailable)' : ''}
              </div>
            )}
          </div>
        );
      case 'file':
        return (
          <div key={index} className="mt-2">
            <div className="px-3 py-2 bg-zinc-100 dark:bg-zinc-800 rounded-lg text-sm text-zinc-600 dark:text-zinc-400">
              📎 {attachment.file_name || 'File'} {attachment.unavailable ? '(unavailable)' : ''}
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
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            Loading messages...
          </p>
        </div>
      </div>
    );
  }

  if (messages.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="text-4xl mb-2">💬</div>
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            No messages yet
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((message) => {
        const isSender = message.is_sender === 1;
        
        return (
          <div
            key={message.id}
            className={`flex ${isSender ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[70%] ${
                isSender
                  ? 'bg-blue-600 text-white'
                  : 'bg-white dark:bg-zinc-800 text-zinc-900 dark:text-white'
              } rounded-2xl px-4 py-2 shadow-sm`}
            >
              {/* Message text */}
              {message.text && (
                <p className="text-sm whitespace-pre-wrap break-words">
                  {message.text}
                </p>
              )}
              
              {/* Attachments */}
              {message.attachments && message.attachments.length > 0 && (
                <div>
                  {message.attachments.map((attachment, index) =>
                    renderAttachment(attachment, index)
                  )}
                </div>
              )}
              
              {/* Reactions */}
              {message.reactions && message.reactions.length > 0 && (
                <div className="flex gap-1 mt-1">
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
              
              {/* Timestamp and status */}
              <div
                className={`flex items-center gap-1 mt-1 text-xs ${
                  isSender
                    ? 'text-blue-100'
                    : 'text-zinc-500 dark:text-zinc-400'
                }`}
              >
                <span>{formatTimestamp(message.timestamp)}</span>
                {message.edited === 1 && <span>· Edited</span>}
                {isSender && message.seen === 1 && <span>· Seen</span>}
                {isSender && message.delivered === 1 && message.seen === 0 && (
                  <span>· Delivered</span>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

