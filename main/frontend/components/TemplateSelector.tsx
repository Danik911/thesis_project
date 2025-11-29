/**
 * TemplateSelector Component
 *
 * Card-based grid for selecting GAMP-5 category templates with filtering.
 * Part of the pharmaceutical test generation workflow.
 */

import { useState } from 'react';
import {
  TEMPLATES,
  URSTemplate,
  GampCategoryFilter,
  getCategoryInfo,
} from '@/lib/templates';

interface TemplateSelectorProps {
  onSelect: (template: URSTemplate) => void;
  selectedId: string | null;
}

export default function TemplateSelector({
  onSelect,
  selectedId,
}: TemplateSelectorProps) {
  const [filter, setFilter] = useState<GampCategoryFilter>('all');

  const filteredTemplates =
    filter === 'all'
      ? TEMPLATES
      : TEMPLATES.filter((t) => t.gampCategory === filter);

  const filterOptions: { value: GampCategoryFilter; label: string }[] = [
    { value: 'all', label: 'All Templates' },
    { value: '3', label: 'Category 3' },
    { value: '4', label: 'Category 4' },
    { value: '5', label: 'Category 5' },
    { value: 'ambiguous', label: 'Ambiguous' },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-white mb-2">
          Choose a Template
        </h2>
        <p className="text-slate-400">
          Select a GAMP-5 category template to customize for your system
        </p>
      </div>

      {/* Category Filter Tabs */}
      <div className="flex flex-wrap gap-2 justify-center">
        {filterOptions.map((option) => (
          <button
            key={option.value}
            onClick={() => setFilter(option.value)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
              filter === option.value
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/25'
                : 'bg-slate-700/50 text-slate-300 hover:bg-slate-700 hover:text-white'
            }`}
          >
            {option.label}
            {option.value !== 'all' && (
              <span className="ml-2 text-xs opacity-70">
                ({TEMPLATES.filter((t) => t.gampCategory === option.value).length})
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Template Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {filteredTemplates.map((template) => {
          const categoryInfo = getCategoryInfo(template.gampCategory);
          const isSelected = selectedId === template.id;

          return (
            <button
              key={template.id}
              onClick={() => onSelect(template)}
              className={`card text-left hover:border-blue-500/50 transition-all duration-200 group ${
                isSelected
                  ? 'border-blue-500 ring-2 ring-blue-500/30 bg-blue-500/5'
                  : 'hover:bg-slate-800/80'
              }`}
            >
              <div className="flex flex-col h-full">
                {/* Icon and Title */}
                <div className="flex items-start gap-3 mb-3">
                  <span
                    className="text-3xl group-hover:scale-110 transition-transform duration-200"
                    role="img"
                    aria-label={template.name}
                  >
                    {template.icon}
                  </span>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-white truncate">
                      {template.name}
                    </h3>
                    <span
                      className={`inline-block mt-1 px-2 py-0.5 text-xs rounded-full ${categoryInfo.colorClass}`}
                    >
                      {template.gampCategory === 'ambiguous'
                        ? 'Ambiguous'
                        : `GAMP ${template.gampCategory}`}
                    </span>
                  </div>
                </div>

                {/* Description */}
                <p className="text-sm text-slate-400 line-clamp-3 flex-grow">
                  {template.description}
                </p>

                {/* Complexity Badge */}
                <div className="mt-3 pt-3 border-t border-slate-700/50">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500">Complexity</span>
                    <span
                      className={`font-medium ${
                        template.data.complexityLevel === 'Low'
                          ? 'text-green-400'
                          : template.data.complexityLevel === 'Medium'
                          ? 'text-yellow-400'
                          : template.data.complexityLevel === 'Medium-High'
                          ? 'text-orange-400'
                          : 'text-red-400'
                      }`}
                    >
                      {template.data.complexityLevel}
                    </span>
                  </div>
                </div>

                {/* Selected Indicator */}
                {isSelected && (
                  <div className="absolute top-2 right-2">
                    <svg
                      className="w-5 h-5 text-blue-500"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                )}
              </div>
            </button>
          );
        })}
      </div>

      {/* Empty State */}
      {filteredTemplates.length === 0 && (
        <div className="text-center py-12">
          <div className="text-slate-500 text-lg">
            No templates found for this category
          </div>
          <button
            onClick={() => setFilter('all')}
            className="mt-4 text-blue-400 hover:text-blue-300"
          >
            View all templates
          </button>
        </div>
      )}

      {/* Category Legend */}
      <div className="mt-8 p-4 bg-slate-800/30 rounded-xl border border-slate-700/50">
        <h4 className="text-sm font-medium text-slate-400 mb-3">
          GAMP-5 Category Guide
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-green-500/50"></span>
            <span className="text-slate-300">
              <strong>Cat 3:</strong> Standard Software
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-blue-500/50"></span>
            <span className="text-slate-300">
              <strong>Cat 4:</strong> Configured Products
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-purple-500/50"></span>
            <span className="text-slate-300">
              <strong>Cat 5:</strong> Custom Applications
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-amber-500/50"></span>
            <span className="text-slate-300">
              <strong>Ambiguous:</strong> Needs Review
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
