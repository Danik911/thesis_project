interface TemplateField {
  key: string;
  label: string;
  kind: 'fixed' | 'variable';
  value?: string;
}

interface TemplatePreviewProps {
  fields: TemplateField[];
  onContinue: () => void;
}

export default function TemplatePreview({ fields, onContinue }: TemplatePreviewProps) {
  const fixedCount = fields.filter((field) => field.kind === 'fixed').length;
  const variableCount = fields.filter((field) => field.kind === 'variable').length;

  return (
    <div className="rounded-xl bg-slate-800/50 border border-slate-700/50 p-5 space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-500">Template Skeleton</p>
          <h3 className="text-lg font-semibold text-slate-100 mt-1">Pre-Extraction Preview</h3>
        </div>
        <p className="text-sm text-slate-300">{fixedCount} template + {variableCount} variable</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {fields.map((field) => (
          <div
            key={field.key}
            className={`rounded-lg px-3 py-2 border text-sm ${
              field.kind === 'fixed'
                ? 'bg-emerald-500/10 border-emerald-500/25 text-emerald-300'
                : 'bg-slate-900 border-slate-600 border-dashed text-slate-300'
            }`}
          >
            <p className="font-medium">{field.label}</p>
            <p className="text-xs mt-1 opacity-80">{field.value ?? (field.kind === 'fixed' ? 'Template default' : 'To be extracted')}</p>
          </div>
        ))}
      </div>

      <div className="flex justify-end">
        <button
          onClick={onContinue}
          className="px-4 py-2 rounded-lg text-sm font-medium bg-emerald-600 hover:bg-emerald-500 text-white transition-all"
        >
          Continue to Extraction
        </button>
      </div>
    </div>
  );
}

export type { TemplatePreviewProps, TemplateField };