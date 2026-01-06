'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import Link from 'next/link';
import {
  MessageCircle,
  X,
  Send,
  Loader2,
  Bot,
  User,
  FileText,
  ExternalLink,
  AlertCircle,
  Maximize2,
  Minimize2,
} from 'lucide-react';
import { Button, Badge } from '@/components/primitives';
import { cn } from '@/lib/utils';
import { streamChat, type ChatSource } from '@/lib/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: ChatSource[];
  isStreaming?: boolean;
  error?: string;
}

export function ChatWidget() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Extract property ID from URL if on a property page
  const propertyIdMatch = pathname.match(/\/properties\/([^/]+)/);
  const currentPropertyId = propertyIdMatch ? propertyIdMatch[1] : undefined;

  // Don't show widget on the chat page itself
  if (pathname === '/chat') {
    return null;
  }

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

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
        currentPropertyId
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

  return (
    <>
      {/* Floating Button */}
      <AnimatePresence>
        {!isOpen && (
          <motion.button
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setIsOpen(true)}
            className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-[var(--color-primary-500)] text-white shadow-lg hover:bg-[var(--color-primary-600)] transition-colors flex items-center justify-center"
          >
            <MessageCircle className="h-6 w-6" />
            {messages.length > 0 && (
              <span className="absolute -top-1 -right-1 w-5 h-5 bg-[var(--color-critical-500)] rounded-full text-xs flex items-center justify-center">
                {messages.filter((m) => m.role === 'assistant').length}
              </span>
            )}
          </motion.button>
        )}
      </AnimatePresence>

      {/* Chat Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="fixed bottom-6 right-6 z-50 w-[400px] h-[600px] max-h-[80vh] bg-[var(--color-surface)] rounded-2xl shadow-2xl border border-[var(--color-border-default)] flex flex-col overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--color-border-subtle)] bg-[var(--color-surface-raised)]">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-[var(--color-primary-50)] dark:bg-[var(--color-primary-500)]/20 flex items-center justify-center">
                  <Bot className="h-4 w-4 text-[var(--color-primary-500)]" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm text-[var(--color-text-primary)]">
                    Insurance Assistant
                  </h3>
                  {currentPropertyId && (
                    <p className="text-xs text-[var(--color-text-muted)]">
                      Focused on current property
                    </p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-1">
                <Link href="/chat">
                  <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                    <Maximize2 className="h-4 w-4" />
                  </Button>
                </Link>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0"
                  onClick={() => setIsOpen(false)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <div className="p-3 rounded-full bg-[var(--color-primary-50)] dark:bg-[var(--color-primary-500)]/10 mb-3">
                    <MessageCircle className="h-6 w-6 text-[var(--color-primary-500)]" />
                  </div>
                  <p className="text-sm font-medium text-[var(--color-text-primary)] mb-1">
                    How can I help?
                  </p>
                  <p className="text-xs text-[var(--color-text-muted)] max-w-[250px]">
                    Ask questions about your insurance documents and policies.
                  </p>
                  <div className="mt-4 space-y-2">
                    {[
                      'What policies expire soon?',
                      'Show coverage gaps',
                      'Total insured value?',
                    ].map((suggestion) => (
                      <button
                        key={suggestion}
                        onClick={() => setInput(suggestion)}
                        className="block w-full text-xs px-3 py-2 rounded-lg bg-[var(--color-surface-sunken)] hover:bg-[var(--color-surface)] border border-[var(--color-border-subtle)] text-[var(--color-text-secondary)] transition-colors"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                messages.map((message) => (
                  <WidgetMessage key={message.id} message={message} />
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-3 border-t border-[var(--color-border-subtle)] bg-[var(--color-surface-raised)]">
              <div className="flex items-end gap-2">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask a question..."
                  rows={1}
                  className="flex-1 px-3 py-2 text-sm rounded-lg border border-[var(--color-border-default)] bg-[var(--color-surface)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] resize-none focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-500)] focus:border-transparent max-h-[100px]"
                  disabled={isLoading}
                />
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleSend}
                  disabled={!input.trim() || isLoading}
                  className="h-9 w-9 p-0 rounded-lg"
                >
                  {isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

function WidgetMessage({ message }: { message: Message }) {
  const isUser = message.role === 'user';

  return (
    <div className={cn('flex gap-2', isUser && 'flex-row-reverse')}>
      <div
        className={cn(
          'flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center',
          isUser
            ? 'bg-[var(--color-primary-500)] text-white'
            : 'bg-[var(--color-surface-sunken)] text-[var(--color-text-secondary)]'
        )}
      >
        {isUser ? <User className="h-3 w-3" /> : <Bot className="h-3 w-3" />}
      </div>

      <div className={cn('flex-1 max-w-[85%]', isUser && 'text-right')}>
        <div
          className={cn(
            'inline-block rounded-xl px-3 py-2 text-xs',
            isUser
              ? 'bg-[var(--color-primary-500)] text-white rounded-tr-sm'
              : 'bg-[var(--color-surface-sunken)] text-[var(--color-text-primary)] rounded-tl-sm'
          )}
        >
          {message.error ? (
            <div className="flex items-center gap-1 text-[var(--color-critical-500)]">
              <AlertCircle className="h-3 w-3" />
              <span>{message.error}</span>
            </div>
          ) : (
            <>
              {isUser ? (
                <div className="whitespace-pre-wrap">{message.content}</div>
              ) : (
                <div className="prose prose-xs dark:prose-invert max-w-none prose-p:my-0.5 prose-ul:my-0.5 prose-li:my-0 prose-headings:my-1 prose-strong:text-[var(--color-text-primary)]">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
              )}
              {message.isStreaming && (
                <span className="inline-block w-1.5 h-3 bg-current animate-pulse ml-0.5" />
              )}
            </>
          )}
        </div>

        {/* Compact Sources */}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-1 flex flex-wrap gap-1">
            {message.sources.slice(0, 3).map((source, index) => (
              <span
                key={index}
                className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-[var(--color-surface-sunken)] text-[10px] text-[var(--color-text-muted)]"
              >
                <FileText className="h-2.5 w-2.5" />
                <span className="max-w-[80px] truncate">{source.document_name}</span>
              </span>
            ))}
            {message.sources.length > 3 && (
              <span className="text-[10px] text-[var(--color-text-muted)]">
                +{message.sources.length - 3} more
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
