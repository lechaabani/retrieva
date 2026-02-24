"use client";

import React, { useEffect, useState } from "react";
import {
  CreditCard,
  BarChart3,
  FileText,
  Database,
  Globe,
  Crown,
  Check,
  X,
  ExternalLink,
  Loader2,
  AlertTriangle,
} from "lucide-react";
import {
  getPlans,
  getSubscription,
  createCheckout,
  createBillingPortal,
  type PlanInfo,
  type SubscriptionData,
} from "@/lib/api";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDate(iso: string | null): string {
  if (!iso) return "-";
  return new Date(iso).toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

function planBadgeClasses(plan: string): string {
  switch (plan) {
    case "pro":
      return "bg-brand-100 text-brand-700 dark:bg-brand-950 dark:text-brand-300";
    case "enterprise":
      return "bg-violet-100 text-violet-700 dark:bg-violet-950 dark:text-violet-300";
    default:
      return "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300";
  }
}

function statusColor(status: string): string {
  switch (status) {
    case "active":
      return "text-green-600 dark:text-green-400";
    case "trialing":
      return "text-blue-600 dark:text-blue-400";
    case "past_due":
      return "text-red-600 dark:text-red-400";
    case "canceled":
      return "text-gray-500";
    default:
      return "text-gray-500";
  }
}

function statusLabel(status: string): string {
  switch (status) {
    case "active":
      return "Actif";
    case "trialing":
      return "Essai";
    case "past_due":
      return "Paiement en retard";
    case "canceled":
      return "Annule";
    default:
      return status;
  }
}

function barColor(pct: number): string {
  if (pct >= 95) return "bg-red-500";
  if (pct >= 80) return "bg-amber-500";
  return "bg-brand-600";
}

function formatLimit(limit: number): string {
  if (limit === -1) return "Illimite";
  return limit.toLocaleString("fr-FR");
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function UsageBar({
  label,
  used,
  limit,
  percentage,
  icon,
}: {
  label: string;
  used: number;
  limit: number;
  percentage: number;
  icon: React.ReactNode;
}) {
  const isUnlimited = limit === -1;
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2 text-text-secondary">
          {icon}
          <span>{label}</span>
        </div>
        <span className="font-medium text-text-primary">
          {used.toLocaleString("fr-FR")} / {isUnlimited ? "Illimite" : limit.toLocaleString("fr-FR")}
        </span>
      </div>
      <div className="h-2 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            isUnlimited ? "bg-brand-600 w-0" : barColor(percentage)
          }`}
          style={{ width: isUnlimited ? "0%" : `${Math.min(percentage, 100)}%` }}
        />
      </div>
      {!isUnlimited && percentage >= 80 && (
        <p className="text-xs text-amber-600 dark:text-amber-400 flex items-center gap-1">
          <AlertTriangle size={12} />
          {percentage >= 95 ? "Limite presque atteinte" : "Utilisation elevee"}
        </p>
      )}
    </div>
  );
}

function PlanCard({
  plan,
  isCurrent,
  onSelect,
  loading,
}: {
  plan: PlanInfo;
  isCurrent: boolean;
  onSelect: () => void;
  loading: boolean;
}) {
  const isPro = plan.name === "pro";
  const isEnterprise = plan.name === "enterprise";

  return (
    <div
      className={`relative rounded-xl border p-6 flex flex-col ${
        isCurrent
          ? "border-brand-500 ring-2 ring-brand-200 dark:ring-brand-900"
          : "border-border"
      } bg-surface-0`}
    >
      {isCurrent && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-brand-600 px-3 py-0.5 text-xs font-semibold text-white">
          Plan actuel
        </div>
      )}
      {isPro && !isCurrent && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-amber-500 px-3 py-0.5 text-xs font-semibold text-white flex items-center gap-1">
          <Crown size={12} /> Populaire
        </div>
      )}

      <div className="mb-4">
        <h3 className="text-lg font-bold text-text-primary">{plan.display_name}</h3>
        <div className="mt-2">
          {plan.price === 0 ? (
            <span className="text-3xl font-bold text-text-primary">Gratuit</span>
          ) : plan.price === -1 ? (
            <span className="text-3xl font-bold text-text-primary">Sur mesure</span>
          ) : (
            <div className="flex items-baseline gap-1">
              <span className="text-3xl font-bold text-text-primary">
                {plan.price}&euro;
              </span>
              <span className="text-text-muted text-sm">/ mois</span>
            </div>
          )}
        </div>
      </div>

      <ul className="flex-1 space-y-2 mb-6">
        {plan.features.map((feature) => (
          <li key={feature} className="flex items-start gap-2 text-sm text-text-secondary">
            <Check size={16} className="text-green-500 mt-0.5 shrink-0" />
            <span>{feature}</span>
          </li>
        ))}
      </ul>

      {isCurrent ? (
        <button
          disabled
          className="w-full rounded-lg border border-border bg-surface-2 px-4 py-2.5 text-sm font-medium text-text-muted cursor-not-allowed"
        >
          Plan actuel
        </button>
      ) : isEnterprise ? (
        <a
          href="mailto:contact@retrieva.io?subject=Retrieva%20Enterprise"
          className="w-full rounded-lg bg-violet-600 hover:bg-violet-700 px-4 py-2.5 text-sm font-medium text-white text-center transition-colors inline-block"
        >
          Nous contacter
        </a>
      ) : (
        <button
          onClick={onSelect}
          disabled={loading}
          className="w-full rounded-lg bg-brand-600 hover:bg-brand-700 px-4 py-2.5 text-sm font-medium text-white transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              Redirection...
            </>
          ) : (
            `Passer au ${plan.display_name}`
          )}
        </button>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page component
// ---------------------------------------------------------------------------

export default function BillingPage() {
  const [plans, setPlans] = useState<PlanInfo[]>([]);
  const [subscription, setSubscription] = useState<SubscriptionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null);
  const [portalLoading, setPortalLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      setLoading(true);
      setError(null);
      const [plansData, subData] = await Promise.all([
        getPlans(),
        getSubscription(),
      ]);
      setPlans(plansData);
      setSubscription(subData);
    } catch (err: any) {
      setError(err.message || "Erreur lors du chargement des donnees de facturation.");
    } finally {
      setLoading(false);
    }
  }

  async function handleCheckout(plan: string) {
    try {
      setCheckoutLoading(plan);
      const { checkout_url } = await createCheckout(plan);
      window.location.href = checkout_url;
    } catch (err: any) {
      setError(err.message || "Erreur lors de la creation de la session de paiement.");
      setCheckoutLoading(null);
    }
  }

  async function handlePortal() {
    try {
      setPortalLoading(true);
      const { portal_url } = await createBillingPortal();
      window.location.href = portal_url;
    } catch (err: any) {
      setError(err.message || "Erreur lors de l'ouverture du portail de facturation.");
      setPortalLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 size={32} className="animate-spin text-brand-600" />
      </div>
    );
  }

  if (error && !subscription) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="rounded-lg border border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950 p-4 text-red-700 dark:text-red-300">
          {error}
        </div>
      </div>
    );
  }

  const sub = subscription!;
  const currentPlan = sub.plan;
  const isPaid = currentPlan !== "community";

  return (
    <div className="max-w-5xl mx-auto space-y-8 p-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Facturation</h1>
        <p className="text-text-muted mt-1">
          Gerez votre abonnement et suivez votre consommation.
        </p>
      </div>

      {error && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950 p-3 text-amber-700 dark:text-amber-300 text-sm">
          {error}
        </div>
      )}

      {/* Current Plan Card */}
      <div className="rounded-xl border border-border bg-surface-0 p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <CreditCard size={20} className="text-text-muted" />
              <h2 className="text-lg font-semibold text-text-primary">
                Abonnement actuel
              </h2>
            </div>
            <div className="flex items-center gap-3 pl-8">
              <span
                className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-semibold ${planBadgeClasses(
                  currentPlan
                )}`}
              >
                {currentPlan === "enterprise" && <Crown size={14} />}
                {plans.find((p) => p.name === currentPlan)?.display_name || currentPlan}
              </span>
              <span className={`text-sm font-medium ${statusColor(sub.status)}`}>
                {statusLabel(sub.status)}
              </span>
            </div>
            {sub.current_period_end && (
              <p className="text-sm text-text-muted pl-8">
                {sub.cancel_at_period_end
                  ? `Se termine le ${formatDate(sub.current_period_end)}`
                  : `Prochain renouvellement : ${formatDate(sub.current_period_end)}`}
              </p>
            )}
          </div>
          <div className="flex gap-3 pl-8 sm:pl-0">
            {isPaid ? (
              <button
                onClick={handlePortal}
                disabled={portalLoading}
                className="inline-flex items-center gap-2 rounded-lg border border-border bg-surface-0 px-4 py-2 text-sm font-medium text-text-primary hover:bg-surface-2 transition-colors disabled:opacity-50"
              >
                {portalLoading ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  <ExternalLink size={16} />
                )}
                Gerer l&apos;abonnement
              </button>
            ) : (
              <button
                onClick={() => handleCheckout("pro")}
                disabled={checkoutLoading !== null}
                className="inline-flex items-center gap-2 rounded-lg bg-brand-600 hover:bg-brand-700 px-4 py-2 text-sm font-medium text-white transition-colors disabled:opacity-50"
              >
                {checkoutLoading === "pro" ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  <Crown size={16} />
                )}
                Passer au Pro
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Usage Section */}
      <div className="rounded-xl border border-border bg-surface-0 p-6">
        <div className="flex items-center gap-2 mb-6">
          <BarChart3 size={20} className="text-text-muted" />
          <h2 className="text-lg font-semibold text-text-primary">Consommation</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <UsageBar
            label={sub.usage.documents.label}
            used={sub.usage.documents.used}
            limit={sub.usage.documents.limit}
            percentage={sub.usage.documents.percentage}
            icon={<FileText size={16} />}
          />
          <UsageBar
            label={sub.usage.queries.label}
            used={sub.usage.queries.used}
            limit={sub.usage.queries.limit}
            percentage={sub.usage.queries.percentage}
            icon={<Database size={16} />}
          />
          <UsageBar
            label={sub.usage.collections.label}
            used={sub.usage.collections.used}
            limit={sub.usage.collections.limit}
            percentage={sub.usage.collections.percentage}
            icon={<Database size={16} />}
          />
          <UsageBar
            label={sub.usage.widgets.label}
            used={sub.usage.widgets.used}
            limit={sub.usage.widgets.limit}
            percentage={sub.usage.widgets.percentage}
            icon={<Globe size={16} />}
          />
        </div>
      </div>

      {/* Plan Comparison */}
      <div>
        <h2 className="text-lg font-semibold text-text-primary mb-4">
          Comparer les plans
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {plans.map((plan) => (
            <PlanCard
              key={plan.name}
              plan={plan}
              isCurrent={plan.name === currentPlan}
              onSelect={() => handleCheckout(plan.name)}
              loading={checkoutLoading === plan.name}
            />
          ))}
        </div>
      </div>

      {/* Plan Feature Comparison Table */}
      <div className="rounded-xl border border-border bg-surface-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-surface-1">
              <th className="text-left px-6 py-3 font-medium text-text-secondary">
                Fonctionnalite
              </th>
              {plans.map((plan) => (
                <th
                  key={plan.name}
                  className={`text-center px-4 py-3 font-medium ${
                    plan.name === currentPlan
                      ? "text-brand-600 dark:text-brand-400"
                      : "text-text-secondary"
                  }`}
                >
                  {plan.display_name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {[
              {
                label: "Documents",
                values: ["100", "10 000", "Illimite"],
              },
              {
                label: "Requetes / mois",
                values: ["1 000", "50 000", "Illimite"],
              },
              {
                label: "Collections",
                values: ["3", "50", "Illimite"],
              },
              {
                label: "Widgets",
                values: ["0", "10", "Illimite"],
              },
              {
                label: "API REST",
                values: [true, true, true],
              },
              {
                label: "Connecteurs avances",
                values: [false, true, true],
              },
              {
                label: "Analytics avances",
                values: [false, true, true],
              },
              {
                label: "Support prioritaire",
                values: [false, true, true],
              },
              {
                label: "SSO / SAML",
                values: [false, false, true],
              },
              {
                label: "SLA garanti",
                values: [false, false, true],
              },
              {
                label: "Deploiement on-premise",
                values: [false, false, true],
              },
            ].map((row, idx) => (
              <tr
                key={row.label}
                className={idx % 2 === 0 ? "" : "bg-surface-1/50"}
              >
                <td className="px-6 py-3 text-text-primary font-medium">
                  {row.label}
                </td>
                {row.values.map((val, i) => (
                  <td key={i} className="text-center px-4 py-3">
                    {typeof val === "boolean" ? (
                      val ? (
                        <Check
                          size={16}
                          className="inline text-green-500"
                        />
                      ) : (
                        <X size={16} className="inline text-gray-300 dark:text-gray-600" />
                      )
                    ) : (
                      <span className="text-text-secondary">{val}</span>
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Billing History Placeholder */}
      <div className="rounded-xl border border-border bg-surface-0 p-6">
        <div className="flex items-center gap-2 mb-4">
          <CreditCard size={20} className="text-text-muted" />
          <h2 className="text-lg font-semibold text-text-primary">
            Historique de facturation
          </h2>
        </div>
        <p className="text-sm text-text-muted mb-4">
          L&apos;historique de facturation est disponible dans le portail Stripe.
        </p>
        {isPaid && (
          <button
            onClick={handlePortal}
            disabled={portalLoading}
            className="inline-flex items-center gap-2 rounded-lg border border-border bg-surface-0 px-4 py-2 text-sm font-medium text-text-primary hover:bg-surface-2 transition-colors disabled:opacity-50"
          >
            {portalLoading ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <ExternalLink size={16} />
            )}
            Ouvrir le portail
          </button>
        )}
      </div>
    </div>
  );
}
