'use client';

import { usePathname } from 'next/navigation';
import { AppShell } from './AppShell';
import { useAuth } from '@/lib/auth-context';
import { LogoIcon } from '@/components/shared/Logo';
import { Skeleton } from '@/components/primitives';

// Routes that should NOT have the AppShell (sidebar, header)
const noShellRoutes = ['/auth', '/onboarding'];

function isNoShellRoute(pathname: string): boolean {
  return noShellRoutes.some((route) => pathname.startsWith(route));
}

export function ConditionalAppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { isLoading, isAuthenticated } = useAuth();

  // Show loading state while checking auth
  if (isLoading) {
    return (
      <div className="min-h-screen bg-[var(--color-background)] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-pulse">
            <LogoIcon size={48} />
          </div>
          <Skeleton className="h-4 w-32" />
        </div>
      </div>
    );
  }

  // Auth and onboarding pages don't get the AppShell
  if (isNoShellRoute(pathname)) {
    return <>{children}</>;
  }

  // Protected routes get the AppShell (only if authenticated)
  if (isAuthenticated) {
    return <AppShell>{children}</AppShell>;
  }

  // Not authenticated and not on auth/onboarding route - show nothing while redirecting
  return null;
}
