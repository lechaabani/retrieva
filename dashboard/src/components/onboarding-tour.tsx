"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  ArrowLeft,
  X,
  CheckCircle2,
  FileText,
  MessageSquare,
  Globe,
  Puzzle,
  BarChart3,
  Upload,
  Sparkles,
} from "lucide-react";

interface TourStep {
  title: string;
  description: string;
  icon: React.ReactNode;
  highlight?: string;
  action?: string;
}

const TOUR_STEPS: TourStep[] = [
  {
    title: "Bienvenue sur Retrieva !",
    description:
      "Decouvrons ensemble votre nouvelle plateforme RAG. Ce tour rapide vous montrera les fonctionnalites cles en 2 minutes.",
    icon: <Sparkles size={32} className="text-yellow-400" />,
  },
  {
    title: "Ingerez vos documents",
    description:
      "Uploadez des PDF, DOCX, HTML, CSV ou connectez vos sources (Notion, Google Drive, API). Les documents sont automatiquement decoupes et indexes.",
    icon: <Upload size={32} className="text-indigo-400" />,
    action: "/documents",
  },
  {
    title: "Organisez en collections",
    description:
      "Regroupez vos documents par theme, projet ou departement. Chaque collection a ses propres parametres de recherche.",
    icon: <FileText size={32} className="text-emerald-400" />,
    action: "/collections",
  },
  {
    title: "Testez dans le Playground",
    description:
      "Posez des questions a vos documents en temps reel. Ajustez le top-k, la strategie de recherche, et voyez les sources citees.",
    icon: <MessageSquare size={32} className="text-purple-400" />,
    action: "/playground",
  },
  {
    title: "Integrez avec les Widgets",
    description:
      "Deployez un chatbot ou une barre de recherche sur votre site en un seul script. Personnalisez les couleurs et le comportement.",
    icon: <Globe size={32} className="text-sky-400" />,
    action: "/widgets",
  },
  {
    title: "Etendez avec les Plugins",
    description:
      "Ajoutez des embedders, generators, chunkers depuis le marketplace. Creez vos propres plugins pour des besoins specifiques.",
    icon: <Puzzle size={32} className="text-amber-400" />,
    action: "/plugins",
  },
  {
    title: "Suivez les performances",
    description:
      "Analytics en temps reel : latence, confiance, tokens. Evaluez la qualite de vos reponses avec des suites de tests automatisees.",
    icon: <BarChart3 size={32} className="text-pink-400" />,
    action: "/analytics",
  },
  {
    title: "Vous etes pret !",
    description:
      "Commencez par uploader vos premiers documents, puis testez dans le Playground. Utilisez \u2318K a tout moment pour naviguer rapidement.",
    icon: <CheckCircle2 size={32} className="text-green-400" />,
  },
];

export function OnboardingTour() {
  const router = useRouter();
  const [visible, setVisible] = useState(false);
  const [step, setStep] = useState(0);
  const [exiting, setExiting] = useState(false);

  useEffect(() => {
    const seen = localStorage.getItem("retrieva_tour_completed");
    if (!seen) {
      const timer = setTimeout(() => setVisible(true), 1500);
      return () => clearTimeout(timer);
    }
  }, []);

  const handleClose = useCallback(() => {
    setExiting(true);
    setTimeout(() => {
      setVisible(false);
      setExiting(false);
      localStorage.setItem("retrieva_tour_completed", "true");
    }, 300);
  }, []);

  const handleNext = useCallback(() => {
    if (step < TOUR_STEPS.length - 1) {
      setStep((s) => s + 1);
    } else {
      handleClose();
    }
  }, [step, handleClose]);

  const handlePrev = useCallback(() => {
    if (step > 0) setStep((s) => s - 1);
  }, [step]);

  const handleGoTo = useCallback(
    (action?: string) => {
      if (action) {
        router.push(action);
      }
      handleNext();
    },
    [router, handleNext]
  );

  if (!visible) return null;

  const currentStep = TOUR_STEPS[step];
  const isFirst = step === 0;
  const isLast = step === TOUR_STEPS.length - 1;
  const progress = ((step + 1) / TOUR_STEPS.length) * 100;

  return (
    <div className="fixed inset-0 z-[150] flex items-center justify-center">
      {/* Backdrop */}
      <div
        className={`absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity duration-300 ${
          exiting ? "opacity-0" : "opacity-100"
        }`}
        onClick={handleClose}
      />

      {/* Tour Card */}
      <div
        className={`relative w-full max-w-lg mx-4 bg-surface-0 rounded-2xl shadow-2xl border border-border overflow-hidden transition-all duration-300 ${
          exiting ? "opacity-0 scale-95" : "opacity-100 scale-100"
        }`}
      >
        {/* Progress bar */}
        <div className="h-1 bg-surface-2">
          <div
            className="h-full bg-gradient-to-r from-brand-600 to-purple-600 transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Close button */}
        <button
          onClick={handleClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-2 transition-colors z-10"
        >
          <X size={18} />
        </button>

        {/* Content */}
        <div className="p-8 text-center">
          {/* Icon */}
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-50 to-purple-50 dark:from-brand-950 dark:to-purple-950 flex items-center justify-center mx-auto mb-6 shadow-sm">
            {currentStep.icon}
          </div>

          {/* Step indicator */}
          <div className="flex items-center justify-center gap-1.5 mb-4">
            {TOUR_STEPS.map((_, i) => (
              <button
                key={i}
                onClick={() => setStep(i)}
                className={`h-1.5 rounded-full transition-all duration-300 ${
                  i === step
                    ? "w-6 bg-brand-600"
                    : i < step
                    ? "w-1.5 bg-brand-300 dark:bg-brand-700"
                    : "w-1.5 bg-surface-3"
                }`}
              />
            ))}
          </div>

          <h2 className="text-xl font-bold text-text-primary mb-3">
            {currentStep.title}
          </h2>
          <p className="text-sm text-text-secondary leading-relaxed max-w-md mx-auto">
            {currentStep.description}
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between px-8 pb-6">
          <div>
            {!isFirst && (
              <button
                onClick={handlePrev}
                className="flex items-center gap-1.5 text-sm text-text-muted hover:text-text-primary transition-colors"
              >
                <ArrowLeft size={14} />
                Precedent
              </button>
            )}
          </div>
          <div className="flex items-center gap-3">
            {!isLast && (
              <button
                onClick={handleClose}
                className="text-sm text-text-muted hover:text-text-primary transition-colors"
              >
                Passer le tour
              </button>
            )}
            <button
              onClick={() => handleGoTo(currentStep.action)}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-brand-600 to-purple-600 hover:from-brand-500 hover:to-purple-500 text-white text-sm font-semibold transition-all shadow-lg shadow-brand-500/25"
            >
              {isLast
                ? "Commencer"
                : currentStep.action
                ? "Voir et continuer"
                : "Suivant"}
              <ArrowRight size={14} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
