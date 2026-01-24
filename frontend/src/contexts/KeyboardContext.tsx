import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react';

interface ShortcutHandler {
  key: string;
  handler: (event: KeyboardEvent) => void;
  description?: string;
}

interface KeyboardContextValue {
  registerShortcuts: (shortcuts: Record<string, (event: KeyboardEvent) => void>) => void;
  unregisterShortcuts: () => void;
  disableShortcuts: () => void;
  enableShortcuts: () => void;
  isEnabled: boolean;
  debugMode: boolean;
  setDebugMode: (enabled: boolean) => void;
}

const KeyboardContext = createContext<KeyboardContextValue | undefined>(undefined);

export function useKeyboard() {
  const context = useContext(KeyboardContext);
  if (!context) {
    throw new Error('useKeyboard must be used within KeyboardProvider');
  }
  return context;
}

interface KeyboardProviderProps {
  children: React.ReactNode;
}

export function KeyboardProvider({ children }: KeyboardProviderProps) {
  const [isEnabled, setIsEnabled] = useState(true);
  const [debugMode, setDebugMode] = useState(false);
  const shortcutsRef = useRef<Map<string, ShortcutHandler>>(new Map());
  const screenIdRef = useRef<number>(0);

  const isInputFocused = useCallback(() => {
    const activeElement = document.activeElement;
    if (!activeElement) return false;

    const tagName = activeElement.tagName.toLowerCase();
    const isEditable = activeElement.getAttribute('contenteditable') === 'true';

    return (
      tagName === 'input' ||
      tagName === 'textarea' ||
      tagName === 'select' ||
      isEditable
    );
  }, []);

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    // Don't intercept if shortcuts are disabled
    if (!isEnabled) return;

    // Don't intercept if user is typing in an input field
    if (isInputFocused()) return;

    // Don't intercept browser shortcuts (Ctrl/Cmd/Alt combinations)
    if (event.ctrlKey || event.metaKey || event.altKey) return;

    const key = event.key.toLowerCase();
    const handler = shortcutsRef.current.get(key);

    if (handler) {
      if (debugMode) {
        if (import.meta.env.DEV) console.log(`[KeyboardContext] Handling shortcut: ${key}`);
      }

      event.preventDefault();
      handler.handler(event);
    }
  }, [isEnabled, isInputFocused, debugMode]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);

  const registerShortcuts = useCallback((shortcuts: Record<string, (event: KeyboardEvent) => void>) => {
    const currentScreenId = ++screenIdRef.current;

    // Clear previous shortcuts
    shortcutsRef.current.clear();

    // Register new shortcuts
    Object.entries(shortcuts).forEach(([key, handler]) => {
      shortcutsRef.current.set(key.toLowerCase(), {
        key: key.toLowerCase(),
        handler,
      });
    });

    if (debugMode) {
      if (import.meta.env.DEV) console.log(`[KeyboardContext] Registered shortcuts:`, Array.from(shortcutsRef.current.keys()));
    }

    // Return cleanup function
    return () => {
      if (screenIdRef.current === currentScreenId) {
        shortcutsRef.current.clear();
      }
    };
  }, [debugMode]);

  const unregisterShortcuts = useCallback(() => {
    shortcutsRef.current.clear();
    if (debugMode) {
      if (import.meta.env.DEV) console.log('[KeyboardContext] Unregistered all shortcuts');
    }
  }, [debugMode]);

  const disableShortcuts = useCallback(() => {
    setIsEnabled(false);
    if (debugMode) {
      if (import.meta.env.DEV) console.log('[KeyboardContext] Shortcuts disabled');
    }
  }, [debugMode]);

  const enableShortcuts = useCallback(() => {
    setIsEnabled(true);
    if (debugMode) {
      if (import.meta.env.DEV) console.log('[KeyboardContext] Shortcuts enabled');
    }
  }, [debugMode]);

  const value: KeyboardContextValue = {
    registerShortcuts,
    unregisterShortcuts,
    disableShortcuts,
    enableShortcuts,
    isEnabled,
    debugMode,
    setDebugMode,
  };

  return (
    <KeyboardContext.Provider value={value}>
      {children}
    </KeyboardContext.Provider>
  );
}

// Hook for easy shortcut registration in components
export function useKeyboardShortcuts(
  shortcuts: Record<string, (event: KeyboardEvent) => void>,
  deps: React.DependencyList = []
) {
  const { registerShortcuts } = useKeyboard();

  useEffect(() => {
    const cleanup = registerShortcuts(shortcuts);
    return cleanup;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
}
