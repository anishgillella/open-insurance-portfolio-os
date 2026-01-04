'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { cn, getGrade, getGradeHexColor } from '@/lib/utils';

interface HealthComponent {
  name: string;
  score: number;
  weight: number;
}

interface HealthRadialChartProps {
  components: HealthComponent[];
  overallScore: number;
  size?: number;
  className?: string;
  animated?: boolean;
}

export function HealthRadialChart({
  components,
  overallScore,
  size = 300,
  className,
  animated = true,
}: HealthRadialChartProps) {
  const [isVisible, setIsVisible] = useState(!animated);
  const grade = getGrade(overallScore);
  const gradeColor = getGradeHexColor(grade);

  useEffect(() => {
    if (animated) {
      const timer = setTimeout(() => setIsVisible(true), 100);
      return () => clearTimeout(timer);
    }
  }, [animated]);

  const center = size / 2;
  const maxRadius = size / 2 - 30;
  const innerRadius = maxRadius * 0.35;
  const segmentCount = components.length;
  const anglePerSegment = (2 * Math.PI) / segmentCount;
  const gapAngle = 0.03; // Small gap between segments

  const getPointOnCircle = (angle: number, radius: number) => ({
    x: center + radius * Math.cos(angle - Math.PI / 2),
    y: center + radius * Math.sin(angle - Math.PI / 2),
  });

  const createSegmentPath = (index: number, score: number) => {
    const startAngle = index * anglePerSegment + gapAngle / 2;
    const endAngle = (index + 1) * anglePerSegment - gapAngle / 2;
    const outerRadius = innerRadius + (maxRadius - innerRadius) * (score / 100);

    const innerStart = getPointOnCircle(startAngle, innerRadius);
    const innerEnd = getPointOnCircle(endAngle, innerRadius);
    const outerStart = getPointOnCircle(startAngle, outerRadius);
    const outerEnd = getPointOnCircle(endAngle, outerRadius);

    const largeArcFlag = endAngle - startAngle > Math.PI ? 1 : 0;

    return `
      M ${innerStart.x} ${innerStart.y}
      L ${outerStart.x} ${outerStart.y}
      A ${outerRadius} ${outerRadius} 0 ${largeArcFlag} 1 ${outerEnd.x} ${outerEnd.y}
      L ${innerEnd.x} ${innerEnd.y}
      A ${innerRadius} ${innerRadius} 0 ${largeArcFlag} 0 ${innerStart.x} ${innerStart.y}
      Z
    `;
  };

  const getSegmentColor = (score: number) => {
    if (score >= 90) return '#10B981';
    if (score >= 80) return '#14B8A6';
    if (score >= 70) return '#F59E0B';
    if (score >= 60) return '#F97316';
    return '#EF4444';
  };

  const getLabelPosition = (index: number) => {
    const angle = index * anglePerSegment + anglePerSegment / 2;
    const labelRadius = maxRadius + 20;
    return getPointOnCircle(angle, labelRadius);
  };

  return (
    <div className={cn('relative', className)}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Background circles */}
        {[0.25, 0.5, 0.75, 1].map((fraction, i) => (
          <circle
            key={i}
            cx={center}
            cy={center}
            r={innerRadius + (maxRadius - innerRadius) * fraction}
            fill="none"
            stroke="var(--color-border-subtle)"
            strokeWidth={1}
            strokeDasharray="4 4"
            opacity={0.5}
          />
        ))}

        {/* Segment paths */}
        {components.map((component, index) => {
          const color = getSegmentColor(component.score);

          return (
            <motion.path
              key={component.name}
              d={createSegmentPath(index, isVisible ? component.score : 0)}
              fill={color}
              fillOpacity={0.8}
              stroke={color}
              strokeWidth={2}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{
                opacity: isVisible ? 1 : 0,
                scale: isVisible ? 1 : 0.8,
              }}
              transition={{
                duration: 0.6,
                delay: index * 0.1,
                ease: [0.22, 1, 0.36, 1],
              }}
              style={{ transformOrigin: `${center}px ${center}px` }}
            />
          );
        })}

        {/* Max radius indicator (full segment outline) */}
        {components.map((_, index) => (
          <path
            key={`outline-${index}`}
            d={createSegmentPath(index, 100)}
            fill="none"
            stroke="var(--color-border-subtle)"
            strokeWidth={1}
            opacity={0.3}
          />
        ))}

        {/* Center circle with score */}
        <motion.circle
          cx={center}
          cy={center}
          r={innerRadius - 5}
          fill="var(--color-surface)"
          stroke={gradeColor}
          strokeWidth={3}
          initial={{ scale: 0 }}
          animate={{ scale: isVisible ? 1 : 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
        />

        {/* Score text */}
        <motion.text
          x={center}
          y={center - 8}
          textAnchor="middle"
          className="text-3xl font-bold"
          fill="var(--color-text-primary)"
          initial={{ opacity: 0 }}
          animate={{ opacity: isVisible ? 1 : 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
        >
          {overallScore}
        </motion.text>
        <motion.text
          x={center}
          y={center + 15}
          textAnchor="middle"
          className="text-sm"
          fill="var(--color-text-muted)"
          initial={{ opacity: 0 }}
          animate={{ opacity: isVisible ? 1 : 0 }}
          transition={{ duration: 0.5, delay: 0.6 }}
        >
          Health Score
        </motion.text>
        <motion.text
          x={center}
          y={center + 32}
          textAnchor="middle"
          className="text-lg font-bold"
          fill={gradeColor}
          initial={{ opacity: 0 }}
          animate={{ opacity: isVisible ? 1 : 0 }}
          transition={{ duration: 0.5, delay: 0.7 }}
        >
          Grade {grade}
        </motion.text>
      </svg>

      {/* Labels outside the chart */}
      <div className="absolute inset-0 pointer-events-none">
        {components.map((component, index) => {
          const pos = getLabelPosition(index);
          const isLeft = pos.x < center;
          const isTop = pos.y < center;

          return (
            <motion.div
              key={component.name}
              className={cn(
                'absolute flex flex-col',
                isLeft ? 'items-end text-right' : 'items-start text-left'
              )}
              style={{
                left: pos.x,
                top: pos.y,
                transform: `translate(${isLeft ? '-100%' : '0'}, -50%)`,
              }}
              initial={{ opacity: 0, x: isLeft ? 10 : -10 }}
              animate={{ opacity: isVisible ? 1 : 0, x: 0 }}
              transition={{ duration: 0.4, delay: 0.8 + index * 0.05 }}
            >
              <span className="text-xs font-medium text-[var(--color-text-secondary)] whitespace-nowrap">
                {component.name}
              </span>
              <span
                className="text-sm font-bold"
                style={{ color: getSegmentColor(component.score) }}
              >
                {component.score}%
              </span>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
