"use client";

import React from "react";
import Link from "next/link";
import { Lock, Crown, Shield } from "lucide-react";
import { cn } from "@/lib/utils";
import type { PlanTier } from "@/lib/feature-flags";

interface UpgradeBannerProps {
  requiredTier: Exclude<PlanTier, "community">;
  featureLabel: string;
  featureDescription?: string;
  className?: string;
}

export function UpgradeBanner({
  requiredTier,
  featureLabel,
  featureDescription,
  className,
}: UpgradeBannerProps) {
  const isEnterprise = requiredTier === "enterprise";
  const tierLabel = isEnterprise ? "Enterprise" : "Pro";
  const ctaLabel = isEnterprise
    ? "Passer au plan Enterprise"
    : "Passer au plan Pro";
  const ctaHref = isEnterprise
    ? "https://retrieva.ai/pricing"
    : "/upgrade";

  return (
    <div
      className={cn(
        "animate-fade-in flex items-center justify-center min-h-[60vh]",
        className
      )}
    >
      <div className="relative w-full max-w-lg rounded-2xl p-[2px] bg-gradient-to-br from-brand-600 to-violet-600">
        <div className="rounded-2xl bg-surface-0 p-8 text-center space-y-6">
          {/* Icon */}
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-brand-100 to-violet-100 dark:from-brand-950 dark:to-violet-950">
            <Lock className="h-6 w-6 text-brand-600 dark:text-brand-400" />
          </div>

          {/* Title */}
          <div className="space-y-2">
            <div className="inline-flex items-center gap-1.5 rounded-full bg-gradient-to-r from-brand-50 to-violet-50 dark:from-brand-950 dark:to-violet-950 px-3 py-1 text-xs font-semibold text-brand-700 dark:text-brand-300">
              {isEnterprise ? (
                <Shield className="h-3 w-3" />
              ) : (
                <Crown className="h-3 w-3" />
              )}
              Fonctionnalite {tierLabel}
            </div>
            <h2 className="text-xl font-bold text-text-primary">
              {featureLabel}
            </h2>
            {featureDescription && (
              <p className="text-sm text-text-secondary max-w-sm mx-auto">
                {featureDescription}
              </p>
            )}
          </div>

          {/* CTA */}
          <div className="space-y-3">
            <Link
              href={ctaHref}
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-brand-600 to-violet-600 px-6 py-2.5 text-sm font-semibold text-white shadow-lg hover:shadow-xl transition-all duration-200 hover:scale-[1.02]"
            >
              {isEnterprise ? (
                <Shield className="h-4 w-4" />
              ) : (
                <Crown className="h-4 w-4" />
              )}
              {ctaLabel}
            </Link>
            <p className="text-xs text-text-muted">
              Ou{" "}
              <a
                href="https://github.com/retrieva-ai/retrieva"
                target="_blank"
                rel="noopener noreferrer"
                className="underline hover:text-text-secondary transition-colors"
              >
                auto-hebergez avec toutes les fonctionnalites
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
