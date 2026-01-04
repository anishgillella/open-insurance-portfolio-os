# Design System

The Open Insurance design system creates a premium, immersive experience through rich gradients, depth, glass effects, and thoughtful animations. Every token is designed to evoke trust, clarity, and delight.

---

## Color Palette

### Primary Colors

The primary palette establishes trust and professionalism with deep ocean blues.

```typescript
// tailwind.config.ts
const colors = {
  primary: {
    50:  '#E6F4FF',  // Lightest - backgrounds
    100: '#BAE0FF',  // Light - hover states
    200: '#91CAFF',  // Soft - borders
    300: '#69B4FF',  // Medium - secondary elements
    400: '#4096FF',  // Bright - interactive elements
    500: '#1677FF',  // Base - primary actions
    600: '#0958D9',  // Dark - pressed states
    700: '#003EB3',  // Deeper - emphasis
    800: '#002C8C',  // Deep - headers
    900: '#001D66',  // Darkest - text on light
  },
};
```

### Semantic Status Colors

Status colors communicate state instantly through consistent meaning.

```typescript
const status = {
  critical: {
    50:  '#FFF1F0',  // Background
    100: '#FFCCC7',  // Light
    200: '#FFA39E',  // Soft
    300: '#FF7875',  // Medium
    400: '#FF4D4F',  // Base
    500: '#F5222D',  // Dark
    600: '#CF1322',  // Darker
    700: '#A8071A',  // Deep
    gradient: 'from-red-500 to-rose-600',
    glow: 'rgba(255, 77, 79, 0.4)',
  },

  warning: {
    50:  '#FFFBE6',
    100: '#FFF1B8',
    200: '#FFE58F',
    300: '#FFD666',
    400: '#FFC53D',
    500: '#FAAD14',  // Base
    600: '#D48806',
    700: '#AD6800',
    gradient: 'from-amber-400 to-orange-500',
    glow: 'rgba(250, 173, 20, 0.4)',
  },

  success: {
    50:  '#F6FFED',
    100: '#D9F7BE',
    200: '#B7EB8F',
    300: '#95DE64',
    400: '#73D13D',
    500: '#52C41A',  // Base
    600: '#389E0D',
    700: '#237804',
    gradient: 'from-emerald-400 to-green-600',
    glow: 'rgba(82, 196, 26, 0.4)',
  },

  info: {
    50:  '#E6F4FF',
    100: '#BAE0FF',
    200: '#91CAFF',
    300: '#69B4FF',
    400: '#4096FF',
    500: '#1677FF',  // Base
    600: '#0958D9',
    700: '#003EB3',
    gradient: 'from-blue-400 to-indigo-600',
    glow: 'rgba(22, 119, 255, 0.4)',
  },
};
```

### Health Score Grade Colors

Each grade has a distinct gradient that creates immediate visual recognition.

```typescript
const gradeColors = {
  A: {
    gradient: 'from-emerald-400 via-green-500 to-teal-600',
    solid: '#10B981',
    text: '#065F46',
    bg: '#ECFDF5',
    glow: 'rgba(16, 185, 129, 0.5)',
    label: 'Excellent',
  },
  B: {
    gradient: 'from-green-400 via-teal-500 to-cyan-600',
    solid: '#14B8A6',
    text: '#115E59',
    bg: '#F0FDFA',
    glow: 'rgba(20, 184, 166, 0.5)',
    label: 'Good',
  },
  C: {
    gradient: 'from-amber-400 via-yellow-500 to-orange-500',
    solid: '#F59E0B',
    text: '#92400E',
    bg: '#FFFBEB',
    glow: 'rgba(245, 158, 11, 0.5)',
    label: 'Fair',
  },
  D: {
    gradient: 'from-orange-400 via-orange-500 to-red-500',
    solid: '#F97316',
    text: '#9A3412',
    bg: '#FFF7ED',
    glow: 'rgba(249, 115, 22, 0.5)',
    label: 'Poor',
  },
  F: {
    gradient: 'from-red-500 via-rose-500 to-pink-600',
    solid: '#EF4444',
    text: '#991B1B',
    bg: '#FEF2F2',
    glow: 'rgba(239, 68, 68, 0.5)',
    label: 'Critical',
  },
};
```

### Surface & Background Colors

Layered surfaces create depth and visual hierarchy.

```typescript
const surface = {
  // Backgrounds
  background: {
    primary: '#F5F7FA',    // Main app background
    secondary: '#FFFFFF',  // Card backgrounds
    tertiary: '#EEF2F6',   // Sunken areas
    inverse: '#1A1A2E',    // Dark mode / overlays
  },

  // Glass effects
  glass: {
    white: 'rgba(255, 255, 255, 0.7)',
    whiteStrong: 'rgba(255, 255, 255, 0.85)',
    dark: 'rgba(0, 0, 0, 0.05)',
    darkStrong: 'rgba(0, 0, 0, 0.1)',
    blur: '20px',
    blurStrong: '40px',
  },

  // Borders
  border: {
    subtle: 'rgba(0, 0, 0, 0.06)',
    default: 'rgba(0, 0, 0, 0.1)',
    strong: 'rgba(0, 0, 0, 0.15)',
    glass: 'rgba(255, 255, 255, 0.2)',
  },
};
```

---

## Typography

### Font Stack

```typescript
const fontFamily = {
  sans: [
    'Inter var',
    'SF Pro Display',
    '-apple-system',
    'BlinkMacSystemFont',
    'Segoe UI',
    'Roboto',
    'sans-serif',
  ],
  mono: [
    'JetBrains Mono',
    'SF Mono',
    'Fira Code',
    'Consolas',
    'monospace',
  ],
};
```

### Type Scale

```typescript
const fontSize = {
  // Display - Hero numbers, scores
  'display-2xl': ['96px', { lineHeight: '1.0', letterSpacing: '-0.03em', fontWeight: '800' }],
  'display-xl':  ['72px', { lineHeight: '1.05', letterSpacing: '-0.025em', fontWeight: '700' }],
  'display-lg':  ['48px', { lineHeight: '1.1', letterSpacing: '-0.02em', fontWeight: '700' }],
  'display-md':  ['36px', { lineHeight: '1.15', letterSpacing: '-0.015em', fontWeight: '600' }],

  // Headings - Section titles
  'heading-xl': ['28px', { lineHeight: '1.25', letterSpacing: '-0.01em', fontWeight: '600' }],
  'heading-lg': ['24px', { lineHeight: '1.3', letterSpacing: '-0.005em', fontWeight: '600' }],
  'heading-md': ['20px', { lineHeight: '1.35', fontWeight: '600' }],
  'heading-sm': ['18px', { lineHeight: '1.4', fontWeight: '600' }],

  // Body - Content text
  'body-lg': ['18px', { lineHeight: '1.6', fontWeight: '400' }],
  'body-md': ['16px', { lineHeight: '1.6', fontWeight: '400' }],
  'body-sm': ['14px', { lineHeight: '1.55', fontWeight: '400' }],

  // Utility - Labels, captions
  'label-lg': ['14px', { lineHeight: '1.4', fontWeight: '500' }],
  'label-md': ['12px', { lineHeight: '1.35', fontWeight: '500' }],
  'label-sm': ['11px', { lineHeight: '1.3', fontWeight: '500', letterSpacing: '0.02em' }],

  // Caption - Helper text
  'caption': ['12px', { lineHeight: '1.4', fontWeight: '400' }],
};
```

### Usage Guidelines

| Context | Style | Example |
|---------|-------|---------|
| Health Score number | display-2xl | "82" |
| Page titles | heading-xl | "Shoaff Park Apartments" |
| Section headers | heading-lg | "Coverage Gaps" |
| Card titles | heading-md | "Property Policy" |
| Body content | body-md | Policy descriptions |
| Data labels | label-md | "Total Insured Value" |
| Helper text | caption | "Last updated 2 hours ago" |
| Money/Numbers | mono, display-* | "$35,900,000" |

---

## Spacing System

Based on an 8px grid for consistency and rhythm.

```typescript
const spacing = {
  0:    '0px',
  0.5:  '2px',
  1:    '4px',
  1.5:  '6px',
  2:    '8px',     // Base unit
  2.5:  '10px',
  3:    '12px',
  3.5:  '14px',
  4:    '16px',    // Common padding
  5:    '20px',
  6:    '24px',    // Section spacing
  7:    '28px',
  8:    '32px',    // Large gaps
  9:    '36px',
  10:   '40px',
  11:   '44px',
  12:   '48px',    // Section margins
  14:   '56px',
  16:   '64px',
  20:   '80px',
  24:   '96px',    // Page padding
  28:   '112px',
  32:   '128px',
};

// Layout-specific
const layout = {
  containerMax: '1440px',
  containerPadding: '24px',
  sidebarWidth: '280px',
  sidebarCollapsed: '72px',
  headerHeight: '72px',
  pageGutter: '32px',
};
```

---

## Border Radius

Generous radii for a friendly, modern feel.

```typescript
const borderRadius = {
  none: '0',
  sm:   '6px',     // Small elements (badges)
  md:   '8px',     // Buttons, inputs
  lg:   '12px',    // Cards
  xl:   '16px',    // Large cards
  '2xl': '20px',   // Modals
  '3xl': '24px',   // Hero elements
  full: '9999px', // Pills, avatars
};
```

---

## Shadows & Elevation

Multi-layered shadows create realistic depth.

```typescript
const boxShadow = {
  // Elevation levels
  'elevation-1': `
    0 1px 2px rgba(0, 0, 0, 0.03),
    0 1px 3px rgba(0, 0, 0, 0.05)
  `,
  'elevation-2': `
    0 2px 4px rgba(0, 0, 0, 0.03),
    0 4px 8px rgba(0, 0, 0, 0.06)
  `,
  'elevation-3': `
    0 4px 8px rgba(0, 0, 0, 0.04),
    0 8px 16px rgba(0, 0, 0, 0.08)
  `,
  'elevation-4': `
    0 8px 16px rgba(0, 0, 0, 0.06),
    0 16px 32px rgba(0, 0, 0, 0.1)
  `,

  // Glass effect
  'glass': `
    inset 0 1px 0 0 rgba(255, 255, 255, 0.5),
    0 4px 16px rgba(0, 0, 0, 0.08),
    0 8px 32px rgba(0, 0, 0, 0.12)
  `,
  'glass-hover': `
    inset 0 1px 0 0 rgba(255, 255, 255, 0.6),
    0 8px 24px rgba(0, 0, 0, 0.1),
    0 12px 40px rgba(0, 0, 0, 0.15)
  `,

  // Colored glows
  'glow-primary': '0 0 24px rgba(22, 119, 255, 0.35)',
  'glow-success': '0 0 24px rgba(82, 196, 26, 0.35)',
  'glow-warning': '0 0 24px rgba(250, 173, 20, 0.35)',
  'glow-critical': '0 0 24px rgba(255, 77, 79, 0.35)',

  // Score ring glow
  'score-glow': '0 0 40px var(--score-color)',

  // Inner shadows
  'inner-sm': 'inset 0 1px 2px rgba(0, 0, 0, 0.06)',
  'inner-md': 'inset 0 2px 4px rgba(0, 0, 0, 0.08)',
};
```

---

## Glass Effects (Glassmorphism)

```css
/* Base glass card */
.glass-card {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow:
    inset 0 1px 0 0 rgba(255, 255, 255, 0.5),
    0 4px 16px rgba(0, 0, 0, 0.08);
}

/* Frosted glass - stronger blur */
.glass-frosted {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(40px);
  -webkit-backdrop-filter: blur(40px);
}

/* Dark glass - for overlays */
.glass-dark {
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

/* Glass with gradient tint */
.glass-gradient {
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.8) 0%,
    rgba(255, 255, 255, 0.6) 100%
  );
  backdrop-filter: blur(20px);
}
```

---

## Gradients

### Background Gradients

```css
/* Ambient mesh gradient for backgrounds */
.bg-mesh {
  background:
    radial-gradient(at 40% 20%, rgba(22, 119, 255, 0.08) 0px, transparent 50%),
    radial-gradient(at 80% 0%, rgba(16, 185, 129, 0.06) 0px, transparent 50%),
    radial-gradient(at 0% 50%, rgba(250, 173, 20, 0.05) 0px, transparent 50%),
    radial-gradient(at 80% 50%, rgba(239, 68, 68, 0.04) 0px, transparent 50%),
    radial-gradient(at 0% 100%, rgba(22, 119, 255, 0.06) 0px, transparent 50%),
    linear-gradient(180deg, #F5F7FA 0%, #FFFFFF 100%);
}

/* Subtle page gradient */
.bg-subtle {
  background: linear-gradient(180deg, #F8FAFC 0%, #F1F5F9 100%);
}
```

### Interactive Gradients

```css
/* Button gradient */
.btn-gradient {
  background: linear-gradient(135deg, #1677FF 0%, #0958D9 100%);
}

.btn-gradient:hover {
  background: linear-gradient(135deg, #4096FF 0%, #1677FF 100%);
}

/* Success gradient */
.gradient-success {
  background: linear-gradient(135deg, #52C41A 0%, #389E0D 100%);
}

/* Warning gradient */
.gradient-warning {
  background: linear-gradient(135deg, #FAAD14 0%, #D48806 100%);
}

/* Critical gradient */
.gradient-critical {
  background: linear-gradient(135deg, #FF4D4F 0%, #CF1322 100%);
}
```

### Score Ring Gradients

```css
/* Animated gradient for score rings */
.score-ring-a {
  background: conic-gradient(from 0deg, #10B981, #14B8A6, #10B981);
}

.score-ring-b {
  background: conic-gradient(from 0deg, #14B8A6, #06B6D4, #14B8A6);
}

.score-ring-c {
  background: conic-gradient(from 0deg, #F59E0B, #FBBF24, #F59E0B);
}

.score-ring-d {
  background: conic-gradient(from 0deg, #F97316, #FB923C, #F97316);
}

.score-ring-f {
  background: conic-gradient(from 0deg, #EF4444, #F87171, #EF4444);
}
```

---

## Animation Tokens

### Timing Functions

```typescript
const transitionTimingFunction = {
  'ease-out-expo': 'cubic-bezier(0.16, 1, 0.3, 1)',      // Quick start, smooth end
  'ease-out-back': 'cubic-bezier(0.34, 1.56, 0.64, 1)',  // Slight overshoot
  'ease-in-out-expo': 'cubic-bezier(0.87, 0, 0.13, 1)',  // Smooth both ends
  'spring': 'cubic-bezier(0.22, 1, 0.36, 1)',            // Natural spring
  'bounce': 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',    // Playful bounce
};
```

### Duration Scale

```typescript
const transitionDuration = {
  instant: '50ms',    // Immediate feedback
  fast:    '150ms',   // Hover states
  normal:  '250ms',   // Standard transitions
  slow:    '350ms',   // Page transitions
  slower:  '500ms',   // Complex animations
  slowest: '700ms',   // Hero animations
};
```

### Common Transitions

```css
/* Hover lift effect */
.hover-lift {
  transition: transform 250ms cubic-bezier(0.22, 1, 0.36, 1),
              box-shadow 250ms cubic-bezier(0.22, 1, 0.36, 1);
}

.hover-lift:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.12);
}

/* Scale on press */
.press-scale {
  transition: transform 150ms cubic-bezier(0.22, 1, 0.36, 1);
}

.press-scale:active {
  transform: scale(0.97);
}

/* Fade in up */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in-up {
  animation: fadeInUp 500ms cubic-bezier(0.22, 1, 0.36, 1) forwards;
}
```

---

## Component Tokens

### Buttons

```typescript
const button = {
  // Sizes
  height: {
    sm: '32px',
    md: '40px',
    lg: '48px',
    xl: '56px',
  },
  padding: {
    sm: '0 12px',
    md: '0 16px',
    lg: '0 24px',
    xl: '0 32px',
  },
  fontSize: {
    sm: '13px',
    md: '14px',
    lg: '16px',
    xl: '18px',
  },
  borderRadius: '8px',

  // States
  primary: {
    bg: 'linear-gradient(135deg, #1677FF 0%, #0958D9 100%)',
    bgHover: 'linear-gradient(135deg, #4096FF 0%, #1677FF 100%)',
    text: '#FFFFFF',
    shadow: '0 2px 8px rgba(22, 119, 255, 0.35)',
  },
  secondary: {
    bg: '#FFFFFF',
    bgHover: '#F5F7FA',
    text: '#1A1A2E',
    border: 'rgba(0, 0, 0, 0.1)',
  },
  ghost: {
    bg: 'transparent',
    bgHover: 'rgba(0, 0, 0, 0.04)',
    text: '#4B5563',
  },
  danger: {
    bg: 'linear-gradient(135deg, #FF4D4F 0%, #CF1322 100%)',
    bgHover: 'linear-gradient(135deg, #FF7875 0%, #FF4D4F 100%)',
    text: '#FFFFFF',
    shadow: '0 2px 8px rgba(255, 77, 79, 0.35)',
  },
};
```

### Cards

```typescript
const card = {
  padding: {
    sm: '16px',
    md: '24px',
    lg: '32px',
  },
  borderRadius: '16px',
  border: '1px solid rgba(0, 0, 0, 0.06)',
  shadow: 'elevation-2',

  variants: {
    default: {
      bg: '#FFFFFF',
    },
    glass: {
      bg: 'rgba(255, 255, 255, 0.7)',
      backdropBlur: '20px',
      border: '1px solid rgba(255, 255, 255, 0.2)',
    },
    elevated: {
      bg: '#FFFFFF',
      shadow: 'elevation-3',
    },
    interactive: {
      bg: '#FFFFFF',
      hoverShadow: 'elevation-4',
      hoverTransform: 'translateY(-4px)',
    },
  },
};
```

### Inputs

```typescript
const input = {
  height: {
    sm: '36px',
    md: '44px',
    lg: '52px',
  },
  padding: '12px 16px',
  borderRadius: '10px',
  border: '1px solid rgba(0, 0, 0, 0.1)',
  borderFocus: '2px solid #1677FF',
  bg: '#FFFFFF',
  bgDisabled: '#F5F7FA',
  placeholder: '#9CA3AF',
  shadow: 'inset 0 1px 2px rgba(0, 0, 0, 0.04)',
  shadowFocus: '0 0 0 4px rgba(22, 119, 255, 0.12)',
};
```

### Badges

```typescript
const badge = {
  padding: '4px 10px',
  borderRadius: '6px',
  fontSize: '12px',
  fontWeight: '500',

  variants: {
    critical: { bg: '#FFF1F0', text: '#CF1322', border: '#FFCCC7' },
    warning:  { bg: '#FFFBE6', text: '#D48806', border: '#FFF1B8' },
    success:  { bg: '#F6FFED', text: '#389E0D', border: '#D9F7BE' },
    info:     { bg: '#E6F4FF', text: '#0958D9', border: '#BAE0FF' },
    neutral:  { bg: '#F5F7FA', text: '#4B5563', border: '#E5E7EB' },
  },
};
```

---

## Tailwind Configuration

Complete Tailwind config extending the design system:

```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: { /* ... primary palette */ },
        critical: { /* ... critical palette */ },
        warning: { /* ... warning palette */ },
        success: { /* ... success palette */ },
        surface: { /* ... surface colors */ },
      },
      fontFamily: {
        sans: ['Inter var', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      fontSize: { /* ... type scale */ },
      spacing: { /* ... spacing scale */ },
      borderRadius: { /* ... radius scale */ },
      boxShadow: { /* ... shadow scale */ },
      transitionTimingFunction: { /* ... easing functions */ },
      transitionDuration: { /* ... duration scale */ },
      animation: {
        'fade-in': 'fadeIn 300ms ease-out',
        'fade-in-up': 'fadeInUp 500ms cubic-bezier(0.22, 1, 0.36, 1)',
        'scale-in': 'scaleIn 200ms cubic-bezier(0.22, 1, 0.36, 1)',
        'slide-in-right': 'slideInRight 300ms cubic-bezier(0.22, 1, 0.36, 1)',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        pulseGlow: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.6' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
    require('@tailwindcss/forms'),
  ],
};

export default config;
```

---

## CSS Variables

Global CSS variables for runtime theming:

```css
/* globals.css */
:root {
  /* Colors */
  --color-primary: 22, 119, 255;
  --color-critical: 255, 77, 79;
  --color-warning: 250, 173, 20;
  --color-success: 82, 196, 26;

  /* Surfaces */
  --surface-background: 245, 247, 250;
  --surface-card: 255, 255, 255;
  --surface-glass: 255, 255, 255, 0.7;

  /* Typography */
  --font-sans: 'Inter var', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;

  /* Spacing */
  --page-padding: 32px;
  --card-padding: 24px;
  --sidebar-width: 280px;
  --header-height: 72px;

  /* Animations */
  --transition-fast: 150ms;
  --transition-normal: 250ms;
  --easing-spring: cubic-bezier(0.22, 1, 0.36, 1);

  /* 3D Scene */
  --three-ambient-intensity: 0.4;
  --three-point-intensity: 0.8;
}

/* Reduced motion preference */
@media (prefers-reduced-motion: reduce) {
  :root {
    --transition-fast: 0ms;
    --transition-normal: 0ms;
  }

  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Next Steps

Continue to [02-component-architecture.md](./02-component-architecture.md) for the complete component hierarchy and patterns.
