"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

interface AiConfigContextValue {
  prompt: string;
  setPrompt: (value: string) => void;
  isLoaded: boolean;
}

const AiConfigContext = createContext<AiConfigContextValue | undefined>(
  undefined
);

const STORAGE_KEY = "ai-assist-prompt";

export function AiConfigProvider({ children }: { children: ReactNode }) {
  const [prompt, setPromptState] = useState("");
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    try {
      const saved = window.localStorage.getItem(STORAGE_KEY);
      if (saved) {
        setPromptState(saved);
      }
    } catch (err) {
      console.warn("Failed to load AI prompt from storage:", err);
    } finally {
      setIsLoaded(true);
    }
  }, []);

  const setPrompt = useCallback((value: string) => {
    setPromptState(value);
    if (typeof window === "undefined") {
      return;
    }
    try {
      window.localStorage.setItem(STORAGE_KEY, value);
    } catch (err) {
      console.warn("Failed to persist AI prompt:", err);
    }
  }, []);

  const value = useMemo(
    () => ({ prompt, setPrompt, isLoaded }),
    [prompt, setPrompt, isLoaded]
  );

  return (
    <AiConfigContext.Provider value={value}>
      {children}
    </AiConfigContext.Provider>
  );
}

export function useAiConfig() {
  const ctx = useContext(AiConfigContext);
  if (!ctx) {
    throw new Error("useAiConfig must be used within AiConfigProvider");
  }
  return ctx;
}

