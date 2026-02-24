"use client";

import React from "react";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";
import { ToastProvider } from "@/components/ui/toast";
import { FeatureFlagsProvider } from "@/lib/feature-flags";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <title>Retrieva - Le WordPress du RAG</title>
        <meta
          name="description"
          content="Retrieva - Plateforme RAG modulaire et extensible."
        />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className="antialiased">
        <AuthProvider>
          <FeatureFlagsProvider>
            <ToastProvider>{children}</ToastProvider>
          </FeatureFlagsProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
