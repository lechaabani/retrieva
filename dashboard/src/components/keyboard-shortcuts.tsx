"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Keyboard, Command, ArrowRight, X } from "lucide-react";

interface ShortcutDef {
  keys: string[];
  label: string;
}

interface ShortcutSection {
  title: string;
  shortcuts: ShortcutDef[];
}

const shortcutSections: ShortcutSection[] = [
  {
    title: "Navigation",
    shortcuts: [
      { keys: ["g", "h"], label: "Aller au Dashboard" },
      { keys: ["g", "d"], label: "Aller aux Documents" },
      { keys: ["g", "c"], label: "Aller aux Collections" },
      { keys: ["g", "p"], label: "Aller au Playground" },
      { keys: ["g", "a"], label: "Aller aux Analytics" },
      { keys: ["g", "s"], label: "Aller aux Settings" },
    ],
  },
  {
    title: "Actions",
    shortcuts: [
      { keys: ["n", "d"], label: "Nouveau document (upload)" },
      { keys: ["n", "c"], label: "Nouvelle collection" },
    ],
  },
  {
    title: "General",
    shortcuts: [
      { keys: ["⌘", "K"], label: "Ouvrir la palette de commandes" },
      { keys: ["/"], label: "Rechercher (ouvrir palette)" },
      { keys: ["?"], label: "Afficher les raccourcis clavier" },
      { keys: ["Esc"], label: "Fermer le modal actif" },
    ],
  },
];

const SEQUENCE_TIMEOUT = 500;

export function KeyboardShortcuts() {
  const router = useRouter();
  const [helpOpen, setHelpOpen] = useState(false);
  const sequenceRef = useRef<{ key: string; time: number } | null>(null);

  // Listen for custom event from sidebar button
  useEffect(() => {
    const handler = () => setHelpOpen(true);
    window.addEventListener("open-shortcuts-help", handler);
    return () => window.removeEventListener("open-shortcuts-help", handler);
  }, []);

  const isInputFocused = useCallback((): boolean => {
    const tag = document.activeElement?.tagName?.toLowerCase();
    if (tag === "input" || tag === "textarea" || tag === "select") return true;
    if ((document.activeElement as HTMLElement)?.isContentEditable) return true;
    return false;
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Escape always works — close help modal
      if (e.key === "Escape") {
        if (helpOpen) {
          setHelpOpen(false);
          e.preventDefault();
        }
        return;
      }

      // Don't process shortcuts when typing in form fields
      if (isInputFocused()) return;

      // Don't process if a modifier key is held (except shift for ?)
      if (e.ctrlKey || e.metaKey || e.altKey) return;

      // ? (Shift + /) — open help
      if (e.key === "?") {
        e.preventDefault();
        setHelpOpen((prev) => !prev);
        return;
      }

      // If help modal is open, don't process navigation shortcuts
      if (helpOpen) return;

      // / — focus search (trigger Cmd+K)
      if (e.key === "/") {
        e.preventDefault();
        window.dispatchEvent(
          new KeyboardEvent("keydown", {
            key: "k",
            code: "KeyK",
            metaKey: true,
            ctrlKey: navigator.platform.includes("Win") || navigator.platform.includes("Linux"),
            bubbles: true,
          })
        );
        return;
      }

      const now = Date.now();
      const pending = sequenceRef.current;

      // Check for second key in a sequence
      if (pending && now - pending.time < SEQUENCE_TIMEOUT) {
        const combo = `${pending.key}${e.key}`;
        sequenceRef.current = null;

        switch (combo) {
          case "gh":
            e.preventDefault();
            router.push("/overview");
            return;
          case "gd":
            e.preventDefault();
            router.push("/documents");
            return;
          case "gc":
            e.preventDefault();
            router.push("/collections");
            return;
          case "gp":
            e.preventDefault();
            router.push("/playground");
            return;
          case "ga":
            e.preventDefault();
            router.push("/analytics");
            return;
          case "gs":
            e.preventDefault();
            router.push("/settings");
            return;
          case "nd":
            e.preventDefault();
            router.push("/sources");
            return;
          case "nc":
            e.preventDefault();
            router.push("/collections?new=true");
            return;
          default:
            break;
        }
      }

      // Record first key of potential sequence
      if (e.key === "g" || e.key === "n") {
        sequenceRef.current = { key: e.key, time: now };
        return;
      }

      // Not a recognized key — clear sequence
      sequenceRef.current = null;
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [helpOpen, isInputFocused, router]);

  if (!helpOpen) return null;

  return (
    <div className="fixed inset-0 z-[110] flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm animate-fade-in"
        onClick={() => setHelpOpen(false)}
      />

      {/* Modal */}
      <div className="relative w-full max-w-lg mx-4 bg-surface-0 rounded-2xl shadow-2xl border border-border overflow-hidden animate-slide-in">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-brand-50 dark:bg-brand-950">
              <Keyboard size={18} className="text-brand-600" />
            </div>
            <h2 className="text-lg font-semibold text-text-primary">
              Raccourcis Clavier
            </h2>
          </div>
          <button
            onClick={() => setHelpOpen(false)}
            className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-2 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-4 max-h-[60vh] overflow-y-auto scrollbar-thin space-y-6">
          {shortcutSections.map((section) => (
            <div key={section.title}>
              <h3 className="text-[11px] font-semibold text-text-muted uppercase tracking-wider mb-3">
                {section.title}
              </h3>
              <div className="space-y-2">
                {section.shortcuts.map((shortcut, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between py-1.5"
                  >
                    <span className="text-sm text-text-secondary">
                      {shortcut.label}
                    </span>
                    <div className="flex items-center gap-1.5 shrink-0 ml-4">
                      {shortcut.keys.map((key, kidx) => (
                        <React.Fragment key={kidx}>
                          {kidx > 0 && shortcut.keys.length === 2 && key !== "K" && (
                            <ArrowRight
                              size={10}
                              className="text-text-muted mx-0.5"
                            />
                          )}
                          <kbd className="inline-flex items-center justify-center min-w-[24px] h-6 px-1.5 rounded-md bg-surface-2 border border-border text-[11px] font-mono font-medium text-text-primary shadow-sm">
                            {key === "⌘" ? (
                              <Command size={11} />
                            ) : (
                              key
                            )}
                          </kbd>
                        </React.Fragment>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-center px-6 py-3 border-t border-border bg-surface-1">
          <span className="text-[11px] text-text-muted">
            Appuyez sur <kbd className="px-1 py-0.5 rounded bg-surface-2 text-[10px] font-mono mx-0.5">Esc</kbd> ou <kbd className="px-1 py-0.5 rounded bg-surface-2 text-[10px] font-mono mx-0.5">?</kbd> pour fermer
          </span>
        </div>
      </div>
    </div>
  );
}
