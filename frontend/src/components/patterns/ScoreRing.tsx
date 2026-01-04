'use client';

import { cn, getGrade, getGradeColor } from '@/lib/utils';
import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

interface ScoreRingProps {
  score: number;
  size?: number;
  strokeWidth?: number;
  showLabel?: boolean;
  showGrade?: boolean;
  animated?: boolean;
  className?: string;
}

const gradeLabels = {
  A: 'Excellent',
  B: 'Good',
  C: 'Fair',
  D: 'Poor',
  F: 'Critical',
};

export function ScoreRing({
  score,
  size = 200,
  strokeWidth = 12,
  showLabel = true,
  showGrade = true,
  animated = true,
  className,
}: ScoreRingProps) {
  const [isVisible, setIsVisible] = useState(!animated);
  const grade = getGrade(score);
  const color = getGradeColor(grade);

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
    <div
      className={cn('relative inline-flex', className)}
      style={{ width: size, height: size }}
    >
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
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          initial={{
            strokeDasharray: circumference,
            strokeDashoffset: circumference,
          }}
          animate={
            isVisible
              ? { strokeDashoffset: circumference - progress }
              : undefined
          }
          transition={{ duration: 1.5, ease: [0.22, 1, 0.36, 1] }}
          style={{
            filter: `drop-shadow(0 0 8px ${color})`,
          }}
        />
      </svg>

      {/* Center content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <motion.span
          className="text-5xl font-bold text-[var(--color-text-primary)] font-mono"
          initial={{ opacity: 0, scale: 0.5 }}
          animate={isVisible ? { opacity: 1, scale: 1 } : undefined}
          transition={{ delay: 0.3, duration: 0.5, ease: 'backOut' }}
        >
          {score}
        </motion.span>
        {showGrade && (
          <motion.span
            className="text-lg font-semibold"
            style={{ color }}
            initial={{ opacity: 0 }}
            animate={isVisible ? { opacity: 1 } : undefined}
            transition={{ delay: 0.6, duration: 0.3 }}
          >
            Grade {grade}
          </motion.span>
        )}
        {showLabel && (
          <motion.span
            className="text-sm text-[var(--color-text-muted)] mt-1"
            initial={{ opacity: 0 }}
            animate={isVisible ? { opacity: 1 } : undefined}
            transition={{ delay: 0.7, duration: 0.3 }}
          >
            {gradeLabels[grade]}
          </motion.span>
        )}
      </div>
    </div>
  );
}
