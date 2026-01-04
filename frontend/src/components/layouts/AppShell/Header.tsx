'use client';

import { cn } from '@/lib/utils';
import { Search, Bell, User } from 'lucide-react';
import { Button } from '@/components/primitives';
import { ThemeToggle } from '@/components/shared';

interface HeaderProps {
  sidebarCollapsed: boolean;
}

export function Header({ sidebarCollapsed }: HeaderProps) {
  return (
    <header
      className={cn(
        'fixed top-0 right-0 z-30 h-[72px]',
        'bg-[var(--color-surface)]/80 backdrop-blur-xl',
        'border-b border-[var(--color-border-subtle)]',
        'flex items-center justify-between px-6',
        'transition-all duration-300'
      )}
      style={{
        left: sidebarCollapsed ? '72px' : '280px',
      }}
    >
      {/* Search */}
      <div className="flex-1 max-w-xl">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--color-text-muted)]" />
          <input
            type="text"
            placeholder="Search properties, policies, documents..."
            className={cn(
              'w-full pl-10 pr-4 py-2.5 rounded-xl',
              'bg-[var(--color-surface-sunken)]',
              'border border-transparent',
              'text-sm text-[var(--color-text-primary)]',
              'placeholder:text-[var(--color-text-muted)]',
              'focus:outline-none focus:border-[var(--color-primary-500)]',
              'focus:ring-4 focus:ring-[var(--color-primary-500)]/20',
              'transition-all'
            )}
          />
          <kbd className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-[var(--color-text-muted)] bg-[var(--color-surface)] px-1.5 py-0.5 rounded border border-[var(--color-border-default)]">
            ⌘K
          </kbd>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1 ml-4">
        <ThemeToggle />
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-[var(--color-critical-500)] rounded-full" />
        </Button>
        <Button variant="ghost" size="icon">
          <User className="h-5 w-5" />
        </Button>
      </div>
    </header>
  );
}
