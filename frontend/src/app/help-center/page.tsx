'use client';

import { useState } from 'react';
import { Upload, Clock, Eye, Play, BookOpen, Headphones, User } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/primitives';

type ContentType = 'article' | 'course' | 'podcast';

interface HelpContent {
  id: string;
  type: ContentType;
  title: string;
  description: string;
  author: string;
  authorAvatar?: string;
  duration?: string;
  views?: number;
  images: string[];
}

const helpContent: HelpContent[] = [
  // Articles
  {
    id: '1',
    type: 'article',
    title: 'Insurance for Dummies',
    description: 'Learn about the ins and outs of property insurance',
    author: 'Daniel Taylor',
    duration: '5 min',
    images: [
      'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=400&h=300&fit=crop',
      'https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=400&h=300&fit=crop',
    ],
  },
  {
    id: '2',
    type: 'article',
    title: 'Understanding Policy Coverage',
    description: 'A comprehensive guide to understanding what your policy covers',
    author: 'Sarah Chen',
    duration: '8 min',
    images: [
      'https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=400&h=300&fit=crop',
    ],
  },
  {
    id: '3',
    type: 'article',
    title: 'Claims Process Explained',
    description: 'Step-by-step guide to filing and tracking insurance claims',
    author: 'Michael Torres',
    duration: '6 min',
    images: [
      'https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=400&h=300&fit=crop',
      'https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=400&h=300&fit=crop',
    ],
  },
  // Courses
  {
    id: '4',
    type: 'course',
    title: 'Intro to Insurance',
    description: 'Learn the ins and outs of property insurance',
    author: 'Daniel Taylor',
    views: 30500,
    images: [
      'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=400&h=300&fit=crop',
    ],
  },
  {
    id: '5',
    type: 'course',
    title: 'Risk Assessment Masterclass',
    description: 'Master the art of evaluating and mitigating property risks',
    author: 'Lisa Wang',
    views: 18200,
    images: [
      'https://images.unsplash.com/photo-1552664730-d307ca884978?w=400&h=300&fit=crop',
    ],
  },
  {
    id: '6',
    type: 'course',
    title: 'Commercial Insurance 101',
    description: 'Everything you need to know about commercial property coverage',
    author: 'James Mitchell',
    views: 24800,
    images: [
      'https://images.unsplash.com/photo-1542744173-8e7e53415bb0?w=400&h=300&fit=crop',
    ],
  },
  // Podcasts
  {
    id: '7',
    type: 'podcast',
    title: 'Insurance Simplified',
    description: 'Learn about the ins and outs of property insurance',
    author: 'Daniel Taylor',
    duration: '60 min',
    images: [
      'https://images.unsplash.com/photo-1497366216548-37526070297c?w=400&h=300&fit=crop',
      'https://images.unsplash.com/photo-1497366811353-6870744d04b2?w=400&h=300&fit=crop',
    ],
  },
  {
    id: '8',
    type: 'podcast',
    title: 'The Coverage Corner',
    description: 'Weekly discussions on insurance trends and best practices',
    author: 'Emily Rodriguez',
    duration: '45 min',
    images: [
      'https://images.unsplash.com/photo-1589903308904-1010c2294adc?w=400&h=300&fit=crop',
    ],
  },
  {
    id: '9',
    type: 'podcast',
    title: 'Property Risk Talks',
    description: 'Expert interviews on managing property portfolio risks',
    author: 'David Kim',
    duration: '55 min',
    images: [
      'https://images.unsplash.com/photo-1478737270239-2f02b77fc618?w=400&h=300&fit=crop',
      'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=400&h=300&fit=crop',
    ],
  },
];

const typeConfig: Record<ContentType, { label: string; color: string; bgColor: string; icon: typeof BookOpen }> = {
  article: {
    label: 'Article',
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
    icon: BookOpen,
  },
  course: {
    label: 'Course',
    color: 'text-purple-600',
    bgColor: 'bg-purple-100',
    icon: Play,
  },
  podcast: {
    label: 'Podcast',
    color: 'text-orange-600',
    bgColor: 'bg-orange-100',
    icon: Headphones,
  },
};

function ContentCard({ content }: { content: HelpContent }) {
  const config = typeConfig[content.type];
  const Icon = config.icon;

  return (
    <div
      className="bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-lg transition-shadow cursor-pointer group"
    >
      {/* Image Grid */}
      <div className="relative aspect-[4/3] overflow-hidden">
        {content.images.length === 1 ? (
          <img
            src={content.images[0]}
            alt={content.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="grid grid-cols-2 gap-1 h-full">
            {content.images.slice(0, 2).map((img, idx) => (
              <div key={idx} className={cn('overflow-hidden', idx === 0 && content.images.length === 2 && 'row-span-2')}>
                <img
                  src={img}
                  alt={`${content.title} ${idx + 1}`}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                />
              </div>
            ))}
          </div>
        )}

        {/* Type Badge */}
        <div className="absolute top-3 left-3">
          <span className={cn(
            'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium',
            config.bgColor,
            config.color
          )}>
            <Icon className="h-3.5 w-3.5" />
            {config.label}
          </span>
        </div>

        {/* Play button for courses */}
        {content.type === 'course' && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-14 h-14 rounded-full bg-white/90 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
              <Play className="h-6 w-6 text-purple-600 ml-1" fill="currentColor" />
            </div>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-1 group-hover:text-teal-600 transition-colors">
          {content.title}
        </h3>
        <p className="text-sm text-gray-500 mb-4 line-clamp-2">
          {content.description}
        </p>

        {/* Footer */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-full bg-gray-200 flex items-center justify-center overflow-hidden">
              {content.authorAvatar ? (
                <img src={content.authorAvatar} alt={content.author} className="w-full h-full object-cover" />
              ) : (
                <User className="h-4 w-4 text-gray-500" />
              )}
            </div>
            <span className="text-sm text-gray-600">{content.author}</span>
          </div>

          <div className="flex items-center gap-3 text-sm text-gray-500">
            {content.duration && (
              <div className="flex items-center gap-1">
                <Clock className="h-4 w-4" />
                <span>{content.duration}</span>
              </div>
            )}
            {content.views && (
              <div className="flex items-center gap-1">
                <Eye className="h-4 w-4" />
                <span>{content.views >= 1000 ? `${(content.views / 1000).toFixed(1)}k` : content.views}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function HelpCenterPage() {
  const [filter, setFilter] = useState<ContentType | 'all'>('all');

  const filteredContent = filter === 'all'
    ? helpContent
    : helpContent.filter((c) => c.type === filter);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Help Center</h1>
        <Button
          variant="ghost"
          size="sm"
          leftIcon={<Upload className="h-4 w-4" />}
          className="text-gray-500 hover:text-gray-700"
        >
          Upload Document
        </Button>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => setFilter('all')}
          className={cn(
            'px-4 py-2 text-sm font-medium rounded-lg transition-colors',
            filter === 'all'
              ? 'bg-teal-500 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          )}
        >
          All
        </button>
        {Object.entries(typeConfig).map(([type, config]) => (
          <button
            key={type}
            onClick={() => setFilter(type as ContentType)}
            className={cn(
              'px-4 py-2 text-sm font-medium rounded-lg transition-colors',
              filter === type
                ? 'bg-teal-500 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            {config.label}s
          </button>
        ))}
      </div>

      {/* Content Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredContent.map((content) => (
          <ContentCard key={content.id} content={content} />
        ))}
      </div>

      {/* Empty State */}
      {filteredContent.length === 0 && (
        <div className="text-center py-16">
          <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            No content found
          </h3>
          <p className="text-gray-500">
            Try selecting a different filter
          </p>
        </div>
      )}
    </div>
  );
}
