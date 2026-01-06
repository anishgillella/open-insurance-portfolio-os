'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { Logo } from '@/components/shared/Logo';

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-[var(--color-background)] flex flex-col">
      {/* Header with Logo */}
      <header className="w-full py-6 px-8">
        <Link href="/">
          <Logo size="md" />
        </Link>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
          className="w-full max-w-md"
        >
          {children}
        </motion.div>
      </main>

      {/* Footer */}
      <footer className="w-full py-6 text-center">
        <p className="text-sm text-[var(--color-text-muted)]">
          © {new Date().getFullYear()} Open Insurance.
        </p>
      </footer>
    </div>
  );
}
