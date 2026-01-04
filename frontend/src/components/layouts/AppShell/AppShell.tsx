'use client';

import { useState } from 'react';
import { cn } from '@/lib/utils';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="min-h-screen bg-[var(--color-background)]">
      {/* Sidebar */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      {/* Header */}
      <Header sidebarCollapsed={sidebarCollapsed} />

      {/* Main content */}
      <main
        className={cn(
          'pt-[72px] min-h-screen transition-all duration-300'
        )}
        style={{
          marginLeft: sidebarCollapsed ? '72px' : '280px',
        }}
      >
        <div className="p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
