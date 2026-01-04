# Animations & Interactions

Complete guide to Framer Motion animations, micro-interactions, and delightful user experiences that make Open Insurance feel premium.

---

## Animation Philosophy

### Core Principles

1. **Purpose Over Flash:** Every animation serves a purpose—guiding attention, providing feedback, or establishing spatial relationships
2. **Quick but Smooth:** Snappy interactions (150-250ms) with smooth easing, never sluggish
3. **Natural Motion:** Physics-based springs over linear timing for organic feel
4. **Consistent Language:** Same types of elements animate the same way everywhere
5. **Respect Preferences:** Honor `prefers-reduced-motion` for accessibility

---

## Framer Motion Setup

### Installation

```bash
npm install framer-motion
```

### Motion Configuration

```tsx
// lib/motion.ts
import { Variants, Transition } from 'framer-motion';

// ============ EASING FUNCTIONS ============
export const easing = {
  // Quick out - good for entrances
  easeOut: [0.16, 1, 0.3, 1],
  // Smooth both ends - good for state changes
  easeInOut: [0.65, 0, 0.35, 1],
  // Spring-like - good for interactive elements
  spring: [0.22, 1, 0.36, 1],
  // Bouncy - good for success states
  bounce: [0.68, -0.55, 0.265, 1.55],
  // Anticipation - good for important reveals
  anticipate: [0.4, 0, 0.2, 1],
};

// ============ DURATION SCALE ============
export const duration = {
  instant: 0.05,
  fast: 0.15,
  normal: 0.25,
  slow: 0.35,
  slower: 0.5,
  slowest: 0.7,
};

// ============ SPRING PRESETS ============
export const springPresets = {
  // Snappy for buttons, toggles
  snappy: { type: 'spring', stiffness: 400, damping: 30 },
  // Gentle for page transitions
  gentle: { type: 'spring', stiffness: 200, damping: 25 },
  // Bouncy for success states
  bouncy: { type: 'spring', stiffness: 300, damping: 20 },
  // Slow for large elements
  slow: { type: 'spring', stiffness: 100, damping: 20 },
};

// ============ TRANSITION PRESETS ============
export const transition = {
  fast: { duration: duration.fast, ease: easing.easeOut },
  normal: { duration: duration.normal, ease: easing.spring },
  slow: { duration: duration.slow, ease: easing.easeInOut },
  spring: springPresets.snappy,
  gentle: springPresets.gentle,
};
```

---

## Animation Variants

### Page Transitions

```tsx
// lib/motion/variants.ts

// Fade in and up - default page entrance
export const pageVariants: Variants = {
  initial: {
    opacity: 0,
    y: 20,
  },
  animate: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.4,
      ease: [0.22, 1, 0.36, 1],
    },
  },
  exit: {
    opacity: 0,
    y: -10,
    transition: {
      duration: 0.2,
      ease: [0.65, 0, 0.35, 1],
    },
  },
};

// Slide in from right - for detail pages
export const slideInRight: Variants = {
  initial: {
    opacity: 0,
    x: 40,
  },
  animate: {
    opacity: 1,
    x: 0,
    transition: {
      duration: 0.35,
      ease: [0.22, 1, 0.36, 1],
    },
  },
  exit: {
    opacity: 0,
    x: -20,
    transition: {
      duration: 0.2,
    },
  },
};

// Scale in - for modals
export const scaleIn: Variants = {
  initial: {
    opacity: 0,
    scale: 0.95,
  },
  animate: {
    opacity: 1,
    scale: 1,
    transition: {
      duration: 0.25,
      ease: [0.22, 1, 0.36, 1],
    },
  },
  exit: {
    opacity: 0,
    scale: 0.98,
    transition: {
      duration: 0.15,
    },
  },
};
```

### Stagger Children

```tsx
// Container for staggered children
export const staggerContainer: Variants = {
  initial: {},
  animate: {
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.1,
    },
  },
  exit: {
    transition: {
      staggerChildren: 0.04,
      staggerDirection: -1,
    },
  },
};

// Individual staggered item
export const staggerItem: Variants = {
  initial: {
    opacity: 0,
    y: 20,
  },
  animate: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.4,
      ease: [0.22, 1, 0.36, 1],
    },
  },
  exit: {
    opacity: 0,
    y: -10,
    transition: {
      duration: 0.2,
    },
  },
};

// Fade only stagger - for lists
export const staggerFade: Variants = {
  initial: { opacity: 0 },
  animate: {
    opacity: 1,
    transition: { duration: 0.3 },
  },
  exit: { opacity: 0 },
};
```

### Card Interactions

```tsx
// Lift on hover
export const cardHover: Variants = {
  rest: {
    y: 0,
    scale: 1,
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
  },
  hover: {
    y: -4,
    scale: 1.01,
    boxShadow: '0 12px 24px -4px rgba(0, 0, 0, 0.1)',
    transition: {
      duration: 0.25,
      ease: [0.22, 1, 0.36, 1],
    },
  },
  tap: {
    y: 0,
    scale: 0.99,
    transition: {
      duration: 0.1,
    },
  },
};

// Glow on hover (for important cards)
export const cardGlow: Variants = {
  rest: {
    boxShadow: '0 0 0 0 rgba(22, 119, 255, 0)',
  },
  hover: {
    boxShadow: '0 0 20px 4px rgba(22, 119, 255, 0.15)',
    transition: {
      duration: 0.3,
    },
  },
};
```

### Button Interactions

```tsx
// Press effect for buttons
export const buttonPress = {
  whileTap: { scale: 0.97 },
  whileHover: { scale: 1.02 },
  transition: { type: 'spring', stiffness: 400, damping: 17 },
};

// Subtle lift for secondary buttons
export const buttonLift = {
  whileHover: { y: -2 },
  whileTap: { y: 0 },
  transition: { duration: 0.15 },
};

// Loading spinner inside button
export const buttonLoading: Variants = {
  initial: { opacity: 0, scale: 0.5 },
  animate: {
    opacity: 1,
    scale: 1,
    transition: { duration: 0.2 },
  },
  exit: {
    opacity: 0,
    scale: 0.5,
    transition: { duration: 0.15 },
  },
};
```

---

## Micro-Interactions

### Count Up Animation

```tsx
// components/patterns/CountUp/CountUp.tsx
'use client';

import { useEffect, useRef, useState } from 'react';
import { motion, useSpring, useTransform, useInView } from 'framer-motion';

interface CountUpProps {
  end: number;
  duration?: number;
  prefix?: string;
  suffix?: string;
  decimals?: number;
  className?: string;
}

export function CountUp({
  end,
  duration = 1.5,
  prefix = '',
  suffix = '',
  decimals = 0,
  className,
}: CountUpProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });
  const [hasAnimated, setHasAnimated] = useState(false);

  const spring = useSpring(0, {
    stiffness: 50,
    damping: 20,
    duration: duration * 1000,
  });

  const display = useTransform(spring, (value) => {
    return `${prefix}${value.toLocaleString('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    })}${suffix}`;
  });

  useEffect(() => {
    if (isInView && !hasAnimated) {
      spring.set(end);
      setHasAnimated(true);
    }
  }, [isInView, end, spring, hasAnimated]);

  return (
    <motion.span ref={ref} className={className}>
      {display}
    </motion.span>
  );
}
```

### Progress Bar Animation

```tsx
// components/patterns/GradientProgress/GradientProgress.tsx
'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface GradientProgressProps {
  value: number;
  max?: number;
  gradient?: string;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
  animated?: boolean;
  className?: string;
}

export function GradientProgress({
  value,
  max = 100,
  gradient,
  showLabel = false,
  size = 'md',
  animated = true,
  className,
}: GradientProgressProps) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));

  const getGradient = () => {
    if (gradient) return gradient;
    if (percentage >= 90) return 'from-emerald-400 to-green-600';
    if (percentage >= 70) return 'from-green-400 to-teal-500';
    if (percentage >= 50) return 'from-amber-400 to-yellow-500';
    if (percentage >= 30) return 'from-orange-400 to-red-500';
    return 'from-red-500 to-rose-600';
  };

  const sizes = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-4',
  };

  return (
    <div className={cn('relative', className)}>
      <div
        className={cn(
          'w-full rounded-full bg-gray-100 overflow-hidden',
          sizes[size]
        )}
      >
        <motion.div
          className={cn('h-full rounded-full bg-gradient-to-r', getGradient())}
          initial={animated ? { width: 0 } : { width: `${percentage}%` }}
          animate={{ width: `${percentage}%` }}
          transition={{
            duration: 1,
            ease: [0.22, 1, 0.36, 1],
            delay: 0.2,
          }}
        />
      </div>
      {showLabel && (
        <motion.span
          className="absolute right-0 -top-6 text-sm font-medium text-gray-600"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          {Math.round(percentage)}%
        </motion.span>
      )}
    </div>
  );
}
```

### Pulse Indicator

```tsx
// components/patterns/PulseIndicator/PulseIndicator.tsx
'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface PulseIndicatorProps {
  color?: 'critical' | 'warning' | 'success' | 'info';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const colors = {
  critical: 'bg-critical-500',
  warning: 'bg-warning-500',
  success: 'bg-success-500',
  info: 'bg-info-500',
};

const sizes = {
  sm: 'h-2 w-2',
  md: 'h-3 w-3',
  lg: 'h-4 w-4',
};

export function PulseIndicator({
  color = 'critical',
  size = 'md',
  className,
}: PulseIndicatorProps) {
  return (
    <span className={cn('relative inline-flex', className)}>
      {/* Pulse ring */}
      <motion.span
        className={cn(
          'absolute inline-flex h-full w-full rounded-full opacity-75',
          colors[color]
        )}
        animate={{
          scale: [1, 1.5, 1.5],
          opacity: [0.75, 0, 0],
        }}
        transition={{
          duration: 1.5,
          repeat: Infinity,
          ease: 'easeOut',
        }}
      />
      {/* Static dot */}
      <span
        className={cn('relative inline-flex rounded-full', colors[color], sizes[size])}
      />
    </span>
  );
}
```

### Hover Reveal

```tsx
// components/patterns/HoverReveal/HoverReveal.tsx
'use client';

import { motion } from 'framer-motion';

interface HoverRevealProps {
  children: React.ReactNode;
  revealContent: React.ReactNode;
}

export function HoverReveal({ children, revealContent }: HoverRevealProps) {
  return (
    <motion.div className="relative group" whileHover="hover" initial="rest">
      <motion.div
        variants={{
          rest: { opacity: 1 },
          hover: { opacity: 0.3 },
        }}
        transition={{ duration: 0.2 }}
      >
        {children}
      </motion.div>

      <motion.div
        className="absolute inset-0 flex items-center justify-center"
        variants={{
          rest: { opacity: 0, y: 10 },
          hover: { opacity: 1, y: 0 },
        }}
        transition={{ duration: 0.2 }}
      >
        {revealContent}
      </motion.div>
    </motion.div>
  );
}
```

### Skeleton Loading

```tsx
// components/primitives/Skeleton/Skeleton.tsx
'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular';
  animation?: 'pulse' | 'wave' | 'none';
}

export function Skeleton({
  className,
  variant = 'rectangular',
  animation = 'wave',
}: SkeletonProps) {
  const variants = {
    text: 'h-4 w-full rounded',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
  };

  if (animation === 'wave') {
    return (
      <div
        className={cn(
          'relative overflow-hidden bg-gray-200',
          variants[variant],
          className
        )}
      >
        <motion.div
          className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/50 to-transparent"
          animate={{ translateX: ['−100%', '100%'] }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            ease: 'linear',
          }}
        />
      </div>
    );
  }

  if (animation === 'pulse') {
    return (
      <motion.div
        className={cn('bg-gray-200', variants[variant], className)}
        animate={{ opacity: [1, 0.5, 1] }}
        transition={{ duration: 1.5, repeat: Infinity }}
      />
    );
  }

  return (
    <div className={cn('bg-gray-200', variants[variant], className)} />
  );
}
```

---

## Page Transition Components

### AnimatedPage Wrapper

```tsx
// components/layouts/AnimatedPage/AnimatedPage.tsx
'use client';

import { motion } from 'framer-motion';
import { pageVariants } from '@/lib/motion/variants';

interface AnimatedPageProps {
  children: React.ReactNode;
  className?: string;
}

export function AnimatedPage({ children, className }: AnimatedPageProps) {
  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className={className}
    >
      {children}
    </motion.div>
  );
}
```

### AnimatedList

```tsx
// components/patterns/AnimatedList/AnimatedList.tsx
'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { staggerContainer, staggerItem } from '@/lib/motion/variants';

interface AnimatedListProps<T> {
  items: T[];
  keyExtractor: (item: T) => string;
  renderItem: (item: T, index: number) => React.ReactNode;
  className?: string;
}

export function AnimatedList<T>({
  items,
  keyExtractor,
  renderItem,
  className,
}: AnimatedListProps<T>) {
  return (
    <motion.div
      variants={staggerContainer}
      initial="initial"
      animate="animate"
      exit="exit"
      className={className}
    >
      <AnimatePresence mode="popLayout">
        {items.map((item, index) => (
          <motion.div
            key={keyExtractor(item)}
            variants={staggerItem}
            layout
            layoutId={keyExtractor(item)}
          >
            {renderItem(item, index)}
          </motion.div>
        ))}
      </AnimatePresence>
    </motion.div>
  );
}
```

---

## Success & Feedback Animations

### Success Checkmark

```tsx
// components/patterns/SuccessCheckmark/SuccessCheckmark.tsx
'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface SuccessCheckmarkProps {
  size?: number;
  className?: string;
}

export function SuccessCheckmark({ size = 64, className }: SuccessCheckmarkProps) {
  return (
    <motion.div
      className={cn('inline-flex', className)}
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      transition={{ type: 'spring', stiffness: 200, damping: 15 }}
    >
      <svg width={size} height={size} viewBox="0 0 64 64">
        {/* Background circle */}
        <motion.circle
          cx="32"
          cy="32"
          r="30"
          fill="none"
          stroke="#10B981"
          strokeWidth="3"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        />

        {/* Checkmark */}
        <motion.path
          d="M20 32 L28 40 L44 24"
          fill="none"
          stroke="#10B981"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.3, delay: 0.4, ease: 'easeOut' }}
        />
      </svg>
    </motion.div>
  );
}
```

### Confetti Burst

```tsx
// components/patterns/ConfettiBurst/ConfettiBurst.tsx
'use client';

import { motion } from 'framer-motion';
import { useMemo } from 'react';

interface ConfettiBurstProps {
  count?: number;
  colors?: string[];
}

export function ConfettiBurst({
  count = 30,
  colors = ['#10B981', '#1677FF', '#F59E0B', '#EF4444', '#8B5CF6'],
}: ConfettiBurstProps) {
  const particles = useMemo(() => {
    return Array.from({ length: count }, (_, i) => ({
      id: i,
      color: colors[i % colors.length],
      angle: (i / count) * 360,
      distance: 50 + Math.random() * 100,
      rotation: Math.random() * 720 - 360,
      scale: 0.5 + Math.random() * 0.5,
    }));
  }, [count, colors]);

  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden">
      {particles.map((particle) => (
        <motion.div
          key={particle.id}
          className="absolute left-1/2 top-1/2 w-2 h-2 rounded-sm"
          style={{ backgroundColor: particle.color }}
          initial={{
            x: 0,
            y: 0,
            scale: 0,
            rotate: 0,
          }}
          animate={{
            x: Math.cos((particle.angle * Math.PI) / 180) * particle.distance,
            y: Math.sin((particle.angle * Math.PI) / 180) * particle.distance,
            scale: [0, particle.scale, 0],
            rotate: particle.rotation,
          }}
          transition={{
            duration: 0.8,
            ease: [0.22, 1, 0.36, 1],
          }}
        />
      ))}
    </div>
  );
}
```

---

## Toast Notifications

```tsx
// components/shared/Toast/Toast.tsx
'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, XCircle, AlertCircle, Info, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ToastProps {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  description?: string;
  onClose: (id: string) => void;
}

const icons = {
  success: CheckCircle,
  error: XCircle,
  warning: AlertCircle,
  info: Info,
};

const styles = {
  success: 'bg-success-50 border-success-200 text-success-800',
  error: 'bg-critical-50 border-critical-200 text-critical-800',
  warning: 'bg-warning-50 border-warning-200 text-warning-800',
  info: 'bg-info-50 border-info-200 text-info-800',
};

export function Toast({ id, type, title, description, onClose }: ToastProps) {
  const Icon = icons[type];

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, x: 100, scale: 0.95 }}
      transition={{ type: 'spring', stiffness: 300, damping: 25 }}
      className={cn(
        'flex items-start gap-3 p-4 rounded-xl border shadow-lg backdrop-blur',
        styles[type]
      )}
    >
      <Icon className="h-5 w-5 flex-shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <p className="font-medium">{title}</p>
        {description && (
          <p className="text-sm opacity-80 mt-1">{description}</p>
        )}
      </div>
      <button
        onClick={() => onClose(id)}
        className="flex-shrink-0 p-1 rounded-full hover:bg-black/5 transition-colors"
      >
        <X className="h-4 w-4" />
      </button>
    </motion.div>
  );
}

export function ToastContainer({ toasts, onClose }) {
  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 w-96">
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <Toast key={toast.id} {...toast} onClose={onClose} />
        ))}
      </AnimatePresence>
    </div>
  );
}
```

---

## Scroll Animations

### Scroll Reveal

```tsx
// components/patterns/ScrollReveal/ScrollReveal.tsx
'use client';

import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';

interface ScrollRevealProps {
  children: React.ReactNode;
  direction?: 'up' | 'down' | 'left' | 'right';
  delay?: number;
  className?: string;
}

export function ScrollReveal({
  children,
  direction = 'up',
  delay = 0,
  className,
}: ScrollRevealProps) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  const directions = {
    up: { y: 40 },
    down: { y: -40 },
    left: { x: 40 },
    right: { x: -40 },
  };

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, ...directions[direction] }}
      animate={isInView ? { opacity: 1, x: 0, y: 0 } : {}}
      transition={{
        duration: 0.6,
        delay,
        ease: [0.22, 1, 0.36, 1],
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
```

### Parallax Effect

```tsx
// components/patterns/Parallax/Parallax.tsx
'use client';

import { motion, useScroll, useTransform } from 'framer-motion';
import { useRef } from 'react';

interface ParallaxProps {
  children: React.ReactNode;
  offset?: number;
  className?: string;
}

export function Parallax({ children, offset = 50, className }: ParallaxProps) {
  const ref = useRef(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ['start end', 'end start'],
  });

  const y = useTransform(scrollYProgress, [0, 1], [offset, -offset]);

  return (
    <motion.div ref={ref} style={{ y }} className={className}>
      {children}
    </motion.div>
  );
}
```

---

## Gesture Interactions

### Swipeable Card

```tsx
// components/patterns/SwipeableCard/SwipeableCard.tsx
'use client';

import { motion, useMotionValue, useTransform, PanInfo } from 'framer-motion';

interface SwipeableCardProps {
  children: React.ReactNode;
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  leftAction?: React.ReactNode;
  rightAction?: React.ReactNode;
}

export function SwipeableCard({
  children,
  onSwipeLeft,
  onSwipeRight,
  leftAction,
  rightAction,
}: SwipeableCardProps) {
  const x = useMotionValue(0);
  const opacity = useTransform(x, [-100, 0, 100], [0.5, 1, 0.5]);
  const scale = useTransform(x, [-100, 0, 100], [0.95, 1, 0.95]);

  const handleDragEnd = (event: MouseEvent | TouchEvent, info: PanInfo) => {
    if (info.offset.x > 100 && onSwipeRight) {
      onSwipeRight();
    } else if (info.offset.x < -100 && onSwipeLeft) {
      onSwipeLeft();
    }
  };

  return (
    <div className="relative">
      {/* Background actions */}
      <div className="absolute inset-0 flex justify-between items-center px-4">
        {leftAction && <div className="text-success-500">{leftAction}</div>}
        {rightAction && <div className="text-critical-500">{rightAction}</div>}
      </div>

      {/* Swipeable content */}
      <motion.div
        drag="x"
        dragConstraints={{ left: 0, right: 0 }}
        dragElastic={0.2}
        onDragEnd={handleDragEnd}
        style={{ x, opacity, scale }}
        className="relative bg-white rounded-xl shadow-md cursor-grab active:cursor-grabbing"
      >
        {children}
      </motion.div>
    </div>
  );
}
```

---

## Reduced Motion Support

```tsx
// hooks/useReducedMotion.ts
'use client';

import { useReducedMotion as useFramerReducedMotion } from 'framer-motion';

// Get safe animation variants based on user preference
export function useSafeAnimation() {
  const prefersReducedMotion = useFramerReducedMotion();

  return {
    // Returns static variant if reduced motion preferred
    animate: prefersReducedMotion ? 'reduced' : 'full',

    // Helper to conditionally apply animations
    maybeAnimate: <T,>(animation: T): T | {} =>
      prefersReducedMotion ? {} : animation,

    // Get appropriate transition
    getTransition: (duration: number) =>
      prefersReducedMotion ? { duration: 0 } : { duration },
  };
}

// Example usage in component
export function AnimatedCard({ children }) {
  const { maybeAnimate, getTransition } = useSafeAnimation();

  return (
    <motion.div
      initial={maybeAnimate({ opacity: 0, y: 20 })}
      animate={{ opacity: 1, y: 0 }}
      transition={getTransition(0.3)}
    >
      {children}
    </motion.div>
  );
}
```

---

## Animation Best Practices

### Do's

1. **Use springs for interactive elements** - buttons, cards, toggles
2. **Stagger lists** - gives rhythm and doesn't overwhelm
3. **Keep durations short** - 150-350ms for most interactions
4. **Use layout animations** - smooth reordering of lists
5. **Animate presence** - exit animations are as important as entrances

### Don'ts

1. **Don't animate everything** - important content should be immediately visible
2. **Don't use long delays** - users shouldn't wait for content
3. **Don't block interaction** - animations shouldn't prevent clicks
4. **Don't loop infinitely** - except for loading states
5. **Don't ignore reduced motion** - always provide fallbacks

---

## Next Steps

Continue to [06-three-js-experiences.md](./06-three-js-experiences.md) for immersive 3D visualizations.
