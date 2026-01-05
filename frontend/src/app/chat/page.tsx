'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Send,
  Loader2,
  Bot,
  User,
  FileText,
  ExternalLink,
  AlertCircle,
  Sparkles,
  Building2,
  Filter,
} from 'lucide-react';
import { Card, Button, Badge } from '@/components/primitives';
import { cn } from '@/lib/utils';
import { staggerContainer, staggerItem } from '@/lib/motion/variants';
import {
  streamChat,
  propertiesApi,
  type ChatSource,
  type Property,
} from '@/lib/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: ChatSource[];
  isStreaming?: boolean;
  error?: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [properties, setProperties] = useState<Property[]>([]);
  const [selectedPropertyId, setSelectedPropertyId] = useState<string>('');
  const [showFilters, setShowFilters] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Fetch properties for filter
  useEffect(() => {
    propertiesApi.list()
      .then((data) => {
        // Handle various API response formats
        setProperties(
          Array.isArray(data) ? data :
          (data as { properties?: Property[]; items?: Property[] })?.properties ||
          (data as { items?: Property[] })?.items || []
        );
      })
      .catch(console.error);
  }, []);

  // Scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim(),
    };

    const assistantMessage: Message = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: '',
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setInput('');
    setIsLoading(true);

    try {
      let content = '';
      let sources: ChatSource[] = [];

      await streamChat(
        userMessage.content,
        {
          onContent: (chunk) => {
            content += chunk;
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMessage.id
                  ? { ...m, content, isStreaming: true }
                  : m
              )
            );
          },
          onSources: (newSources) => {
            sources = newSources;
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMessage.id
                  ? { ...m, sources, isStreaming: true }
                  : m
              )
            );
          },
          onDone: (newConversationId) => {
            setConversationId(newConversationId);
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMessage.id
                  ? { ...m, content, sources, isStreaming: false }
                  : m
              )
            );
          },
          onError: (error) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMessage.id
                  ? { ...m, error, isStreaming: false }
                  : m
              )
            );
          },
        },
        conversationId,
        selectedPropertyId || undefined
      );
    } catch (err) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMessage.id
            ? {
                ...m,
                error: err instanceof Error ? err.message : 'Failed to get response',
                isStreaming: false,
              }
            : m
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const selectedProperty = properties.find((p) => p.id === selectedPropertyId);

  return (
    <motion.div
      variants={staggerContainer}
      initial="initial"
      animate="animate"
      className="flex flex-col h-[calc(100vh-8rem)]"
    >
      {/* Header */}
      <motion.div variants={staggerItem} className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">
            Insurance Assistant
          </h1>
          <p className="text-[var(--color-text-secondary)] mt-1">
            Ask questions about your insurance documents
          </p>
        </div>
        <Button
          variant={showFilters ? 'secondary' : 'ghost'}
          size="sm"
          onClick={() => setShowFilters(!showFilters)}
        >
          <Filter className="h-4 w-4 mr-2" />
          Filters
          {selectedPropertyId && (
            <Badge variant="primary" className="ml-2">
              1
            </Badge>
          )}
        </Button>
      </motion.div>

      {/* Filters */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-4"
          >
            <Card padding="md">
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <label className="text-sm text-[var(--color-text-muted)] mb-1 block">
                    Filter by Property
                  </label>
                  <select
                    value={selectedPropertyId}
                    onChange={(e) => setSelectedPropertyId(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-surface)] text-[var(--color-text-primary)] text-sm"
                  >
                    <option value="">All Properties</option>
                    {properties.map((property) => (
                      <option key={property.id} value={property.id}>
                        {property.name}
                      </option>
                    ))}
                  </select>
                </div>
                {selectedPropertyId && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedPropertyId('')}
                    className="mt-5"
                  >
                    Clear
                  </Button>
                )}
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Messages */}
      <motion.div
        variants={staggerItem}
        className="flex-1 overflow-y-auto rounded-xl border border-[var(--color-border-default)] bg-[var(--color-surface)]"
      >
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-8">
            <div className="p-4 rounded-full bg-[var(--color-primary-50)] dark:bg-[var(--color-primary-500)]/10 mb-4">
              <Sparkles className="h-8 w-8 text-[var(--color-primary-500)]" />
            </div>
            <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">
              How can I help you today?
            </h2>
            <p className="text-[var(--color-text-secondary)] max-w-md mb-6">
              I can answer questions about your insurance policies, coverage details,
              expiration dates, and more based on your uploaded documents.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-lg">
              {[
                'What policies are expiring soon?',
                'Show me coverage gaps',
                'What is my total insured value?',
                'Which properties have compliance issues?',
              ].map((suggestion) => (
                <Button
                  key={suggestion}
                  variant="ghost"
                  className="justify-start text-left h-auto py-3 px-4"
                  onClick={() => {
                    setInput(suggestion);
                    inputRef.current?.focus();
                  }}
                >
                  <span className="text-sm">{suggestion}</span>
                </Button>
              ))}
            </div>
          </div>
        ) : (
          <div className="p-4 space-y-4">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </motion.div>

      {/* Input */}
      <motion.div variants={staggerItem} className="mt-4">
        {selectedProperty && (
          <div className="flex items-center gap-2 mb-2 text-sm text-[var(--color-text-muted)]">
            <Building2 className="h-4 w-4" />
            <span>Filtering by: {selectedProperty.name}</span>
          </div>
        )}
        <div className="flex items-end gap-3">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your insurance documents..."
              rows={1}
              className="w-full px-4 py-3 rounded-xl border border-[var(--color-border-default)] bg-[var(--color-surface)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] resize-none focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-500)] focus:border-transparent"
              disabled={isLoading}
            />
          </div>
          <Button
            variant="primary"
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="h-12 w-12 rounded-xl"
          >
            {isLoading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </Button>
        </div>
        <p className="text-xs text-[var(--color-text-muted)] mt-2 text-center">
          Press Enter to send, Shift+Enter for new line
        </p>
      </motion.div>
    </motion.div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn('flex gap-3', isUser && 'flex-row-reverse')}
    >
      {/* Avatar */}
      <div
        className={cn(
          'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
          isUser
            ? 'bg-[var(--color-primary-500)] text-white'
            : 'bg-[var(--color-surface-sunken)] text-[var(--color-text-secondary)]'
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      {/* Content */}
      <div className={cn('flex-1 max-w-[80%]', isUser && 'text-right')}>
        <div
          className={cn(
            'inline-block rounded-2xl px-4 py-3 text-sm',
            isUser
              ? 'bg-[var(--color-primary-500)] text-white rounded-tr-md'
              : 'bg-[var(--color-surface-sunken)] text-[var(--color-text-primary)] rounded-tl-md'
          )}
        >
          {message.error ? (
            <div className="flex items-center gap-2 text-[var(--color-critical-500)]">
              <AlertCircle className="h-4 w-4" />
              <span>{message.error}</span>
            </div>
          ) : (
            <>
              <div className="whitespace-pre-wrap">{message.content}</div>
              {message.isStreaming && (
                <span className="inline-block w-2 h-4 bg-current animate-pulse ml-1" />
              )}
            </>
          )}
        </div>

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-2 space-y-1">
            <p className="text-xs text-[var(--color-text-muted)]">Sources:</p>
            <div className="flex flex-wrap gap-2">
              {message.sources.map((source, index) => (
                <SourceChip key={index} source={source} />
              ))}
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
}

function SourceChip({ source }: { source: ChatSource }) {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div className="relative">
      <button
        className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-[var(--color-surface)] border border-[var(--color-border-subtle)] text-xs text-[var(--color-text-secondary)] hover:border-[var(--color-primary-300)] transition-colors"
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        onClick={() => window.open(`/documents/${source.document_id}`, '_blank')}
      >
        <FileText className="h-3 w-3" />
        <span className="max-w-[150px] truncate">{source.document_name}</span>
        {source.page && (
          <Badge variant="secondary" className="text-[10px] px-1 py-0">
            p.{source.page}
          </Badge>
        )}
        <ExternalLink className="h-3 w-3" />
      </button>

      {/* Tooltip */}
      <AnimatePresence>
        {showTooltip && source.snippet && (
          <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 5 }}
            className="absolute bottom-full left-0 mb-2 z-50 w-72 p-3 rounded-lg bg-[var(--color-surface-raised)] border border-[var(--color-border-default)] shadow-lg"
          >
            <p className="text-xs text-[var(--color-text-muted)] mb-1">Relevant excerpt:</p>
            <p className="text-xs text-[var(--color-text-secondary)] line-clamp-4">
              "{source.snippet}"
            </p>
            <div className="flex items-center justify-between mt-2 pt-2 border-t border-[var(--color-border-subtle)]">
              <span className="text-[10px] text-[var(--color-text-muted)]">
                Relevance: {Math.round(source.score * 100)}%
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
