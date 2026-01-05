import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import type { HealthGrade } from '@/types/api';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value: number): string {
  if (value >= 1_000_000_000) {
    return `$${(value / 1_000_000_000).toFixed(1)}B`;
  }
  if (value >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(1)}M`;
  }
  if (value >= 1_000) {
    return `$${(value / 1_000).toFixed(0)}K`;
  }
  return `$${value.toFixed(0)}`;
}

export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatDateShort(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
}

export function getGrade(score: number): HealthGrade {
  if (score >= 90) return 'A';
  if (score >= 80) return 'B';
  if (score >= 70) return 'C';
  if (score >= 60) return 'D';
  return 'F';
}

export function getGradeColor(grade: HealthGrade): string {
  const colors: Record<HealthGrade, string> = {
    A: 'from-emerald-400 to-emerald-600',
    B: 'from-green-400 to-green-600',
    C: 'from-yellow-400 to-yellow-600',
    D: 'from-orange-400 to-orange-600',
    F: 'from-red-400 to-red-600',
  };
  return colors[grade];
}

export function getGradeHexColor(grade: HealthGrade): string {
  const colors: Record<HealthGrade, string> = {
    A: '#10b981',
    B: '#22c55e',
    C: '#eab308',
    D: '#f97316',
    F: '#ef4444',
  };
  return colors[grade];
}

export function getScoreColor(score: number): string {
  if (score >= 90) return '#10b981';
  if (score >= 80) return '#22c55e';
  if (score >= 70) return '#eab308';
  if (score >= 60) return '#f97316';
  return '#ef4444';
}

export function getDaysUntil(dateString: string): number {
  const date = new Date(dateString);
  const now = new Date();
  const diffTime = date.getTime() - now.getTime();
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

export function getPercentChange(current: number, previous: number): number {
  if (previous === 0) return 0;
  return Math.round(((current - previous) / previous) * 100);
}
