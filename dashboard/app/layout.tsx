import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Clippin • AI Video Repurposing & Virality Studio',
  description: 'Automated 9:16 vertical clip curation, speaker tracking, and virality scoring for TikTok, YouTube Shorts, and Reels.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
