'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { Sun, Moon, Monitor } from 'lucide-react';
import { useTheme } from '@/lib/theme';
import { cn } from '@/lib/utils';

interface ThemeToggleProps {
  className?: string;
  showLabel?: boolean;
}

export function ThemeToggle({ className, showLabel = false }: ThemeToggleProps) {
  const { theme, setTheme, resolvedTheme } = useTheme();

  const cycleTheme = () => {
    const themes: Array<'light' | 'dark' | 'system'> = ['light', 'dark', 'system'];
    const currentIndex = themes.indexOf(theme);
    const nextIndex = (currentIndex + 1) % themes.length;
    setTheme(themes[nextIndex]);
  };

  const getIcon = () => {
    if (theme === 'system') {
      return <Monitor className="h-5 w-5" />;
    }
    return resolvedTheme === 'dark' ? (
      <Moon className="h-5 w-5" />
    ) : (
      <Sun className="h-5 w-5" />
    );
  };

  const getLabel = () => {
    if (theme === 'system') return 'System';
    return resolvedTheme === 'dark' ? 'Dark' : 'Light';
  };

  return (
    <motion.button
      onClick={cycleTheme}
      className={cn(
        'relative flex items-center gap-2 p-2 rounded-lg',
        'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]',
        'hover:bg-[var(--color-surface-sunken)]',
        'transition-colors duration-200',
        className
      )}
      whileTap={{ scale: 0.95 }}
      whileHover={{ scale: 1.05 }}
      title={`Theme: ${getLabel()}`}
    >
      <AnimatePresence mode="wait">
        <motion.span
          key={theme + resolvedTheme}
          initial={{ opacity: 0, rotate: -90, scale: 0.5 }}
          animate={{ opacity: 1, rotate: 0, scale: 1 }}
          exit={{ opacity: 0, rotate: 90, scale: 0.5 }}
          transition={{ duration: 0.2 }}
        >
          {getIcon()}
        </motion.span>
      </AnimatePresence>
      {showLabel && (
        <span className="text-sm font-medium">{getLabel()}</span>
      )}
    </motion.button>
  );
}

export function ThemeToggleSwitch({ className }: { className?: string }) {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const isDark = resolvedTheme === 'dark';

  const toggleTheme = () => {
    setTheme(isDark ? 'light' : 'dark');
  };

  return (
    <motion.button
      onClick={toggleTheme}
      className={cn(
        'relative w-14 h-8 rounded-full p-1',
        'bg-[var(--color-surface-sunken)]',
        'border border-[var(--color-border-default)]',
        'transition-colors duration-300',
        className
      )}
      whileTap={{ scale: 0.95 }}
    >
      <motion.div
        className={cn(
          'absolute top-1 w-6 h-6 rounded-full',
          'bg-[var(--color-surface)]',
          'shadow-[var(--shadow-elevation-2)]',
          'flex items-center justify-center'
        )}
        animate={{ x: isDark ? 24 : 0 }}
        transition={{ type: 'spring', stiffness: 500, damping: 30 }}
      >
        <AnimatePresence mode="wait">
          <motion.span
            key={isDark ? 'moon' : 'sun'}
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0 }}
            transition={{ duration: 0.15 }}
            className="text-[var(--color-text-secondary)]"
          >
            {isDark ? (
              <Moon className="h-3.5 w-3.5" />
            ) : (
              <Sun className="h-3.5 w-3.5" />
            )}
          </motion.span>
        </AnimatePresence>
      </motion.div>
    </motion.button>
  );
}
