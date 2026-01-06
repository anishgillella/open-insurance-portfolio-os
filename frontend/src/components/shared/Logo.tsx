'use client';

import { cn } from '@/lib/utils';

interface LogoProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showText?: boolean;
}

const sizes = {
  sm: { icon: 32, text: 'text-lg' },
  md: { icon: 40, text: 'text-xl' },
  lg: { icon: 48, text: 'text-2xl' },
};

export function Logo({ className, size = 'md', showText = true }: LogoProps) {
  const { icon, text } = sizes[size];

  return (
    <div className={cn('flex items-center gap-2', className)}>
      {/* Logo Icon - Teal circle with diamond */}
      <svg
        width={icon}
        height={icon}
        viewBox="0 0 48 48"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Outer circle with gradient stroke */}
        <circle
          cx="24"
          cy="24"
          r="21"
          stroke="url(#logoGradient)"
          strokeWidth="3"
          fill="none"
        />
        {/* Inner diamond shape */}
        <path
          d="M24 10L32 24L24 38L16 24L24 10Z"
          fill="url(#logoGradient)"
        />
        {/* Gradient definition */}
        <defs>
          <linearGradient
            id="logoGradient"
            x1="10"
            y1="10"
            x2="38"
            y2="38"
            gradientUnits="userSpaceOnUse"
          >
            <stop stopColor="#5EEAD4" />
            <stop offset="1" stopColor="#14B8A6" />
          </linearGradient>
        </defs>
      </svg>

      {/* Text */}
      {showText && (
        <span className={cn(text, 'font-semibold text-[var(--color-text-primary)]')}>
          Open<span className="font-normal">Insurance</span>
        </span>
      )}
    </div>
  );
}

// Standalone icon version for favicon/loading states
export function LogoIcon({ size = 40, className }: { size?: number; className?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <circle
        cx="24"
        cy="24"
        r="21"
        stroke="url(#logoIconGradient)"
        strokeWidth="3"
        fill="none"
      />
      <path
        d="M24 10L32 24L24 38L16 24L24 10Z"
        fill="url(#logoIconGradient)"
      />
      <defs>
        <linearGradient
          id="logoIconGradient"
          x1="10"
          y1="10"
          x2="38"
          y2="38"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="#5EEAD4" />
          <stop offset="1" stopColor="#14B8A6" />
        </linearGradient>
      </defs>
    </svg>
  );
}
