interface ProvenanceBadgeProps {
  source: 'TEMPLATE' | 'EXTRACTED' | 'INFERRED' | 'SME_REQUIRED' | 'SME_MODIFIED';
  confidence?: number;
  detail?: string;
}

const SOURCE_LABELS: Record<ProvenanceBadgeProps['source'], string> = {
  TEMPLATE: 'Template',
  EXTRACTED: 'Extracted',
  INFERRED: 'Inferred',
  SME_REQUIRED: 'SME Required',
  SME_MODIFIED: 'SME Modified',
};

const SOURCE_CLASSES: Record<ProvenanceBadgeProps['source'], string> = {
  TEMPLATE: 'bg-emerald-500/15 border-emerald-500/25 text-emerald-400',
  EXTRACTED: 'bg-blue-500/15 border-blue-500/25 text-blue-400',
  INFERRED: 'bg-violet-500/15 border-violet-500/25 text-violet-400',
  SME_REQUIRED: 'bg-orange-500/15 border-orange-500/25 text-orange-400',
  SME_MODIFIED: 'bg-amber-500/15 border-amber-500/25 text-amber-400',
};

export default function ProvenanceBadge({ source, confidence, detail }: ProvenanceBadgeProps) {
  const confidenceText = typeof confidence === 'number' ? ` · ${Math.round(confidence * 100)}%` : '';
  const tooltip = detail ? `${SOURCE_LABELS[source]}: ${detail}` : SOURCE_LABELS[source];

  return (
    <span
      title={tooltip}
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] leading-4 font-medium border ${SOURCE_CLASSES[source]}`}
    >
      {SOURCE_LABELS[source]}
      {confidenceText}
    </span>
  );
}

export type { ProvenanceBadgeProps };