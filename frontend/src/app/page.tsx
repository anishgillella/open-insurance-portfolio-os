'use client';

import { motion } from 'framer-motion';
import { useState } from 'react';
import Link from 'next/link';
import {
  Building2,
  DollarSign,
  CreditCard,
  Activity,
  AlertTriangle,
  Clock,
  CheckCircle,
  ArrowRight,
  LayoutGrid,
  BarChart3,
} from 'lucide-react';
import { DataCard, GlassCard, ScoreRing, GradientProgress, StatusBadge } from '@/components/patterns';
import { Button, Card, Badge } from '@/components/primitives';
import { PortfolioTreemap, PortfolioBubbleChart } from '@/components/features/portfolio';
import { staggerContainer, staggerItem } from '@/lib/motion/variants';
import { mockProperties, mockDashboardSummary } from '@/lib/mock-data';

// Mock data for demo
const mockDashboardData = {
  totalProperties: mockDashboardSummary.totalProperties,
  totalInsuredValue: mockDashboardSummary.totalInsuredValue,
  totalPremium: mockDashboardSummary.totalPremium,
  healthScore: mockDashboardSummary.averageHealthScore,
  expirations: [
    { id: 'prop-1', name: 'Shoaff Park Apartments', days: 15, severity: 'critical' as const },
    { id: 'prop-7', name: 'Eastwood Manor', days: 35, severity: 'warning' as const },
    { id: 'prop-2', name: 'Buffalo Run', days: 45, severity: 'warning' as const },
    { id: 'prop-3', name: 'Lake Sheri', days: 78, severity: 'info' as const },
  ],
  alerts: [
    { id: '1', type: 'gap', severity: 'critical' as const, title: 'Underinsurance Gap', description: 'Shoaff Park - $2.1M below recommended', property: 'Shoaff Park' },
    { id: '2', type: 'expiration', severity: 'warning' as const, title: 'Policy Expiring', description: 'Property policy expires in 15 days', property: 'Shoaff Park' },
    { id: '3', type: 'gap', severity: 'warning' as const, title: 'Missing Flood Coverage', description: 'Property in FEMA Zone AE', property: 'Buffalo Run' },
  ],
  healthComponents: [
    { name: 'Coverage Adequacy', score: 80, weight: 25 },
    { name: 'Policy Currency', score: 90, weight: 20 },
    { name: 'Deductible Risk', score: 67, weight: 15 },
    { name: 'Coverage Breadth', score: 80, weight: 15 },
    { name: 'Lender Compliance', score: 100, weight: 15 },
    { name: 'Documentation', score: 70, weight: 10 },
  ],
  recommendations: [
    { title: 'Reduce Shoaff Park deductible from 3% to 2%', points: 5, priority: 'high' as const },
    { title: 'Upload missing EOP for Buffalo Run', points: 3, priority: 'medium' as const },
    { title: 'Review flood coverage options', points: 2, priority: 'low' as const },
  ],
};

function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 18) return 'Good afternoon';
  return 'Good evening';
}

export default function Dashboard() {
  const [portfolioView, setPortfolioView] = useState<'treemap' | 'bubble'>('treemap');

  return (
    <motion.div
      variants={staggerContainer}
      initial="initial"
      animate="animate"
      className="space-y-8"
    >
      {/* Header */}
      <motion.div variants={staggerItem}>
        <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">
          {getGreeting()}
        </h1>
        <p className="text-[var(--color-text-secondary)] mt-1">
          Your portfolio at a glance
        </p>
      </motion.div>

      {/* Stats Grid */}
      <motion.div
        variants={staggerItem}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
      >
        <DataCard
          label="Properties"
          value={mockDashboardData.totalProperties}
          icon={<Building2 className="h-5 w-5" />}
          trend={{ value: 2, direction: 'up', period: 'new this month' }}
        />
        <DataCard
          label="Total Insured Value"
          value={mockDashboardData.totalInsuredValue}
          prefix="$"
          icon={<DollarSign className="h-5 w-5" />}
          trend={{ value: 8, direction: 'up', period: 'YoY' }}
        />
        <DataCard
          label="Annual Premium"
          value={mockDashboardData.totalPremium}
          prefix="$"
          icon={<CreditCard className="h-5 w-5" />}
          trend={{ value: 12, direction: 'up', period: 'YoY' }}
        />
        <DataCard
          label="Health Score"
          value={mockDashboardData.healthScore}
          icon={<Activity className="h-5 w-5" />}
          trend={{ value: 5, direction: 'up', period: 'from last month' }}
        />
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Expiration Timeline */}
        <motion.div variants={staggerItem}>
          <Card padding="lg">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
                Expiration Timeline
              </h2>
              <Clock className="h-5 w-5 text-[var(--color-text-muted)]" />
            </div>
            <div className="space-y-4">
              {mockDashboardData.expirations.map((expiration) => (
                <div
                  key={expiration.id}
                  className="flex items-center gap-4 p-3 rounded-lg bg-[var(--color-surface-sunken)]"
                >
                  <div
                    className={`w-3 h-3 rounded-full ${
                      expiration.severity === 'critical'
                        ? 'bg-[var(--color-critical-500)]'
                        : expiration.severity === 'warning'
                        ? 'bg-[var(--color-warning-500)]'
                        : 'bg-[var(--color-info-500)]'
                    }`}
                  />
                  <div className="flex-1">
                    <p className="font-medium text-[var(--color-text-primary)] text-sm">
                      {expiration.name}
                    </p>
                    <p className="text-xs text-[var(--color-text-muted)]">
                      {expiration.days} days
                    </p>
                  </div>
                  <StatusBadge
                    severity={expiration.severity}
                    label={`${expiration.days}d`}
                    pulse={expiration.severity === 'critical'}
                  />
                </div>
              ))}
            </div>
            <Button variant="ghost" className="w-full mt-4" rightIcon={<ArrowRight className="h-4 w-4" />}>
              View all expirations
            </Button>
          </Card>
        </motion.div>

        {/* Alerts Panel */}
        <motion.div variants={staggerItem}>
          <Card padding="lg">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
                Alerts
              </h2>
              <Badge variant="critical" dot>3 Active</Badge>
            </div>
            <div className="space-y-3">
              {mockDashboardData.alerts.map((alert) => (
                <div
                  key={alert.id}
                  className="p-3 rounded-lg border border-[var(--color-border-subtle)] hover:border-[var(--color-border-default)] transition-colors cursor-pointer"
                >
                  <div className="flex items-start gap-3">
                    <div
                      className={`p-1.5 rounded-lg ${
                        alert.severity === 'critical'
                          ? 'bg-[var(--color-critical-50)] text-[var(--color-critical-500)]'
                          : 'bg-[var(--color-warning-50)] text-[var(--color-warning-500)]'
                      }`}
                    >
                      <AlertTriangle className="h-4 w-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-[var(--color-text-primary)] text-sm">
                          {alert.title}
                        </p>
                        <StatusBadge
                          severity={alert.severity}
                          label={alert.severity}
                          pulse={alert.severity === 'critical'}
                        />
                      </div>
                      <p className="text-xs text-[var(--color-text-muted)] mt-0.5 truncate">
                        {alert.description}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <Button variant="ghost" className="w-full mt-4" rightIcon={<ArrowRight className="h-4 w-4" />}>
              View all alerts
            </Button>
          </Card>
        </motion.div>

        {/* Health Score Widget */}
        <motion.div variants={staggerItem}>
          <GlassCard className="p-6" gradient="from-primary-500 to-success-500">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
                Portfolio Health
              </h2>
              <Badge variant="primary">Score</Badge>
            </div>
            <div className="flex justify-center mb-6">
              <ScoreRing score={mockDashboardData.healthScore} size={160} />
            </div>
            <div className="space-y-3">
              {mockDashboardData.healthComponents.slice(0, 4).map((component) => (
                <div key={component.name}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-[var(--color-text-secondary)]">
                      {component.name}
                    </span>
                    <span className="font-medium text-[var(--color-text-primary)]">
                      {component.score}%
                    </span>
                  </div>
                  <GradientProgress value={component.score} size="sm" />
                </div>
              ))}
            </div>
            <Button variant="ghost" className="w-full mt-4" rightIcon={<ArrowRight className="h-4 w-4" />}>
              View full breakdown
            </Button>
          </GlassCard>
        </motion.div>
      </div>

      {/* Portfolio Visualization */}
      <motion.div variants={staggerItem}>
        <Card padding="lg">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
                Portfolio Overview
              </h2>
              <p className="text-sm text-[var(--color-text-muted)]">
                Click any property to view details
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant={portfolioView === 'treemap' ? 'primary' : 'ghost'}
                size="sm"
                leftIcon={<LayoutGrid className="h-4 w-4" />}
                onClick={() => setPortfolioView('treemap')}
              >
                Treemap
              </Button>
              <Button
                variant={portfolioView === 'bubble' ? 'primary' : 'ghost'}
                size="sm"
                leftIcon={<BarChart3 className="h-4 w-4" />}
                onClick={() => setPortfolioView('bubble')}
              >
                Bubble
              </Button>
            </div>
          </div>
          {portfolioView === 'treemap' ? (
            <PortfolioTreemap properties={mockProperties} height={350} />
          ) : (
            <PortfolioBubbleChart properties={mockProperties} height={350} />
          )}
          <div className="mt-4 flex justify-center">
            <Link href="/properties">
              <Button variant="ghost" rightIcon={<ArrowRight className="h-4 w-4" />}>
                View all properties
              </Button>
            </Link>
          </div>
        </Card>
      </motion.div>

      {/* Recommendations */}
      <motion.div variants={staggerItem}>
        <Card padding="lg">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
              Top Recommendations
            </h2>
            <CheckCircle className="h-5 w-5 text-[var(--color-success-500)]" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {mockDashboardData.recommendations.map((rec, i) => (
              <div
                key={i}
                className="p-4 rounded-xl bg-[var(--color-surface-sunken)] hover:bg-[var(--color-surface)] hover:shadow-[var(--shadow-elevation-2)] transition-all cursor-pointer"
              >
                <div className="flex items-start justify-between mb-2">
                  <Badge
                    variant={
                      rec.priority === 'high'
                        ? 'critical'
                        : rec.priority === 'medium'
                        ? 'warning'
                        : 'info'
                    }
                  >
                    {rec.priority}
                  </Badge>
                  <span className="text-sm font-semibold text-[var(--color-success-600)]">
                    +{rec.points} pts
                  </span>
                </div>
                <p className="text-sm text-[var(--color-text-primary)]">
                  {rec.title}
                </p>
              </div>
            ))}
          </div>
        </Card>
      </motion.div>
    </motion.div>
  );
}
