"use client";

import { useState, useRef, KeyboardEvent } from "react";
import {
  InputGroup,
  InputGroupAddon,
  InputGroupButton,
  InputGroupTextarea,
} from "@/components/ui/input-group";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ChevronDown, Loader2, Paperclip, Send } from "lucide-react";
import { ApiError, AssistMode, generateSuggestedMessage } from "@/lib/api";
import { useAiConfig } from "@/contexts/AiConfigContext";

interface MessageInputProps {
  onSendMessage: (text: string, attachments: File[]) => Promise<void>;
  disabled?: boolean;
  chatId?: string;
  assistMode: AssistMode;
  onAssistModeChange: (mode: AssistMode) => Promise<void>;
}

const MODE_LABELS: Record<AssistMode, string> = {
  manual: "Manual",
  "ai-assisted": "AI Assisted",
  autopilot: "Autopilot",
};

export function MessageInput({
  onSendMessage,
  disabled,
  chatId,
  assistMode,
  onAssistModeChange,
}: MessageInputProps) {
  const [message, setMessage] = useState("");
  const [attachments, setAttachments] = useState<File[]>([]);
  const [sending, setSending] = useState(false);
  const [suggesting, setSuggesting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [modeUpdating, setModeUpdating] = useState(false);
  const [modeError, setModeError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { prompt: aiPrompt, isLoaded: aiConfigLoaded } = useAiConfig();

  const handleSend = async () => {
    if (
      (!message.trim() && attachments.length === 0) ||
      sending ||
      suggesting ||
      disabled
    ) {
      return;
    }

    setSending(true);
    setError(null);
    try {
      await onSendMessage(message.trim(), attachments);
      setMessage("");
      setAttachments([]);
    } catch (error) {
      console.error("Failed to send message:", error);
      setError(
        error instanceof Error ? error.message : "Failed to send message"
      );
    } finally {
      setSending(false);
    }
  };

  const handleGenerateSuggestion = async () => {
    if (assistMode !== "ai-assisted") {
      return;
    }
    if (suggesting || sending || disabled) {
      return;
    }
    if (!chatId) {
      setError("Select a chat to request a suggestion.");
      return;
    }
    if (!aiConfigLoaded) {
      setError("AI prompt is still loading. Please try again.");
      return;
    }
    const prompt = aiPrompt.trim();
    if (!prompt) {
      setError("Set an AI prompt before requesting suggestions.");
      return;
    }

    setSuggesting(true);
    setError(null);

    try {
      const response = await generateSuggestedMessage(chatId, { prompt });
      setMessage(response.suggestion);
    } catch (err) {
      const friendlyMessage =
        err instanceof ApiError
          ? err.message
          : "Failed to generate suggestion. Please try again.";
      setError(friendlyMessage);
    } finally {
      setSuggesting(false);
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    setAttachments((prev) => [...prev, ...files]);
    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const removeAttachment = (index: number) => {
    setAttachments((prev) => prev.filter((_, i) => i !== index));
  };

  const handleAssistModeSelect = async (mode: AssistMode) => {
    if (mode === assistMode) {
      return;
    }
    setModeError(null);
    setModeUpdating(true);
    try {
      await onAssistModeChange(mode);
    } catch (err) {
      const friendly =
        err instanceof Error ? err.message : "Failed to update assist mode.";
      setModeError(friendly);
    } finally {
      setModeUpdating(false);
    }
  };

  return (
    <div className="border-t border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-4">
      {/* Attachment Preview */}
      {attachments.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-2">
          {attachments.map((file, index) => (
            <div
              key={index}
              className="flex items-center gap-2 px-3 py-1.5 bg-zinc-100 dark:bg-zinc-800 rounded-lg text-sm"
            >
              <span className="text-zinc-700 dark:text-zinc-300 truncate max-w-[150px]">
                {file.name}
              </span>
              <button
                onClick={() => removeAttachment(index)}
                className="text-zinc-500 hover:text-red-600 dark:text-zinc-400 dark:hover:text-red-400"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Input Area */}
      <div className="flex items-end gap-2">
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleFileSelect}
          className="hidden"
        />

        <InputGroup
          data-disabled={disabled || sending || suggesting}
          className="flex-1 items-end bg-zinc-100 dark:bg-zinc-900/60"
        >
          <InputGroupAddon className="gap-1 pl-2 pr-1 items-end">
            <InputGroupButton
              type="button"
              size="icon-sm"
              variant="ghost"
              onClick={() => fileInputRef.current?.click()}
              disabled={disabled || sending || suggesting}
              aria-label="Attach files"
            >
              <Paperclip className="size-4" />
            </InputGroupButton>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <InputGroupButton
                  type="button"
                  size="sm"
                  variant="outline"
                  className="gap-1 text-xs font-medium"
                  disabled={disabled || sending || suggesting || modeUpdating}
                >
                  {modeUpdating ? (
                    <Loader2 className="size-3.5 animate-spin" />
                  ) : (
                    <>
                      {MODE_LABELS[assistMode]}
                      <ChevronDown className="size-3.5 opacity-70" />
                    </>
                  )}
                </InputGroupButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="w-56">
                <DropdownMenuLabel>Response mode</DropdownMenuLabel>
                <DropdownMenuRadioGroup
                  value={assistMode}
                  onValueChange={(value) =>
                    handleAssistModeSelect(value as AssistMode)
                  }
                >
                  <DropdownMenuRadioItem value="manual">
                    <div className="flex flex-col text-left">
                      <span className="text-sm font-medium">Manual</span>
                      <span className="text-xs text-muted-foreground">
                        You craft every message yourself.
                      </span>
                    </div>
                  </DropdownMenuRadioItem>
                  <DropdownMenuRadioItem value="ai-assisted">
                    <div className="flex flex-col text-left">
                      <span className="text-sm font-medium">AI Assisted</span>
                      <span className="text-xs text-muted-foreground">
                        Get suggestions before sending.
                      </span>
                    </div>
                  </DropdownMenuRadioItem>
                  <DropdownMenuRadioItem value="autopilot">
                    <div className="flex flex-col text-left">
                      <span className="text-sm font-medium">Autopilot</span>
                      <span className="text-xs text-muted-foreground">
                        Let AI drive the conversation.
                      </span>
                    </div>
                  </DropdownMenuRadioItem>
                </DropdownMenuRadioGroup>
              </DropdownMenuContent>
            </DropdownMenu>

            {assistMode === "ai-assisted" && (
              <InputGroupButton
                type="button"
                size="sm"
                variant="secondary"
                className="text-xs font-semibold whitespace-nowrap"
                onClick={handleGenerateSuggestion}
                disabled={disabled || sending || suggesting}
                aria-label="Generate AI suggestion"
              >
                {suggesting ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  "Suggest"
                )}
              </InputGroupButton>
            )}
          </InputGroupAddon>

          <InputGroupTextarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Type a message..."
            disabled={disabled || sending || suggesting}
            rows={1}
            className="min-h-[44px] max-h-[140px] overflow-y-auto scrollbar-hide"
          />

          <InputGroupAddon align="inline-end" className="pr-3 items-end">
            <InputGroupButton
              type="button"
              size="icon-sm"
              className="bg-slate-700 text-white hover:bg-slate-800 dark:bg-slate-600 dark:hover:bg-slate-500"
              onClick={handleSend}
              disabled={
                (!message.trim() && attachments.length === 0) ||
                disabled ||
                sending ||
                suggesting
              }
              aria-label="Send message"
            >
              {sending ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Send className="size-4" />
              )}
            </InputGroupButton>
          </InputGroupAddon>
        </InputGroup>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-2 p-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-xs text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}

      {modeError && (
        <div className="mt-2 p-2 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
          <p className="text-xs text-amber-700 dark:text-amber-400">
            {modeError}
          </p>
        </div>
      )}

      {assistMode === "autopilot" && (
        <p className="mt-2 text-xs text-blue-600 dark:text-blue-400">
          Autopilot will reply automatically when new messages arrive. You can
          still send manual responses anytime.
        </p>
      )}

      {/* Hint Text */}
      {!error && (
        <p className="mt-2 text-xs text-zinc-500 dark:text-zinc-400">
          Press Enter to send, Shift+Enter for new line
        </p>
      )}
    </div>
  );
}
