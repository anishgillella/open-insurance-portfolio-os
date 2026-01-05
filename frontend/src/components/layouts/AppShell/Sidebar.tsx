'use client';

import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Building2,
  AlertTriangle,
  RefreshCw,
  MessageSquare,
  ChevronLeft,
  ChevronRight,
  Shield,
} from 'lucide-react';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Properties', href: '/properties', icon: Building2 },
  { name: 'Gaps', href: '/gaps', icon: AlertTriangle },
  { name: 'Compliance', href: '/compliance', icon: Shield },
  { name: 'Renewals', href: '/renewals', icon: RefreshCw },
  { name: 'Chat', href: '/chat', icon: MessageSquare },
];

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const pathname = usePathname();

  return (
    <motion.aside
      className={cn(
        'fixed left-0 top-0 bottom-0 z-40',
        'bg-[var(--color-surface)] border-r border-[var(--color-border-subtle)]',
        'flex flex-col'
      )}
      initial={false}
      animate={{
        width: collapsed ? 72 : 280,
      }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
    >
      {/* Logo */}
      <div className="h-[72px] flex items-center px-4 border-b border-[var(--color-border-subtle)]">
        <Link href="/" className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl gradient-primary flex items-center justify-center">
            <Shield className="h-5 w-5 text-white" />
          </div>
          {!collapsed && (
            <motion.span
              className="font-semibold text-lg text-[var(--color-text-primary)]"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              Open Insurance
            </motion.span>
          )}
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        {navigation.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all',
                'hover:bg-[var(--color-surface-sunken)]',
                isActive && 'bg-[var(--color-primary-50)] text-[var(--color-primary-600)]',
                !isActive && 'text-[var(--color-text-secondary)]'
              )}
            >
              <Icon className={cn('h-5 w-5 flex-shrink-0', isActive && 'text-[var(--color-primary-500)]')} />
              {!collapsed && (
                <>
                  <span className="font-medium flex-1">{item.name}</span>
                  {item.badge && (
                    <span className="bg-[var(--color-critical-500)] text-white text-xs font-medium px-2 py-0.5 rounded-full">
                      {item.badge}
                    </span>
                  )}
                </>
              )}
              {collapsed && item.badge && (
                <span className="absolute right-2 top-1 w-2 h-2 bg-[var(--color-critical-500)] rounded-full" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Toggle button */}
      <div className="p-3 border-t border-[var(--color-border-subtle)]">
        <button
          onClick={onToggle}
          className={cn(
            'w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg',
            'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]',
            'hover:bg-[var(--color-surface-sunken)] transition-colors'
          )}
        >
          {collapsed ? (
            <ChevronRight className="h-5 w-5" />
          ) : (
            <>
              <ChevronLeft className="h-5 w-5" />
              <span className="text-sm">Collapse</span>
            </>
          )}
        </button>
      </div>
    </motion.aside>
  );
}
