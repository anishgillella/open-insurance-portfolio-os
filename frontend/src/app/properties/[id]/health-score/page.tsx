'use client';

import { use } from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { ArrowLeft, RefreshCw, TrendingUp, Sparkles } from 'lucide-react';
import { cn, getGrade, getGradeColor, formatCurrency } from '@/lib/utils';
import { Button, Card, Badge } from '@/components/primitives';
import { GlassCard, ScoreRing } from '@/components/patterns';
import { HealthScoreGlobe } from '@/components/three';
import { ComponentBreakdown, RecommendationList, ScoreHistory } from '@/components/features/health-score';
import { mockProperties, mockHealthComponents, mockRecommendations, mockScoreHistory } from '@/lib/mock-data';
import { staggerContainer, staggerItem } from '@/lib/motion/variants';
import { useState } from 'react';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function HealthScorePage({ params }: PageProps) {
  const { id } = use(params);
  const property = mockProperties.find((p) => p.id === id);
  const [isRecalculating, setIsRecalculating] = useState(false);
  const [use3D, setUse3D] = useState(true);

  if (!property) {
    return (
      <div className="text-center py-16">
        <TrendingUp className="h-12 w-12 text-[var(--color-text-muted)] mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">
          Property not found
        </h3>
        <Link href="/properties">
          <Button variant="secondary">Back to properties</Button>
        </Link>
      </div>
    );
  }

  const grade = getGrade(property.health_score);
  const gradeColor = getGradeColor(grade);

  // Filter recommendations for this property
  const propertyRecommendations = mockRecommendations.filter(
    (r) => !r.action_url || r.action_url.includes(property.id)
  );
  const totalPotentialPoints = propertyRecommendations.reduce((sum, r) => sum + r.potential_improvement, 0);

  const handleRecalculate = async () => {
    setIsRecalculating(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setIsRecalculating(false);
  };

  return (
    <motion.div
      variants={staggerContainer}
      initial="initial"
      animate="animate"
      className="space-y-6"
    >
      {/* Back Link */}
      <motion.div variants={staggerItem} className="flex items-center justify-between">
        <Link
          href={`/properties/${property.id}`}
          className="inline-flex items-center gap-2 text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to {property.name}
        </Link>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setUse3D(!use3D)}
          >
            {use3D ? '2D View' : '3D View'}
          </Button>
          <Button
            variant="secondary"
            size="sm"
            leftIcon={<RefreshCw className={cn('h-4 w-4', isRecalculating && 'animate-spin')} />}
            onClick={handleRecalculate}
            disabled={isRecalculating}
          >
            {isRecalculating ? 'Recalculating...' : 'Recalculate'}
          </Button>
        </div>
      </motion.div>

      {/* Hero Section with 3D Globe */}
      <motion.div variants={staggerItem}>
        <GlassCard className="p-8" gradient="from-primary-500 to-success-500" hover={false}>
          <div className="text-center mb-6">
            <h1 className="text-2xl font-bold text-[var(--color-text-primary)] mb-2">
              Insurance Health Score™
            </h1>
            <p className="text-[var(--color-text-secondary)]">
              {property.name}
            </p>
          </div>

          <div className="flex flex-col lg:flex-row items-center justify-center gap-8">
            {/* 3D Globe or 2D Ring */}
            <div className="flex justify-center">
              {use3D ? (
                <HealthScoreGlobe
                  score={property.health_score}
                  components={mockHealthComponents}
                  size={350}
                />
              ) : (
                <ScoreRing score={property.health_score} size={250} />
              )}
            </div>

            {/* Quick Stats */}
            <div className="space-y-4 text-center lg:text-left">
              <div>
                <p className="text-sm text-[var(--color-text-muted)] mb-1">Current Score</p>
                <p className="text-5xl font-bold text-[var(--color-text-primary)]">
                  {property.health_score}
                </p>
                <p className="text-lg font-semibold" style={{ color: gradeColor }}>
                  Grade {grade}
                </p>
              </div>

              <div className="flex items-center gap-2 text-[var(--color-success-500)]">
                <TrendingUp className="h-5 w-5" />
                <span className="font-medium">+5 pts from last month</span>
              </div>

              <div className="flex items-center gap-2 text-[var(--color-primary-500)]">
                <Sparkles className="h-5 w-5" />
                <span className="font-medium">+{totalPotentialPoints} pts available</span>
              </div>

              <div className="pt-2">
                <Badge variant="primary">
                  TIV: {formatCurrency(property.total_insured_value)}
                </Badge>
              </div>
            </div>
          </div>
        </GlassCard>
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Component Breakdown */}
        <motion.div variants={staggerItem}>
          <Card padding="lg">
            <ComponentBreakdown components={mockHealthComponents} />
          </Card>
        </motion.div>

        {/* Recommendations */}
        <motion.div variants={staggerItem}>
          <Card padding="lg">
            <RecommendationList recommendations={propertyRecommendations} />
          </Card>
        </motion.div>
      </div>

      {/* Score History */}
      <motion.div variants={staggerItem}>
        <Card padding="lg">
          <ScoreHistory history={mockScoreHistory} />
        </Card>
      </motion.div>

      {/* Bottom CTA */}
      <motion.div variants={staggerItem}>
        <Card padding="lg" className="bg-gradient-to-r from-[var(--color-primary-50)] to-[var(--color-success-50)] dark:from-[var(--color-primary-500)]/10 dark:to-[var(--color-success-500)]/10">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div>
              <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
                Want to improve your score?
              </h3>
              <p className="text-[var(--color-text-secondary)]">
                Address the top recommendations to gain up to +{totalPotentialPoints} points
              </p>
            </div>
            <div className="flex gap-3">
              <Link href={`/properties/${property.id}/gaps`}>
                <Button variant="secondary">View Gaps</Button>
              </Link>
              <Link href={`/chat?property=${property.id}`}>
                <Button variant="primary">Ask AI for Help</Button>
              </Link>
            </div>
          </div>
        </Card>
      </motion.div>
    </motion.div>
  );
}
