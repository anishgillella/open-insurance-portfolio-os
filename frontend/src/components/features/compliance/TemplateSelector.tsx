'use client';

import { motion } from 'framer-motion';
import {
  Shield,
  Building2,
  Lock,
  ChevronRight,
  Check,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatCurrency } from '@/lib/utils';
import { Badge, Card } from '@/components/primitives';
import { staggerContainer, staggerItem } from '@/lib/motion/variants';

interface ComplianceTemplate {
  name: string;
  display_name: string;
  description: string;
  requirements: {
    min_property_coverage_pct: number;
    min_gl_limit: number;
    min_umbrella_limit?: number;
    min_umbrella_by_units?: Array<{ min_units: number; max_units: number; limit: number }>;
    max_deductible_pct: number;
    max_deductible_flat?: number | null;
    requires_flood: boolean;
    requires_earthquake: boolean;
    requires_terrorism: boolean;
  };
}

interface TemplateSelectorProps {
  templates: ComplianceTemplate[];
  selectedTemplate: string | null;
  onSelectTemplate: (templateName: string) => void;
  showDetails?: boolean;
}

const templateIcons: Record<string, typeof Shield> = {
  standard: Shield,
  fannie_mae: Building2,
  conservative: Lock,
};

const templateColors: Record<string, { bg: string; text: string; border: string }> = {
  standard: {
    bg: 'bg-[var(--color-primary-50)]',
    text: 'text-[var(--color-primary-600)]',
    border: 'border-[var(--color-primary-200)]',
  },
  fannie_mae: {
    bg: 'bg-[var(--color-info-50)]',
    text: 'text-[var(--color-info-600)]',
    border: 'border-[var(--color-info-200)]',
  },
  conservative: {
    bg: 'bg-[var(--color-warning-50)]',
    text: 'text-[var(--color-warning-600)]',
    border: 'border-[var(--color-warning-200)]',
  },
};

function TemplateCard({
  template,
  isSelected,
  onClick,
  showDetails,
}: {
  template: ComplianceTemplate;
  isSelected: boolean;
  onClick: () => void;
  showDetails: boolean;
}) {
  const Icon = templateIcons[template.name] || Shield;
  const colors = templateColors[template.name] || templateColors.standard;

  return (
    <motion.div
      variants={staggerItem}
      className={cn(
        'relative p-4 rounded-xl cursor-pointer transition-all',
        'border-2',
        isSelected
          ? 'border-[var(--color-primary-500)] shadow-[var(--shadow-elevation-2)]'
          : 'border-[var(--color-border-subtle)] hover:border-[var(--color-border-default)]',
        'bg-[var(--color-surface)]'
      )}
      onClick={onClick}
      whileHover={{ y: -2 }}
      whileTap={{ scale: 0.99 }}
    >
      {/* Selection indicator */}
      {isSelected && (
        <div className="absolute top-3 right-3 w-6 h-6 rounded-full bg-[var(--color-primary-500)] flex items-center justify-center">
          <Check className="h-4 w-4 text-white" />
        </div>
      )}

      {/* Header */}
      <div className="flex items-start gap-3 mb-3">
        <div className={cn('p-2 rounded-lg', colors.bg)}>
          <Icon className={cn('h-5 w-5', colors.text)} />
        </div>
        <div>
          <h3 className="font-semibold text-[var(--color-text-primary)]">
            {template.display_name}
          </h3>
          <p className="text-sm text-[var(--color-text-muted)]">
            {template.description}
          </p>
        </div>
      </div>

      {showDetails && (
        <div className="space-y-3 pt-3 border-t border-[var(--color-border-subtle)]">
          {/* Requirements Grid */}
          <div className="grid grid-cols-2 gap-2">
            <div className="p-2 rounded-lg bg-[var(--color-surface-sunken)]">
              <p className="text-xs text-[var(--color-text-muted)]">Property Coverage</p>
              <p className="text-sm font-medium text-[var(--color-text-primary)]">
                {template.requirements.min_property_coverage_pct}%
              </p>
            </div>
            <div className="p-2 rounded-lg bg-[var(--color-surface-sunken)]">
              <p className="text-xs text-[var(--color-text-muted)]">GL Limit</p>
              <p className="text-sm font-medium text-[var(--color-text-primary)]">
                {formatCurrency(template.requirements.min_gl_limit)}
              </p>
            </div>
            <div className="p-2 rounded-lg bg-[var(--color-surface-sunken)]">
              <p className="text-xs text-[var(--color-text-muted)]">
                {template.requirements.min_umbrella_by_units ? 'Umbrella (by units)' : 'Umbrella'}
              </p>
              <p className="text-sm font-medium text-[var(--color-text-primary)]">
                {template.requirements.min_umbrella_by_units
                  ? 'Variable'
                  : formatCurrency(template.requirements.min_umbrella_limit || 0)}
              </p>
            </div>
            <div className="p-2 rounded-lg bg-[var(--color-surface-sunken)]">
              <p className="text-xs text-[var(--color-text-muted)]">Max Deductible</p>
              <p className="text-sm font-medium text-[var(--color-text-primary)]">
                {template.requirements.max_deductible_pct}%
              </p>
            </div>
          </div>

          {/* Special Coverage Requirements */}
          <div className="flex flex-wrap gap-2">
            {template.requirements.requires_flood && (
              <Badge variant="info" size="sm">Flood Required</Badge>
            )}
            {template.requirements.requires_earthquake && (
              <Badge variant="warning" size="sm">Earthquake Required</Badge>
            )}
            {template.requirements.requires_terrorism && (
              <Badge variant="secondary" size="sm">Terrorism Required</Badge>
            )}
          </div>
        </div>
      )}
    </motion.div>
  );
}

export function TemplateSelector({
  templates,
  selectedTemplate,
  onSelectTemplate,
  showDetails = true,
}: TemplateSelectorProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
            Compliance Templates
          </h3>
          <p className="text-sm text-[var(--color-text-muted)]">
            Select a template to check compliance requirements
          </p>
        </div>
      </div>

      <motion.div
        variants={staggerContainer}
        initial="initial"
        animate="animate"
        className="grid grid-cols-1 md:grid-cols-3 gap-4"
      >
        {templates.map((template) => (
          <TemplateCard
            key={template.name}
            template={template}
            isSelected={selectedTemplate === template.name}
            onClick={() => onSelectTemplate(template.name)}
            showDetails={showDetails}
          />
        ))}
      </motion.div>
    </div>
  );
}
