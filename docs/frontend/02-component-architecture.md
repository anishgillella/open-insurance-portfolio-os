# Component Architecture

A hierarchical component system that scales from atomic primitives to complex domain features, with a dedicated Three.js layer for immersive 3D experiences.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PAGES (app/)                                    │
│     Dashboard, Properties, Property Detail, Gaps, Chat, Renewals...        │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────────┐
│                           LAYOUTS (layouts/)                                 │
│              AppShell, PageContainer, SplitView, FullScreenModal            │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────────┐
│                          FEATURES (features/)                                │
│    Dashboard, HealthScore, Gaps, Renewals, Chat, Documents, Compliance     │
└────────────┬─────────────────────┴──────────────────────┬───────────────────┘
             │                                             │
┌────────────▼────────────┐                 ┌──────────────▼──────────────────┐
│    PATTERNS (patterns/)  │                 │       THREE.JS (three/)         │
│  DataCard, GlassCard,   │                 │  HealthScoreGlobe, PropertyCity │
│  StatusBadge, ScoreRing │                 │  CoverageShield, RenewalPath    │
└────────────┬────────────┘                 └──────────────┬──────────────────┘
             │                                             │
┌────────────▼─────────────────────────────────────────────▼──────────────────┐
│                         PRIMITIVES (primitives/)                             │
│          Button, Card, Badge, Dialog, Input, Select, Progress...            │
│                        (Extended shadcn/ui)                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
frontend/
├── app/                          # Next.js App Router pages
│   ├── layout.tsx               # Root layout with providers
│   ├── page.tsx                 # Dashboard
│   ├── properties/
│   ├── gaps/
│   ├── chat/
│   ├── documents/
│   └── renewals/
│
├── components/
│   ├── primitives/              # Atomic UI elements
│   │   ├── Button/
│   │   ├── Card/
│   │   ├── Badge/
│   │   ├── Dialog/
│   │   ├── Input/
│   │   ├── Select/
│   │   ├── Progress/
│   │   ├── Skeleton/
│   │   ├── Tooltip/
│   │   ├── Avatar/
│   │   └── index.ts
│   │
│   ├── patterns/                # Reusable compound components
│   │   ├── GlassCard/
│   │   ├── DataCard/
│   │   ├── StatusBadge/
│   │   ├── ScoreRing/
│   │   ├── GradientProgress/
│   │   ├── TrendIndicator/
│   │   ├── TimelineItem/
│   │   ├── AlertCard/
│   │   ├── ComparisonRow/
│   │   ├── EmptyState/
│   │   ├── LoadingState/
│   │   └── index.ts
│   │
│   ├── three/                   # Three.js/R3F components
│   │   ├── HealthScoreGlobe/
│   │   ├── PropertyCity/
│   │   ├── CoverageShield/
│   │   ├── RenewalPath/
│   │   ├── GradientMeshBg/
│   │   ├── DocumentPipeline/
│   │   ├── shared/
│   │   │   ├── FloatingLabel.tsx
│   │   │   ├── GlowingSphere.tsx
│   │   │   ├── ParticleSystem.tsx
│   │   │   ├── AnimatedRing.tsx
│   │   │   └── Scene.tsx
│   │   └── index.ts
│   │
│   ├── features/                # Domain-specific components
│   │   ├── dashboard/
│   │   │   ├── PortfolioStats/
│   │   │   ├── ExpirationTimeline/
│   │   │   ├── AlertsPanel/
│   │   │   ├── HealthScoreWidget/
│   │   │   ├── QuickActions/
│   │   │   └── index.ts
│   │   │
│   │   ├── properties/
│   │   │   ├── PropertyCard/
│   │   │   ├── PropertyGrid/
│   │   │   ├── PropertyHeader/
│   │   │   ├── PropertyFilters/
│   │   │   ├── BuildingsList/
│   │   │   ├── InsuranceSummary/
│   │   │   └── index.ts
│   │   │
│   │   ├── health-score/
│   │   │   ├── HealthScoreHero/
│   │   │   ├── ComponentBreakdown/
│   │   │   ├── ScoreHistory/
│   │   │   ├── RecommendationList/
│   │   │   ├── GradeComparison/
│   │   │   └── index.ts
│   │   │
│   │   ├── policies/
│   │   │   ├── PolicyCard/
│   │   │   ├── PolicyList/
│   │   │   ├── CoverageTable/
│   │   │   ├── EndorsementList/
│   │   │   ├── PolicyComparison/
│   │   │   └── index.ts
│   │   │
│   │   ├── gaps/
│   │   │   ├── GapCard/
│   │   │   ├── GapsList/
│   │   │   ├── GapDetail/
│   │   │   ├── GapAnalysis/
│   │   │   ├── GapFilters/
│   │   │   ├── AcknowledgeDialog/
│   │   │   ├── ResolveDialog/
│   │   │   └── index.ts
│   │   │
│   │   ├── renewals/
│   │   │   ├── RenewalTimeline/
│   │   │   ├── ForecastChart/
│   │   │   ├── MarketContext/
│   │   │   ├── ReadinessScore/
│   │   │   ├── NegotiationInsights/
│   │   │   ├── BrokerPackage/
│   │   │   └── index.ts
│   │   │
│   │   ├── documents/
│   │   │   ├── DocumentUpload/
│   │   │   ├── UploadWizard/
│   │   │   ├── DocumentGrid/
│   │   │   ├── DocumentCard/
│   │   │   ├── ProcessingStatus/
│   │   │   ├── DocumentViewer/
│   │   │   └── index.ts
│   │   │
│   │   ├── chat/
│   │   │   ├── ChatInterface/
│   │   │   ├── MessageBubble/
│   │   │   ├── StreamingText/
│   │   │   ├── SourceCitation/
│   │   │   ├── SuggestedQuestions/
│   │   │   ├── PropertySelector/
│   │   │   └── index.ts
│   │   │
│   │   └── compliance/
│   │       ├── ComplianceStatus/
│   │       ├── RequirementCheck/
│   │       ├── LenderCard/
│   │       ├── ComplianceReport/
│   │       └── index.ts
│   │
│   ├── layouts/
│   │   ├── AppShell/
│   │   │   ├── AppShell.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   ├── MobileNav.tsx
│   │   │   └── index.ts
│   │   ├── PageContainer/
│   │   ├── SplitView/
│   │   ├── FullScreenModal/
│   │   └── index.ts
│   │
│   └── shared/
│       ├── Navigation/
│       ├── CommandPalette/
│       ├── NotificationCenter/
│       ├── GlobalSearch/
│       ├── ErrorBoundary/
│       └── index.ts
│
├── hooks/
│   ├── queries/                 # React Query hooks
│   ├── mutations/               # React Query mutations
│   ├── useMediaQuery.ts
│   ├── useDebounce.ts
│   └── index.ts
│
├── lib/
│   ├── api/                     # API client
│   ├── utils/                   # Utility functions
│   └── constants/               # App constants
│
├── types/
│   ├── api.ts                   # API response types
│   ├── components.ts            # Component prop types
│   └── index.ts
│
└── styles/
    └── globals.css              # Global styles & CSS variables
```

---

## Primitives Layer

Extended shadcn/ui components with Open Insurance styling.

### Button

```tsx
// components/primitives/Button/Button.tsx
import { cn } from '@/lib/utils';
import { cva, type VariantProps } from 'class-variance-authority';
import { motion } from 'framer-motion';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-lg font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        primary: 'bg-gradient-to-r from-primary-500 to-primary-600 text-white shadow-md hover:shadow-lg hover:from-primary-400 hover:to-primary-500',
        secondary: 'bg-white border border-gray-200 text-gray-900 hover:bg-gray-50 hover:border-gray-300',
        ghost: 'hover:bg-gray-100 text-gray-700',
        danger: 'bg-gradient-to-r from-critical-400 to-critical-500 text-white shadow-md hover:shadow-lg',
        success: 'bg-gradient-to-r from-success-400 to-success-500 text-white shadow-md hover:shadow-lg',
      },
      size: {
        sm: 'h-8 px-3 text-sm',
        md: 'h-10 px-4 text-sm',
        lg: 'h-12 px-6 text-base',
        xl: 'h-14 px-8 text-lg',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);

interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  loading?: boolean;
}

export function Button({
  className,
  variant,
  size,
  loading,
  children,
  ...props
}: ButtonProps) {
  return (
    <motion.button
      className={cn(buttonVariants({ variant, size }), className)}
      whileTap={{ scale: 0.97 }}
      whileHover={{ y: -2 }}
      disabled={loading || props.disabled}
      {...props}
    >
      {loading ? <Spinner className="mr-2" /> : null}
      {children}
    </motion.button>
  );
}
```

### Card

```tsx
// components/primitives/Card/Card.tsx
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'glass' | 'elevated' | 'interactive';
  padding?: 'sm' | 'md' | 'lg' | 'none';
}

export function Card({
  className,
  variant = 'default',
  padding = 'md',
  children,
  ...props
}: CardProps) {
  const variants = {
    default: 'bg-white border border-gray-100 shadow-elevation-1',
    glass: 'bg-white/70 backdrop-blur-xl border border-white/20 shadow-glass',
    elevated: 'bg-white shadow-elevation-3',
    interactive: 'bg-white shadow-elevation-2 hover:shadow-elevation-4 hover:-translate-y-1 cursor-pointer',
  };

  const paddings = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  const Component = variant === 'interactive' ? motion.div : 'div';

  return (
    <Component
      className={cn(
        'rounded-xl transition-all duration-300',
        variants[variant],
        paddings[padding],
        className
      )}
      {...(variant === 'interactive' && {
        whileHover: { y: -4, scale: 1.01 },
        transition: { duration: 0.2 },
      })}
      {...props}
    >
      {children}
    </Component>
  );
}
```

### Badge

```tsx
// components/primitives/Badge/Badge.tsx
import { cn } from '@/lib/utils';
import { cva, type VariantProps } from 'class-variance-authority';

const badgeVariants = cva(
  'inline-flex items-center rounded-md px-2.5 py-0.5 text-xs font-medium transition-colors',
  {
    variants: {
      variant: {
        critical: 'bg-critical-50 text-critical-600 border border-critical-200',
        warning: 'bg-warning-50 text-warning-600 border border-warning-200',
        success: 'bg-success-50 text-success-600 border border-success-200',
        info: 'bg-info-50 text-info-600 border border-info-200',
        neutral: 'bg-gray-100 text-gray-600 border border-gray-200',
      },
      size: {
        sm: 'text-[10px] px-1.5 py-0.5',
        md: 'text-xs px-2.5 py-0.5',
        lg: 'text-sm px-3 py-1',
      },
    },
    defaultVariants: {
      variant: 'neutral',
      size: 'md',
    },
  }
);

interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {
  dot?: boolean;
}

export function Badge({ className, variant, size, dot, children, ...props }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant, size }), className)} {...props}>
      {dot && (
        <span
          className={cn(
            'mr-1.5 h-1.5 w-1.5 rounded-full',
            variant === 'critical' && 'bg-critical-500',
            variant === 'warning' && 'bg-warning-500',
            variant === 'success' && 'bg-success-500',
            variant === 'info' && 'bg-info-500'
          )}
        />
      )}
      {children}
    </span>
  );
}
```

---

## Patterns Layer

Compound components combining primitives with specific behaviors.

### GlassCard

```tsx
// components/patterns/GlassCard/GlassCard.tsx
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  gradient?: string;
  hover?: boolean;
  glow?: 'primary' | 'success' | 'warning' | 'critical';
}

export function GlassCard({
  className,
  gradient,
  hover = true,
  glow,
  children,
  ...props
}: GlassCardProps) {
  const glowColors = {
    primary: 'shadow-glow-primary',
    success: 'shadow-glow-success',
    warning: 'shadow-glow-warning',
    critical: 'shadow-glow-critical',
  };

  return (
    <motion.div
      className={cn(
        'relative overflow-hidden rounded-2xl',
        'bg-white/70 backdrop-blur-xl',
        'border border-white/20',
        'shadow-glass',
        hover && 'transition-all duration-300 hover:shadow-glass-hover hover:bg-white/80',
        glow && glowColors[glow],
        className
      )}
      whileHover={hover ? { y: -4 } : undefined}
      {...props}
    >
      {/* Gradient overlay */}
      {gradient && (
        <div
          className={cn(
            'absolute inset-0 opacity-5',
            `bg-gradient-to-br ${gradient}`
          )}
        />
      )}

      {/* Content */}
      <div className="relative">{children}</div>
    </motion.div>
  );
}
```

### DataCard

```tsx
// components/patterns/DataCard/DataCard.tsx
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';
import { TrendIndicator } from '../TrendIndicator';
import { GlassCard } from '../GlassCard';

interface DataCardProps {
  label: string;
  value: string | number;
  trend?: {
    value: number;
    direction: 'up' | 'down' | 'stable';
    period?: string;
  };
  icon?: React.ReactNode;
  variant?: 'default' | 'glass';
  size?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
}

export function DataCard({
  label,
  value,
  trend,
  icon,
  variant = 'default',
  size = 'md',
  onClick,
}: DataCardProps) {
  const sizes = {
    sm: { value: 'text-2xl', label: 'text-xs' },
    md: { value: 'text-3xl', label: 'text-sm' },
    lg: { value: 'text-4xl', label: 'text-base' },
  };

  const CardWrapper = variant === 'glass' ? GlassCard : 'div';

  return (
    <CardWrapper
      className={cn(
        'p-6 cursor-pointer',
        variant === 'default' && 'bg-white rounded-xl shadow-elevation-2 hover:shadow-elevation-3 transition-all'
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className={cn('text-gray-500 font-medium', sizes[size].label)}>
            {label}
          </p>
          <motion.p
            className={cn('font-bold text-gray-900 mt-1', sizes[size].value)}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            {typeof value === 'number' ? (
              <CountUp end={value} duration={1.5} />
            ) : (
              value
            )}
          </motion.p>
          {trend && (
            <TrendIndicator
              value={trend.value}
              direction={trend.direction}
              period={trend.period}
              className="mt-2"
            />
          )}
        </div>
        {icon && (
          <div className="p-3 bg-primary-50 rounded-xl text-primary-500">
            {icon}
          </div>
        )}
      </div>
    </CardWrapper>
  );
}
```

### ScoreRing

```tsx
// components/patterns/ScoreRing/ScoreRing.tsx
'use client';

import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

interface ScoreRingProps {
  score: number;
  size?: number;
  strokeWidth?: number;
  showLabel?: boolean;
  animated?: boolean;
  className?: string;
}

const gradeConfig = {
  A: { color: 'stroke-emerald-500', gradient: 'from-emerald-400 to-green-600', label: 'Excellent' },
  B: { color: 'stroke-teal-500', gradient: 'from-green-400 to-teal-500', label: 'Good' },
  C: { color: 'stroke-amber-500', gradient: 'from-amber-400 to-yellow-500', label: 'Fair' },
  D: { color: 'stroke-orange-500', gradient: 'from-orange-400 to-red-500', label: 'Poor' },
  F: { color: 'stroke-red-500', gradient: 'from-red-500 to-rose-600', label: 'Critical' },
};

function getGrade(score: number): keyof typeof gradeConfig {
  if (score >= 90) return 'A';
  if (score >= 80) return 'B';
  if (score >= 70) return 'C';
  if (score >= 60) return 'D';
  return 'F';
}

export function ScoreRing({
  score,
  size = 200,
  strokeWidth = 12,
  showLabel = true,
  animated = true,
  className,
}: ScoreRingProps) {
  const [isVisible, setIsVisible] = useState(!animated);
  const grade = getGrade(score);
  const config = gradeConfig[grade];

  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = (score / 100) * circumference;

  useEffect(() => {
    if (animated) {
      const timer = setTimeout(() => setIsVisible(true), 100);
      return () => clearTimeout(timer);
    }
  }, [animated]);

  return (
    <div className={cn('relative inline-flex', className)} style={{ width: size, height: size }}>
      <svg
        className="transform -rotate-90"
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
      >
        {/* Background ring */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-gray-100"
        />

        {/* Progress ring */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          className={config.color}
          initial={{ strokeDasharray: circumference, strokeDashoffset: circumference }}
          animate={isVisible ? { strokeDashoffset: circumference - progress } : undefined}
          transition={{ duration: 1.5, ease: [0.22, 1, 0.36, 1] }}
          style={{
            filter: `drop-shadow(0 0 8px currentColor)`,
          }}
        />
      </svg>

      {/* Center content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <motion.span
          className="text-5xl font-bold text-gray-900"
          initial={{ opacity: 0, scale: 0.5 }}
          animate={isVisible ? { opacity: 1, scale: 1 } : undefined}
          transition={{ delay: 0.3, duration: 0.5, ease: 'backOut' }}
        >
          {score}
        </motion.span>
        {showLabel && (
          <motion.span
            className={cn('text-lg font-semibold', config.color.replace('stroke-', 'text-'))}
            initial={{ opacity: 0 }}
            animate={isVisible ? { opacity: 1 } : undefined}
            transition={{ delay: 0.6, duration: 0.3 }}
          >
            Grade {grade}
          </motion.span>
        )}
      </div>
    </div>
  );
}
```

### StatusBadge

```tsx
// components/patterns/StatusBadge/StatusBadge.tsx
import { cn } from '@/lib/utils';
import { Badge } from '@/components/primitives/Badge';
import { motion } from 'framer-motion';

type Severity = 'critical' | 'warning' | 'success' | 'info';

interface StatusBadgeProps {
  severity: Severity;
  label: string;
  pulse?: boolean;
  icon?: React.ReactNode;
  className?: string;
}

export function StatusBadge({
  severity,
  label,
  pulse = false,
  icon,
  className,
}: StatusBadgeProps) {
  return (
    <Badge variant={severity} className={cn('relative', className)}>
      {pulse && (
        <motion.span
          className={cn(
            'absolute -left-0.5 -top-0.5 h-2 w-2 rounded-full',
            severity === 'critical' && 'bg-critical-500',
            severity === 'warning' && 'bg-warning-500'
          )}
          animate={{ scale: [1, 1.5, 1], opacity: [1, 0.5, 1] }}
          transition={{ duration: 1.5, repeat: Infinity }}
        />
      )}
      {icon && <span className="mr-1">{icon}</span>}
      {label}
    </Badge>
  );
}
```

### TrendIndicator

```tsx
// components/patterns/TrendIndicator/TrendIndicator.tsx
import { cn } from '@/lib/utils';
import { ArrowUpIcon, ArrowDownIcon, MinusIcon } from 'lucide-react';

interface TrendIndicatorProps {
  value: number;
  direction: 'up' | 'down' | 'stable';
  period?: string;
  invert?: boolean; // For metrics where down is good (e.g., gaps)
  className?: string;
}

export function TrendIndicator({
  value,
  direction,
  period = 'from last month',
  invert = false,
  className,
}: TrendIndicatorProps) {
  const isPositive = invert ? direction === 'down' : direction === 'up';
  const isNegative = invert ? direction === 'up' : direction === 'down';

  const icons = {
    up: ArrowUpIcon,
    down: ArrowDownIcon,
    stable: MinusIcon,
  };

  const Icon = icons[direction];

  return (
    <div className={cn('flex items-center gap-1 text-sm', className)}>
      <span
        className={cn(
          'flex items-center gap-0.5 font-medium',
          isPositive && 'text-success-600',
          isNegative && 'text-critical-600',
          direction === 'stable' && 'text-gray-500'
        )}
      >
        <Icon className="h-3.5 w-3.5" />
        {Math.abs(value)}%
      </span>
      <span className="text-gray-400">{period}</span>
    </div>
  );
}
```

---

## Three.js Components Layer

Immersive 3D visualizations using React Three Fiber.

### Scene (Base Component)

```tsx
// components/three/shared/Scene.tsx
'use client';

import { Canvas } from '@react-three/fiber';
import { Suspense } from 'react';
import { Environment, Preload } from '@react-three/drei';
import { EffectComposer, Bloom } from '@react-three/postprocessing';

interface SceneProps {
  children: React.ReactNode;
  className?: string;
  bloom?: boolean;
  environment?: 'studio' | 'sunset' | 'dawn' | 'night';
}

export function Scene({
  children,
  className,
  bloom = true,
  environment = 'studio',
}: SceneProps) {
  return (
    <div className={className}>
      <Canvas
        camera={{ position: [0, 0, 5], fov: 50 }}
        dpr={[1, 2]}
        gl={{ antialias: true, alpha: true }}
      >
        <Suspense fallback={null}>
          <ambientLight intensity={0.4} />
          <pointLight position={[10, 10, 10]} intensity={0.8} />

          {children}

          <Environment preset={environment} />

          {bloom && (
            <EffectComposer>
              <Bloom
                luminanceThreshold={0.8}
                luminanceSmoothing={0.9}
                intensity={0.5}
              />
            </EffectComposer>
          )}

          <Preload all />
        </Suspense>
      </Canvas>
    </div>
  );
}
```

### HealthScoreGlobe

```tsx
// components/three/HealthScoreGlobe/HealthScoreGlobe.tsx
'use client';

import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Sphere, Html, Float } from '@react-three/drei';
import * as THREE from 'three';
import { Scene } from '../shared/Scene';

interface HealthScoreGlobeProps {
  score: number;
  components?: Array<{
    name: string;
    score: number;
    weight: number;
  }>;
  className?: string;
}

function Globe({ score, components }: Omit<HealthScoreGlobeProps, 'className'>) {
  const meshRef = useRef<THREE.Mesh>(null);
  const particlesRef = useRef<THREE.Points>(null);

  // Calculate color based on score
  const getColor = (score: number) => {
    if (score >= 90) return new THREE.Color('#10B981');
    if (score >= 80) return new THREE.Color('#14B8A6');
    if (score >= 70) return new THREE.Color('#F59E0B');
    if (score >= 60) return new THREE.Color('#F97316');
    return new THREE.Color('#EF4444');
  };

  const color = getColor(score);

  // Rotate globe slowly
  useFrame(({ clock }) => {
    if (meshRef.current) {
      meshRef.current.rotation.y = clock.getElapsedTime() * 0.1;
    }
    if (particlesRef.current) {
      particlesRef.current.rotation.y = -clock.getElapsedTime() * 0.05;
    }
  });

  // Create particle positions for orbiting components
  const particleCount = 1000;
  const particlePositions = new Float32Array(particleCount * 3);
  for (let i = 0; i < particleCount; i++) {
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);
    const r = 2 + Math.random() * 0.5;
    particlePositions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
    particlePositions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
    particlePositions[i * 3 + 2] = r * Math.cos(phi);
  }

  return (
    <group>
      {/* Main sphere */}
      <Float speed={2} rotationIntensity={0.2} floatIntensity={0.3}>
        <Sphere ref={meshRef} args={[1.5, 64, 64]}>
          <meshStandardMaterial
            color={color}
            metalness={0.3}
            roughness={0.4}
            emissive={color}
            emissiveIntensity={0.2}
          />
        </Sphere>
      </Float>

      {/* Orbiting particles */}
      <points ref={particlesRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={particleCount}
            array={particlePositions}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          size={0.02}
          color={color}
          transparent
          opacity={0.6}
          sizeAttenuation
        />
      </points>

      {/* Score label */}
      <Html center position={[0, 0, 0]}>
        <div className="text-center pointer-events-none select-none">
          <div className="text-6xl font-bold text-white drop-shadow-lg">
            {score}
          </div>
          <div className="text-lg font-semibold text-white/80">
            Health Score
          </div>
        </div>
      </Html>

      {/* Component labels */}
      {components?.map((component, i) => {
        const angle = (i / components.length) * Math.PI * 2;
        const x = Math.cos(angle) * 2.5;
        const z = Math.sin(angle) * 2.5;

        return (
          <Html key={component.name} position={[x, 0, z]}>
            <div className="px-2 py-1 bg-white/90 backdrop-blur rounded-lg shadow-lg text-xs whitespace-nowrap">
              <div className="font-medium text-gray-900">{component.name}</div>
              <div className="text-gray-500">{component.score}%</div>
            </div>
          </Html>
        );
      })}
    </group>
  );
}

export function HealthScoreGlobe({ score, components, className }: HealthScoreGlobeProps) {
  return (
    <Scene className={className} bloom>
      <Globe score={score} components={components} />
    </Scene>
  );
}
```

### GradientMeshBg

```tsx
// components/three/GradientMeshBg/GradientMeshBg.tsx
'use client';

import { useRef, useMemo } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { Scene } from '../shared/Scene';

function GradientMesh() {
  const meshRef = useRef<THREE.Mesh>(null);
  const { mouse } = useThree();

  // Create gradient shader
  const shader = useMemo(
    () => ({
      uniforms: {
        uTime: { value: 0 },
        uMouse: { value: new THREE.Vector2(0, 0) },
        uColor1: { value: new THREE.Color('#1677FF') },
        uColor2: { value: new THREE.Color('#10B981') },
        uColor3: { value: new THREE.Color('#F59E0B') },
      },
      vertexShader: `
        varying vec2 vUv;
        uniform float uTime;
        uniform vec2 uMouse;

        void main() {
          vUv = uv;
          vec3 pos = position;

          // Subtle wave effect
          float wave = sin(pos.x * 2.0 + uTime * 0.5) * 0.1;
          wave += sin(pos.y * 2.0 + uTime * 0.3) * 0.1;
          pos.z += wave;

          // Mouse influence
          float dist = distance(uv, uMouse * 0.5 + 0.5);
          pos.z += (1.0 - dist) * 0.2;

          gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
        }
      `,
      fragmentShader: `
        varying vec2 vUv;
        uniform float uTime;
        uniform vec3 uColor1;
        uniform vec3 uColor2;
        uniform vec3 uColor3;

        void main() {
          // Animated gradient
          float t = vUv.x + sin(vUv.y * 3.0 + uTime * 0.2) * 0.1;
          vec3 color = mix(uColor1, uColor2, t);
          color = mix(color, uColor3, vUv.y * 0.3);

          // Soft edges
          float alpha = 0.08;

          gl_FragColor = vec4(color, alpha);
        }
      `,
    }),
    []
  );

  useFrame(({ clock }) => {
    if (meshRef.current) {
      (meshRef.current.material as THREE.ShaderMaterial).uniforms.uTime.value =
        clock.getElapsedTime();
      (meshRef.current.material as THREE.ShaderMaterial).uniforms.uMouse.value.set(
        mouse.x,
        mouse.y
      );
    }
  });

  return (
    <mesh ref={meshRef} position={[0, 0, -2]} scale={[15, 10, 1]}>
      <planeGeometry args={[1, 1, 32, 32]} />
      <shaderMaterial
        {...shader}
        transparent
        depthWrite={false}
      />
    </mesh>
  );
}

export function GradientMeshBg({ className }: { className?: string }) {
  return (
    <div className={className} style={{ position: 'fixed', inset: 0, zIndex: -1 }}>
      <Scene bloom={false}>
        <GradientMesh />
      </Scene>
    </div>
  );
}
```

---

## Features Layer

Domain-specific components combining patterns and Three.js.

### HealthScoreHero

```tsx
// components/features/health-score/HealthScoreHero/HealthScoreHero.tsx
'use client';

import { GlassCard } from '@/components/patterns/GlassCard';
import { HealthScoreGlobe } from '@/components/three/HealthScoreGlobe';
import { TrendIndicator } from '@/components/patterns/TrendIndicator';
import { motion } from 'framer-motion';

interface HealthScoreHeroProps {
  score: number;
  previousScore?: number;
  components: Array<{
    name: string;
    score: number;
    weight: number;
  }>;
  use3D?: boolean;
}

export function HealthScoreHero({
  score,
  previousScore,
  components,
  use3D = true,
}: HealthScoreHeroProps) {
  const trend = previousScore
    ? {
        value: Math.abs(score - previousScore),
        direction: score > previousScore ? 'up' : score < previousScore ? 'down' : 'stable',
        period: 'from last month',
      }
    : undefined;

  return (
    <GlassCard className="p-8 overflow-hidden" gradient="from-primary-500 to-success-500">
      <div className="flex items-center gap-8">
        {/* 3D Globe or 2D Ring */}
        <div className="w-[300px] h-[300px]">
          {use3D ? (
            <HealthScoreGlobe
              score={score}
              components={components}
              className="w-full h-full"
            />
          ) : (
            <ScoreRing score={score} size={280} />
          )}
        </div>

        {/* Score details */}
        <div className="flex-1">
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
          >
            <h2 className="text-heading-xl text-gray-900">Insurance Health Score™</h2>
            <p className="text-body-lg text-gray-600 mt-2">
              Your portfolio's overall insurance quality
            </p>

            {trend && (
              <TrendIndicator
                value={trend.value}
                direction={trend.direction as 'up' | 'down' | 'stable'}
                period={trend.period}
                className="mt-4"
              />
            )}
          </motion.div>

          {/* Component bars */}
          <div className="mt-8 space-y-4">
            {components.map((component, i) => (
              <motion.div
                key={component.name}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + i * 0.1 }}
              >
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-medium text-gray-700">{component.name}</span>
                  <span className="text-gray-500">{component.score}%</span>
                </div>
                <GradientProgress value={component.score} />
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </GlassCard>
  );
}
```

### GapCard

```tsx
// components/features/gaps/GapCard/GapCard.tsx
'use client';

import { Card } from '@/components/primitives/Card';
import { Badge } from '@/components/primitives/Badge';
import { Button } from '@/components/primitives/Button';
import { StatusBadge } from '@/components/patterns/StatusBadge';
import { motion } from 'framer-motion';
import { AlertTriangle, CheckCircle, Eye } from 'lucide-react';

interface GapCardProps {
  gap: {
    id: string;
    type: string;
    severity: 'critical' | 'warning' | 'info';
    title: string;
    description: string;
    currentValue?: string;
    recommendedValue?: string;
    status: 'open' | 'acknowledged' | 'resolved';
  };
  onView: (id: string) => void;
  onAcknowledge: (id: string) => void;
  onResolve: (id: string) => void;
}

export function GapCard({ gap, onView, onAcknowledge, onResolve }: GapCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      layout
    >
      <Card variant="interactive" className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-4">
            {/* Severity icon */}
            <div
              className={cn(
                'p-2 rounded-lg',
                gap.severity === 'critical' && 'bg-critical-50 text-critical-500',
                gap.severity === 'warning' && 'bg-warning-50 text-warning-500',
                gap.severity === 'info' && 'bg-info-50 text-info-500'
              )}
            >
              <AlertTriangle className="h-5 w-5" />
            </div>

            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-gray-900">{gap.title}</h3>
                <StatusBadge
                  severity={gap.severity}
                  label={gap.severity}
                  pulse={gap.severity === 'critical' && gap.status === 'open'}
                />
              </div>
              <p className="text-sm text-gray-600 mt-1">{gap.description}</p>

              {/* Value comparison */}
              {gap.currentValue && gap.recommendedValue && (
                <div className="mt-3 flex items-center gap-4 text-sm">
                  <span className="text-critical-600">
                    Current: {gap.currentValue}
                  </span>
                  <span className="text-gray-400">→</span>
                  <span className="text-success-600">
                    Recommended: {gap.recommendedValue}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => onView(gap.id)}>
              <Eye className="h-4 w-4 mr-1" />
              View
            </Button>
            {gap.status === 'open' && (
              <Button variant="secondary" size="sm" onClick={() => onAcknowledge(gap.id)}>
                Acknowledge
              </Button>
            )}
            {gap.status !== 'resolved' && (
              <Button variant="success" size="sm" onClick={() => onResolve(gap.id)}>
                <CheckCircle className="h-4 w-4 mr-1" />
                Resolve
              </Button>
            )}
          </div>
        </div>
      </Card>
    </motion.div>
  );
}
```

---

## Layout Components

### AppShell

```tsx
// components/layouts/AppShell/AppShell.tsx
'use client';

import { useState } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { GradientMeshBg } from '@/components/three/GradientMeshBg';
import { cn } from '@/lib/utils';

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 3D Background */}
      <GradientMeshBg />

      {/* Sidebar */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      {/* Main content */}
      <div
        className={cn(
          'transition-all duration-300',
          sidebarCollapsed ? 'ml-[72px]' : 'ml-[280px]'
        )}
      >
        <Header />
        <main className="p-8">{children}</main>
      </div>
    </div>
  );
}
```

---

## Component Best Practices

### 1. File Structure

Each component folder contains:
```
ComponentName/
├── ComponentName.tsx      # Main component
├── ComponentName.test.tsx # Tests
├── ComponentName.stories.tsx # Storybook stories (if used)
├── types.ts              # Component-specific types
├── utils.ts              # Component-specific utilities
└── index.ts              # Re-exports
```

### 2. Prop Patterns

```tsx
// Use discriminated unions for variant props
interface CardProps {
  variant: 'default' | 'glass' | 'elevated';
  // ... other props
}

// Use children for composition
interface LayoutProps {
  children: React.ReactNode;
  sidebar?: React.ReactNode;
  footer?: React.ReactNode;
}

// Use render props for customization
interface ListProps<T> {
  items: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
}
```

### 3. Animation Patterns

```tsx
// Define reusable motion variants
export const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -10 },
};

// Use consistent timing
export const springConfig = {
  type: 'spring',
  stiffness: 300,
  damping: 30,
};

// Stagger children
export const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.08,
    },
  },
};
```

### 4. Three.js Performance

```tsx
// Lazy load 3D components
const HealthScoreGlobe = dynamic(
  () => import('@/components/three/HealthScoreGlobe'),
  { ssr: false, loading: () => <ScoreRingSkeleton /> }
);

// Use instancing for particles
// Use LOD for complex models
// Dispose of geometries and materials properly
```

---

## Next Steps

Continue to [03-page-structure.md](./03-page-structure.md) for complete route definitions and screen wireframes.
