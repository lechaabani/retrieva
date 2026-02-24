import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Retrieva — Le WordPress du RAG | Plateforme Open Source",
  description:
    "La plateforme open source pour construire, deployer et scaler vos applications RAG. En production en 5 minutes. Self-hosted ou Cloud.",
  keywords: [
    "RAG",
    "Retrieval Augmented Generation",
    "open source",
    "AI",
    "LLM",
    "vector search",
    "embeddings",
    "chatbot",
    "knowledge base",
  ],
  openGraph: {
    title: "Retrieva — Le WordPress du RAG",
    description:
      "La plateforme open source pour construire, deployer et scaler vos applications RAG. En production en 5 minutes.",
    url: "https://retrieva.ai",
    siteName: "Retrieva",
    type: "website",
    locale: "fr_FR",
  },
  twitter: {
    card: "summary_large_image",
    title: "Retrieva — Le WordPress du RAG",
    description:
      "La plateforme open source pour construire, deployer et scaler vos applications RAG.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr" className="dark scroll-smooth">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap"
          rel="stylesheet"
        />
      </head>
      <body
        className="bg-[#0A0A0F] text-white antialiased"
        style={{ fontFamily: "'Inter', system-ui, -apple-system, sans-serif" }}
      >
        {children}
      </body>
    </html>
  );
}
