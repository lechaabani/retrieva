"use client";

import React from "react";
import Link from "next/link";
import {
  Check,
  X,
  Crown,
  Shield,
  Zap,
  ArrowRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useFeatureFlags } from "@/lib/feature-flags";

interface PlanFeature {
  label: string;
  community: boolean;
  pro: boolean;
  enterprise: boolean;
}

const features: PlanFeature[] = [
  { label: "Dashboard & Overview", community: true, pro: true, enterprise: true },
  { label: "Playground (chat + search)", community: true, pro: true, enterprise: true },
  { label: "Documents & Collections", community: true, pro: true, enterprise: true },
  { label: "Sources & Connectors", community: true, pro: true, enterprise: true },
  { label: "Plugins", community: true, pro: true, enterprise: true },
  { label: "API Keys", community: true, pro: true, enterprise: true },
  { label: "SDK JS + Python", community: true, pro: true, enterprise: true },
  { label: "CLI", community: true, pro: true, enterprise: true },
  { label: "Self-hosted illimite", community: true, pro: true, enterprise: true },
  { label: "Analytics avances", community: false, pro: true, enterprise: true },
  { label: "Pipeline Debugger", community: false, pro: true, enterprise: true },
  { label: "Widgets embarquables", community: false, pro: true, enterprise: true },
  { label: "Templates", community: false, pro: true, enterprise: true },
  { label: "Evaluation RAG", community: false, pro: true, enterprise: true },
  { label: "Suggestions intelligentes", community: false, pro: true, enterprise: true },
  { label: "Comparaison de collections", community: false, pro: true, enterprise: true },
  { label: "Flux d'activite", community: false, pro: true, enterprise: true },
  { label: "Support prioritaire", community: false, pro: true, enterprise: true },
  { label: "Gestion des utilisateurs", community: false, pro: false, enterprise: true },
  { label: "SSO / SAML", community: false, pro: false, enterprise: true },
  { label: "Logs & Audit", community: false, pro: false, enterprise: true },
  { label: "Monitoring sante", community: false, pro: false, enterprise: true },
  { label: "Branding personnalise", community: false, pro: false, enterprise: true },
  { label: "SLA garanti", community: false, pro: false, enterprise: true },
  { label: "Support dedie", community: false, pro: false, enterprise: true },
];

function FeatureCheck({ enabled }: { enabled: boolean }) {
  return enabled ? (
    <Check className="h-4 w-4 text-green-600 dark:text-green-400" />
  ) : (
    <X className="h-4 w-4 text-text-muted/40" />
  );
}

interface PlanCardProps {
  name: string;
  price: string;
  priceSuffix?: string;
  description: string;
  icon: React.ReactNode;
  features: string[];
  highlighted?: boolean;
  badge?: string;
  ctaLabel: string;
  ctaHref: string;
  isCurrent?: boolean;
}

function PlanCard({
  name,
  price,
  priceSuffix,
  description,
  icon,
  features: planFeatures,
  highlighted,
  badge,
  ctaLabel,
  ctaHref,
  isCurrent,
}: PlanCardProps) {
  return (
    <div
      className={cn(
        "relative flex flex-col rounded-2xl border p-6 transition-all duration-200",
        highlighted
          ? "border-brand-600 dark:border-brand-500 shadow-xl shadow-brand-600/10 scale-[1.02]"
          : "border-border hover:border-brand-300 dark:hover:border-brand-700",
        "bg-surface-0"
      )}
    >
      {badge && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
          <span className="inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-brand-600 to-violet-600 px-3 py-1 text-xs font-semibold text-white">
            <Crown className="h-3 w-3" />
            {badge}
          </span>
        </div>
      )}

      <div className="mb-4 flex items-center gap-3">
        <div
          className={cn(
            "flex h-10 w-10 items-center justify-center rounded-xl",
            highlighted
              ? "bg-gradient-to-br from-brand-600 to-violet-600 text-white"
              : "bg-surface-2 text-text-secondary"
          )}
        >
          {icon}
        </div>
        <div>
          <h3 className="text-lg font-bold text-text-primary">{name}</h3>
          <p className="text-xs text-text-muted">{description}</p>
        </div>
      </div>

      <div className="mb-6">
        <span className="text-3xl font-extrabold text-text-primary">{price}</span>
        {priceSuffix && (
          <span className="text-sm text-text-muted ml-1">{priceSuffix}</span>
        )}
      </div>

      <ul className="mb-6 flex-1 space-y-2.5">
        {planFeatures.map((f) => (
          <li key={f} className="flex items-start gap-2 text-sm text-text-secondary">
            <Check className="mt-0.5 h-4 w-4 shrink-0 text-green-600 dark:text-green-400" />
            <span>{f}</span>
          </li>
        ))}
      </ul>

      {isCurrent ? (
        <div className="rounded-lg border border-border bg-surface-2 py-2.5 text-center text-sm font-semibold text-text-muted">
          Plan actuel
        </div>
      ) : (
        <Link
          href={ctaHref}
          className={cn(
            "flex items-center justify-center gap-2 rounded-lg py-2.5 text-sm font-semibold transition-all duration-200",
            highlighted
              ? "bg-gradient-to-r from-brand-600 to-violet-600 text-white shadow-lg hover:shadow-xl hover:scale-[1.01]"
              : "border border-border text-text-primary hover:bg-surface-2"
          )}
        >
          {ctaLabel}
          <ArrowRight className="h-4 w-4" />
        </Link>
      )}
    </div>
  );
}

export default function UpgradePage() {
  const flags = useFeatureFlags();
  const currentTier = flags.tier;

  return (
    <div className="animate-fade-in space-y-10">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-extrabold text-text-primary">
          Choisissez votre plan
        </h1>
        <p className="text-text-secondary max-w-xl mx-auto">
          Retrieva est open source et gratuit. Passez a un plan superieur pour
          debloquer des fonctionnalites avancees et un support prioritaire.
        </p>
      </div>

      {/* Plan cards */}
      <div className="grid gap-6 md:grid-cols-3 max-w-5xl mx-auto items-start">
        <PlanCard
          name="Community (Gratuit)"
          price="0 EUR"
          priceSuffix="/ pour toujours"
          description="Open source, auto-heberge"
          icon={<Zap className="h-5 w-5" />}
          isCurrent={currentTier === "community"}
          ctaLabel="Telecharger"
          ctaHref="https://github.com/lechaabani/retrieva"
          features={[
            "Dashboard & Overview",
            "Playground (chat + search)",
            "Documents & Collections",
            "Sources & Connectors",
            "Plugins",
            "API Keys",
            "SDK JS + Python",
            "CLI",
            "Self-hosted illimite",
          ]}
        />

        <PlanCard
          name="Pro"
          price="29 EUR"
          priceSuffix="/ mois"
          description="Pour les equipes qui grandissent"
          icon={<Crown className="h-5 w-5" />}
          highlighted
          badge="Populaire"
          isCurrent={currentTier === "pro"}
          ctaLabel="Passer au Pro"
          ctaHref="https://retrieva.ai/pricing"
          features={[
            "Tout Community +",
            "Analytics avances",
            "Pipeline Debugger",
            "Widgets embarquables",
            "Templates",
            "Evaluation RAG",
            "Suggestions intelligentes",
            "Comparaison de collections",
            "Flux d'activite",
            "Support prioritaire",
          ]}
        />

        <PlanCard
          name="Enterprise"
          price="Sur devis"
          description="Pour les grandes organisations"
          icon={<Shield className="h-5 w-5" />}
          isCurrent={currentTier === "enterprise"}
          ctaLabel="Contacter les ventes"
          ctaHref="https://retrieva.ai/pricing"
          features={[
            "Tout Pro +",
            "Gestion des utilisateurs",
            "SSO / SAML",
            "Logs & Audit",
            "Monitoring sante",
            "Branding personnalise",
            "SLA garanti",
            "Support dedie",
          ]}
        />
      </div>

      {/* Feature comparison table */}
      <div className="max-w-5xl mx-auto">
        <h2 className="text-xl font-bold text-text-primary mb-4 text-center">
          Comparaison detaillee
        </h2>
        <div className="rounded-xl border border-border overflow-hidden bg-surface-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-surface-1">
                  <th className="px-4 py-3 text-left font-semibold text-text-primary">
                    Fonctionnalite
                  </th>
                  <th className="px-4 py-3 text-center font-semibold text-text-primary w-28">
                    <div className="flex flex-col items-center gap-0.5">
                      <Zap className="h-4 w-4 text-text-muted" />
                      Community
                    </div>
                  </th>
                  <th className="px-4 py-3 text-center font-semibold text-brand-600 w-28">
                    <div className="flex flex-col items-center gap-0.5">
                      <Crown className="h-4 w-4" />
                      Pro
                    </div>
                  </th>
                  <th className="px-4 py-3 text-center font-semibold text-text-primary w-28">
                    <div className="flex flex-col items-center gap-0.5">
                      <Shield className="h-4 w-4 text-text-muted" />
                      Enterprise
                    </div>
                  </th>
                </tr>
              </thead>
              <tbody>
                {features.map((f, i) => (
                  <tr
                    key={f.label}
                    className={cn(
                      "border-b border-border last:border-0",
                      i % 2 === 0 ? "bg-surface-0" : "bg-surface-1/50"
                    )}
                  >
                    <td className="px-4 py-2.5 text-text-secondary">{f.label}</td>
                    <td className="px-4 py-2.5 text-center">
                      <span className="inline-flex justify-center">
                        <FeatureCheck enabled={f.community} />
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-center">
                      <span className="inline-flex justify-center">
                        <FeatureCheck enabled={f.pro} />
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-center">
                      <span className="inline-flex justify-center">
                        <FeatureCheck enabled={f.enterprise} />
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Bottom CTA */}
      <div className="text-center pb-8">
        <p className="text-sm text-text-muted">
          Des questions ?{" "}
          <a
            href="https://retrieva.ai/contact"
            target="_blank"
            rel="noopener noreferrer"
            className="text-brand-600 hover:underline font-medium"
          >
            Contactez-nous
          </a>
        </p>
      </div>
    </div>
  );
}
