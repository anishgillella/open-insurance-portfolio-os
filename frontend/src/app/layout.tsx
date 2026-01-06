import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from '@/components/Providers';
import { AuthProvider } from '@/lib/auth-context';
import { ConditionalAppShell } from '@/components/layouts/ConditionalAppShell';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: 'Open Insurance',
  description: 'AI-powered insurance portfolio management for commercial real estate',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} font-sans antialiased`}>
        <Providers>
          <AuthProvider>
            <ConditionalAppShell>{children}</ConditionalAppShell>
          </AuthProvider>
        </Providers>
      </body>
    </html>
  );
}
