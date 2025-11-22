"use client";

import { useEffect, useState } from "react";
import ProtectedRoute from "@/components/ProtectedRoute";
import AppHeader from "@/components/AppHeader";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { useAiConfig } from "@/contexts/AiConfigContext";

export default function AiConfigPage() {
  const { prompt, setPrompt, isLoaded } = useAiConfig();
  const [value, setValue] = useState("");
  const [status, setStatus] = useState<"idle" | "saving" | "saved">("idle");

  useEffect(() => {
    if (isLoaded) {
      setValue(prompt);
    }
  }, [isLoaded, prompt]);

  const handleSave = () => {
    setStatus("saving");
    setPrompt(value.trim());
    setStatus("saved");
    setTimeout(() => setStatus("idle"), 2000);
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-b from-zinc-50 to-white dark:from-zinc-950 dark:to-black">
        <AppHeader />
        <main className="max-w-3xl mx-auto px-6 py-10">
          <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl shadow-xl p-8 space-y-6">
            <div>
              <h1 className="text-2xl font-semibold text-zinc-900 dark:text-white">
                AI Assistant Prompt
              </h1>
              <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-2">
                Define the guidance the AI agent should follow before crafting
                suggested replies. This text is sent with every suggestion
                request.
              </p>
            </div>

            <div className="space-y-3">
              <label
                htmlFor="aiPrompt"
                className="text-sm font-medium text-zinc-700 dark:text-zinc-200"
              >
                System prompt
              </label>
              <Textarea
                id="aiPrompt"
                value={value}
                onChange={(event) => setValue(event.target.value)}
                placeholder="Example: You are a friendly SDR focused on booking intro meetings..."
                rows={8}
                className="resize-none"
              />
              <p className="text-xs text-muted-foreground">
                Tip: Mention your product value prop, tone, and desired call to
                action.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <Button onClick={handleSave} disabled={status === "saving"}>
                {status === "saving" ? "Saving..." : "Save Prompt"}
              </Button>
              {status === "saved" && (
                <span className="text-sm text-green-600 dark:text-green-400">
                  Prompt saved
                </span>
              )}
            </div>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}

