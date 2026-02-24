"use client";

import React, { createContext, useContext, useMemo } from "react";

export type PlanTier = "community" | "pro" | "enterprise";

export interface FeatureFlags {
  tier: PlanTier;
  // Community (free/open source)
  dashboard: boolean;
  playground: boolean;
  documents: boolean;
  collections: boolean;
  sources: boolean;
  plugins: boolean;
  apiKeys: boolean;
  developers: boolean;
  settings: boolean;
  // Pro
  analytics: boolean;
  evaluation: boolean;
  widgets: boolean;
  templates: boolean;
  pipelineDebugger: boolean;
  smartSuggestions: boolean;
  activityFeed: boolean;
  collectionCompare: boolean;
  // Enterprise
  users: boolean;
  health: boolean;
  logs: boolean;
  sso: boolean;
  customBranding: boolean;
}

export type FeatureName = keyof Omit<FeatureFlags, "tier">;

const communityFeatures: FeatureName[] = [
  "dashboard",
  "playground",
  "documents",
  "collections",
  "sources",
  "plugins",
  "apiKeys",
  "developers",
  "settings",
];

const proFeatures: FeatureName[] = [
  "analytics",
  "evaluation",
  "widgets",
  "templates",
  "pipelineDebugger",
  "smartSuggestions",
  "activityFeed",
  "collectionCompare",
];

const enterpriseFeatures: FeatureName[] = [
  "users",
  "health",
  "logs",
  "sso",
  "customBranding",
];

export function getFeatureFlags(tier: PlanTier): FeatureFlags {
  const flags: FeatureFlags = {
    tier,
    dashboard: false,
    playground: false,
    documents: false,
    collections: false,
    sources: false,
    plugins: false,
    apiKeys: false,
    developers: false,
    settings: false,
    analytics: false,
    evaluation: false,
    widgets: false,
    templates: false,
    pipelineDebugger: false,
    smartSuggestions: false,
    activityFeed: false,
    collectionCompare: false,
    users: false,
    health: false,
    logs: false,
    sso: false,
    customBranding: false,
  };

  // Community features are always enabled
  for (const f of communityFeatures) {
    flags[f] = true;
  }

  // Pro tier enables pro features
  if (tier === "pro" || tier === "enterprise") {
    for (const f of proFeatures) {
      flags[f] = true;
    }
  }

  // Enterprise tier enables enterprise features
  if (tier === "enterprise") {
    for (const f of enterpriseFeatures) {
      flags[f] = true;
    }
  }

  return flags;
}

/**
 * Returns the minimum tier required to access a given feature.
 */
export function getRequiredTier(feature: FeatureName): PlanTier {
  if (communityFeatures.includes(feature)) return "community";
  if (proFeatures.includes(feature)) return "pro";
  return "enterprise";
}

function resolveTier(): PlanTier {
  const env =
    typeof process !== "undefined"
      ? process.env.NEXT_PUBLIC_RETRIEVA_TIER
      : undefined;
  if (env === "pro" || env === "enterprise") return env;
  return "community";
}

const FeatureFlagsContext = createContext<FeatureFlags>(
  getFeatureFlags("community")
);

export function FeatureFlagsProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const flags = useMemo(() => getFeatureFlags(resolveTier()), []);

  return React.createElement(
    FeatureFlagsContext.Provider,
    { value: flags },
    children
  );
}

export function useFeatureFlags(): FeatureFlags {
  return useContext(FeatureFlagsContext);
}

export function isFeatureEnabled(
  flags: FeatureFlags,
  feature: FeatureName
): boolean {
  return flags[feature];
}
