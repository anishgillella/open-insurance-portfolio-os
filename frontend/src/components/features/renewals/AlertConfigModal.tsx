'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  Settings,
  Bell,
  Mail,
  Plus,
  Trash2,
  Save,
  AlertTriangle,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button, Badge } from '@/components/primitives';
import { modalOverlay, modalContent } from '@/lib/motion/variants';
import type { AlertConfig, AlertThreshold, Severity } from '@/types/api';

interface AlertConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  config: AlertConfig;
  propertyName: string;
  onSave: (config: AlertConfig) => void;
}

const severityOptions: { value: Severity; label: string; color: string }[] = [
  { value: 'info', label: 'Info', color: 'bg-[var(--color-info-500)]' },
  { value: 'warning', label: 'Warning', color: 'bg-[var(--color-warning-500)]' },
  { value: 'critical', label: 'Critical', color: 'bg-[var(--color-critical-500)]' },
];

export function AlertConfigModal({
  isOpen,
  onClose,
  config,
  propertyName,
  onSave,
}: AlertConfigModalProps) {
  const [editedConfig, setEditedConfig] = useState<AlertConfig>(config);
  const [newRecipient, setNewRecipient] = useState('');

  const handleToggleEnabled = () => {
    setEditedConfig((prev) => ({ ...prev, enabled: !prev.enabled }));
  };

  const handleAddThreshold = () => {
    const newThreshold: AlertThreshold = {
      days: 30,
      severity: 'warning',
      notify_email: true,
      notify_dashboard: true,
    };
    setEditedConfig((prev) => ({
      ...prev,
      thresholds: [...prev.thresholds, newThreshold].sort((a, b) => b.days - a.days),
    }));
  };

  const handleUpdateThreshold = (
    index: number,
    field: keyof AlertThreshold,
    value: number | Severity | boolean
  ) => {
    setEditedConfig((prev) => {
      const updated = [...prev.thresholds];
      updated[index] = { ...updated[index], [field]: value };
      return { ...prev, thresholds: updated.sort((a, b) => b.days - a.days) };
    });
  };

  const handleRemoveThreshold = (index: number) => {
    setEditedConfig((prev) => ({
      ...prev,
      thresholds: prev.thresholds.filter((_, i) => i !== index),
    }));
  };

  const handleAddRecipient = () => {
    if (newRecipient && !editedConfig.recipients.includes(newRecipient)) {
      setEditedConfig((prev) => ({
        ...prev,
        recipients: [...prev.recipients, newRecipient],
      }));
      setNewRecipient('');
    }
  };

  const handleRemoveRecipient = (email: string) => {
    setEditedConfig((prev) => ({
      ...prev,
      recipients: prev.recipients.filter((r) => r !== email),
    }));
  };

  const handleSave = () => {
    onSave({
      ...editedConfig,
      updated_at: new Date().toISOString().split('T')[0],
    });
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          variants={modalOverlay}
          initial="initial"
          animate="animate"
          exit="exit"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
          onClick={onClose}
        >
          <motion.div
            variants={modalContent}
            className="bg-[var(--color-surface)] rounded-2xl shadow-xl max-w-lg w-full max-h-[85vh] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-[var(--color-border-subtle)]">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-[var(--color-primary-50)] dark:bg-[var(--color-primary-500)]/20">
                  <Settings className="h-5 w-5 text-[var(--color-primary-500)]" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
                    Alert Configuration
                  </h2>
                  <p className="text-sm text-[var(--color-text-muted)]">{propertyName}</p>
                </div>
              </div>
              <Button variant="ghost" size="icon-sm" onClick={onClose}>
                <X className="h-5 w-5" />
              </Button>
            </div>

            {/* Content */}
            <div className="p-6 overflow-y-auto max-h-[60vh] space-y-6">
              {/* Enable/Disable Toggle */}
              <div className="flex items-center justify-between p-4 rounded-xl bg-[var(--color-surface-sunken)]">
                <div className="flex items-center gap-3">
                  <Bell className="h-5 w-5 text-[var(--color-text-muted)]" />
                  <div>
                    <p className="font-medium text-[var(--color-text-primary)]">
                      Enable Renewal Alerts
                    </p>
                    <p className="text-sm text-[var(--color-text-muted)]">
                      Receive notifications for policy renewals
                    </p>
                  </div>
                </div>
                <button
                  onClick={handleToggleEnabled}
                  className={cn(
                    'relative w-12 h-6 rounded-full transition-colors',
                    editedConfig.enabled
                      ? 'bg-[var(--color-primary-500)]'
                      : 'bg-[var(--color-text-muted)]'
                  )}
                >
                  <span
                    className={cn(
                      'absolute top-1 left-1 w-4 h-4 rounded-full bg-white transition-transform',
                      editedConfig.enabled && 'translate-x-6'
                    )}
                  />
                </button>
              </div>

              {/* Thresholds */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <p className="font-medium text-[var(--color-text-primary)]">
                    Alert Thresholds
                  </p>
                  <Button
                    variant="ghost"
                    size="sm"
                    leftIcon={<Plus className="h-4 w-4" />}
                    onClick={handleAddThreshold}
                  >
                    Add
                  </Button>
                </div>
                <div className="space-y-3">
                  {editedConfig.thresholds.map((threshold, idx) => (
                    <div
                      key={idx}
                      className="p-4 rounded-xl border border-[var(--color-border-subtle)] bg-[var(--color-surface)]"
                    >
                      <div className="flex items-center gap-4 mb-3">
                        {/* Days Input */}
                        <div className="flex-1">
                          <label className="text-xs text-[var(--color-text-muted)] mb-1 block">
                            Days Before Expiration
                          </label>
                          <input
                            type="number"
                            min={1}
                            max={365}
                            value={threshold.days}
                            onChange={(e) =>
                              handleUpdateThreshold(idx, 'days', parseInt(e.target.value) || 30)
                            }
                            className="w-full px-3 py-2 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-surface)] text-[var(--color-text-primary)] text-sm"
                          />
                        </div>

                        {/* Severity Select */}
                        <div className="flex-1">
                          <label className="text-xs text-[var(--color-text-muted)] mb-1 block">
                            Severity
                          </label>
                          <select
                            value={threshold.severity}
                            onChange={(e) =>
                              handleUpdateThreshold(idx, 'severity', e.target.value as Severity)
                            }
                            className="w-full px-3 py-2 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-surface)] text-[var(--color-text-primary)] text-sm"
                          >
                            {severityOptions.map((opt) => (
                              <option key={opt.value} value={opt.value}>
                                {opt.label}
                              </option>
                            ))}
                          </select>
                        </div>

                        {/* Delete Button */}
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          className="text-[var(--color-critical-500)] mt-5"
                          onClick={() => handleRemoveThreshold(idx)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>

                      {/* Notification Options */}
                      <div className="flex items-center gap-4">
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={threshold.notify_dashboard}
                            onChange={(e) =>
                              handleUpdateThreshold(idx, 'notify_dashboard', e.target.checked)
                            }
                            className="w-4 h-4 rounded border-[var(--color-border-default)] text-[var(--color-primary-500)]"
                          />
                          <span className="text-sm text-[var(--color-text-secondary)]">
                            Dashboard
                          </span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={threshold.notify_email}
                            onChange={(e) =>
                              handleUpdateThreshold(idx, 'notify_email', e.target.checked)
                            }
                            className="w-4 h-4 rounded border-[var(--color-border-default)] text-[var(--color-primary-500)]"
                          />
                          <Mail className="h-4 w-4 text-[var(--color-text-muted)]" />
                          <span className="text-sm text-[var(--color-text-secondary)]">
                            Email
                          </span>
                        </label>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Email Recipients */}
              <div>
                <p className="font-medium text-[var(--color-text-primary)] mb-3">
                  Email Recipients
                </p>
                <div className="flex gap-2 mb-3">
                  <input
                    type="email"
                    value={newRecipient}
                    onChange={(e) => setNewRecipient(e.target.value)}
                    placeholder="Enter email address"
                    className="flex-1 px-3 py-2 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-surface)] text-[var(--color-text-primary)] text-sm placeholder:text-[var(--color-text-muted)]"
                    onKeyDown={(e) => e.key === 'Enter' && handleAddRecipient()}
                  />
                  <Button variant="secondary" onClick={handleAddRecipient}>
                    Add
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {editedConfig.recipients.map((email) => (
                    <Badge
                      key={email}
                      variant="secondary"
                      className="flex items-center gap-1 pr-1"
                    >
                      {email}
                      <button
                        onClick={() => handleRemoveRecipient(email)}
                        className="p-0.5 rounded hover:bg-[var(--color-surface-sunken)]"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                  {editedConfig.recipients.length === 0 && (
                    <p className="text-sm text-[var(--color-text-muted)]">
                      No recipients added
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end gap-3 p-6 border-t border-[var(--color-border-subtle)]">
              <Button variant="ghost" onClick={onClose}>
                Cancel
              </Button>
              <Button
                variant="primary"
                leftIcon={<Save className="h-4 w-4" />}
                onClick={handleSave}
              >
                Save Configuration
              </Button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
