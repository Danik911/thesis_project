/**
 * TemplateEditor Component
 *
 * Structured form for editing URS template sections before submission.
 * Supports editing system info, introduction, and requirement items.
 */

import { useState, useCallback } from 'react';
import {
  URSTemplate,
  URSTemplateData,
  RequirementItem,
  templateDataToMarkdown,
  getCategoryInfo,
} from '@/lib/templates';

// =============================================================================
// Type Definitions
// =============================================================================

interface TemplateEditorProps {
  template: URSTemplate;
  initialData: URSTemplateData;
  onSubmit: (markdown: string) => void;
  onBack: () => void;
}

type RequirementSectionKey =
  | 'functionalRequirements'
  | 'regulatoryRequirements'
  | 'performanceRequirements'
  | 'integrationRequirements';

// =============================================================================
// Main Component
// =============================================================================

export default function TemplateEditor({
  template,
  initialData,
  onSubmit,
  onBack,
}: TemplateEditorProps) {
  const [data, setData] = useState<URSTemplateData>(initialData);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const categoryInfo = getCategoryInfo(template.gampCategory);

  // ---------------------------------------------------------------------------
  // Field Update Handlers
  // ---------------------------------------------------------------------------

  const updateField = useCallback(
    <K extends keyof URSTemplateData>(field: K, value: URSTemplateData[K]) => {
      setData((prev) => ({ ...prev, [field]: value }));
    },
    []
  );

  const updateRequirement = useCallback(
    (
      section: RequirementSectionKey,
      index: number,
      field: 'id' | 'description',
      value: string
    ) => {
      setData((prev) => ({
        ...prev,
        [section]: prev[section].map((item, i) =>
          i === index ? { ...item, [field]: value } : item
        ),
      }));
    },
    []
  );

  const addRequirement = useCallback((section: RequirementSectionKey) => {
    const prefix = section.replace('Requirements', '').substring(0, 3).toUpperCase();
    const newItem: RequirementItem = {
      id: `URS-${prefix}-NEW`,
      description: '',
    };
    setData((prev) => ({
      ...prev,
      [section]: [...prev[section], newItem],
    }));
  }, []);

  const removeRequirement = useCallback(
    (section: RequirementSectionKey, index: number) => {
      setData((prev) => ({
        ...prev,
        [section]: prev[section].filter((_, i) => i !== index),
      }));
    },
    []
  );

  // ---------------------------------------------------------------------------
  // Submission Handler
  // ---------------------------------------------------------------------------

  const handleSubmit = useCallback(() => {
    setIsSubmitting(true);
    const markdown = templateDataToMarkdown(template, data);
    onSubmit(markdown);
  }, [template, data, onSubmit]);

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Templates
        </button>

        <div className="flex items-center gap-3">
          <span className="text-3xl">{template.icon}</span>
          <div className="text-right">
            <h2 className="text-xl font-bold text-white">{template.name}</h2>
            <span className={`inline-block px-2 py-0.5 text-xs rounded-full ${categoryInfo.colorClass}`}>
              {categoryInfo.label}
            </span>
          </div>
        </div>
      </div>

      {/* Form Sections */}
      <div className="space-y-6">
        {/* System Information */}
        <FormSection title="System Information" icon="🏢">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField
              label="System Name"
              value={data.systemName}
              onChange={(v) => updateField('systemName', v)}
              placeholder="Enter system name..."
            />
            <FormField
              label="System Type"
              value={data.systemType}
              onChange={(v) => updateField('systemType', v)}
              placeholder="e.g., Sample Management Platform"
            />
            <FormField
              label="Domain"
              value={data.domain}
              onChange={(v) => updateField('domain', v)}
              placeholder="e.g., Quality Control"
            />
            <FormSelect
              label="Complexity Level"
              value={data.complexityLevel}
              options={['Low', 'Medium', 'Medium-High', 'High']}
              onChange={(v) => updateField('complexityLevel', v as URSTemplateData['complexityLevel'])}
            />
          </div>
        </FormSection>

        {/* Introduction */}
        <FormSection title="Introduction" icon="📝">
          <textarea
            value={data.introduction}
            onChange={(e) => updateField('introduction', e.target.value)}
            className="w-full h-32 px-4 py-3 bg-slate-900 border border-slate-600 rounded-lg
                       text-white placeholder-slate-500 resize-none
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                       transition-all duration-200"
            placeholder="Describe the purpose and scope of this URS document..."
          />
        </FormSection>

        {/* Functional Requirements */}
        <RequirementSection
          title="Functional Requirements"
          icon="⚙️"
          items={data.functionalRequirements}
          onUpdate={(i, f, v) => updateRequirement('functionalRequirements', i, f, v)}
          onAdd={() => addRequirement('functionalRequirements')}
          onRemove={(i) => removeRequirement('functionalRequirements', i)}
        />

        {/* Regulatory Requirements */}
        <RequirementSection
          title="Regulatory Requirements"
          icon="📋"
          items={data.regulatoryRequirements}
          onUpdate={(i, f, v) => updateRequirement('regulatoryRequirements', i, f, v)}
          onAdd={() => addRequirement('regulatoryRequirements')}
          onRemove={(i) => removeRequirement('regulatoryRequirements', i)}
        />

        {/* Performance Requirements */}
        <RequirementSection
          title="Performance Requirements"
          icon="⚡"
          items={data.performanceRequirements}
          onUpdate={(i, f, v) => updateRequirement('performanceRequirements', i, f, v)}
          onAdd={() => addRequirement('performanceRequirements')}
          onRemove={(i) => removeRequirement('performanceRequirements', i)}
        />

        {/* Integration Requirements */}
        <RequirementSection
          title="Integration Requirements"
          icon="🔗"
          items={data.integrationRequirements}
          onUpdate={(i, f, v) => updateRequirement('integrationRequirements', i, f, v)}
          onAdd={() => addRequirement('integrationRequirements')}
          onRemove={(i) => removeRequirement('integrationRequirements', i)}
        />
      </div>

      {/* Submit Button */}
      <div className="flex justify-between items-center pt-6 border-t border-slate-700">
        <button
          onClick={onBack}
          className="px-6 py-3 rounded-lg border border-slate-600 text-slate-300
                     hover:bg-slate-800 hover:text-white transition-colors"
        >
          Cancel
        </button>

        <button
          onClick={handleSubmit}
          disabled={isSubmitting}
          className="btn-primary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? (
            <>
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="none"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Preparing...
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Generate Test Suite
            </>
          )}
        </button>
      </div>
    </div>
  );
}

// =============================================================================
// Sub-components
// =============================================================================

function FormSection({
  title,
  icon,
  children,
}: {
  title: string;
  icon: string;
  children: React.ReactNode;
}) {
  return (
    <div className="card">
      <h3 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
        <span>{icon}</span>
        {title}
      </h3>
      {children}
    </div>
  );
}

function FormField({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="block text-sm text-slate-400 mb-1.5">{label}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-4 py-2.5 bg-slate-900 border border-slate-600 rounded-lg
                   text-white placeholder-slate-500
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                   transition-all duration-200"
      />
    </div>
  );
}

function FormSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (v: string) => void;
}) {
  return (
    <div>
      <label className="block text-sm text-slate-400 mb-1.5">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-4 py-2.5 bg-slate-900 border border-slate-600 rounded-lg
                   text-white appearance-none cursor-pointer
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                   transition-all duration-200"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e")`,
          backgroundPosition: 'right 0.75rem center',
          backgroundRepeat: 'no-repeat',
          backgroundSize: '1.5em 1.5em',
          paddingRight: '2.5rem',
        }}
      >
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
    </div>
  );
}

function RequirementSection({
  title,
  icon,
  items,
  onUpdate,
  onAdd,
  onRemove,
}: {
  title: string;
  icon: string;
  items: RequirementItem[];
  onUpdate: (index: number, field: 'id' | 'description', value: string) => void;
  onAdd: () => void;
  onRemove: (index: number) => void;
}) {
  return (
    <FormSection title={title} icon={icon}>
      <div className="space-y-3">
        {items.map((item, i) => (
          <div key={i} className="flex gap-3 items-start group">
            {/* Requirement ID */}
            <input
              type="text"
              value={item.id}
              onChange={(e) => onUpdate(i, 'id', e.target.value)}
              className="w-36 px-3 py-2.5 bg-slate-900 border border-slate-600 rounded-lg
                         font-mono text-sm text-blue-400
                         focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                         transition-all duration-200"
              placeholder="URS-XXX-001"
            />

            {/* Requirement Description */}
            <input
              type="text"
              value={item.description}
              onChange={(e) => onUpdate(i, 'description', e.target.value)}
              className="flex-1 px-4 py-2.5 bg-slate-900 border border-slate-600 rounded-lg
                         text-white placeholder-slate-500
                         focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                         transition-all duration-200"
              placeholder="Enter requirement description..."
            />

            {/* Remove Button */}
            <button
              onClick={() => onRemove(i)}
              className="p-2.5 text-slate-500 hover:text-red-400 hover:bg-red-500/10
                         rounded-lg transition-colors opacity-0 group-hover:opacity-100"
              title="Remove requirement"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            </button>
          </div>
        ))}

        {/* Add Requirement Button */}
        <button
          onClick={onAdd}
          className="flex items-center gap-2 text-blue-400 hover:text-blue-300
                     text-sm font-medium transition-colors mt-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Requirement
        </button>

        {/* Empty State */}
        {items.length === 0 && (
          <div className="text-center py-6 text-slate-500 text-sm">
            No requirements defined. Click &quot;Add Requirement&quot; to add one.
          </div>
        )}
      </div>
    </FormSection>
  );
}
