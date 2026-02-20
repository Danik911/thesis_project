export type ProvenanceSource =
  | 'TEMPLATE'
  | 'EXTRACTED'
  | 'INFERRED'
  | 'SME_REQUIRED'
  | 'SME_MODIFIED';

export interface ClassificationResult {
  test_type: 'HPLC' | 'LOD' | 'TITRATION' | 'IDENTITY' | 'OTHER';
  confidence: number;
  method: string;
  evidence: string[];
  pdf_filename?: string | null;
}

export interface TemplateResponse {
  test_type: 'HPLC' | 'LOD' | 'TITRATION' | 'IDENTITY';
  mda_template: Record<string, unknown>;
  variable_fields: string[];
  fixed_fields: string[];
  analysis_count: number;
  component_count: number;
  calc_variable_count: number;
  calculation_count: number;
}

export interface ProvenanceField {
  source: ProvenanceSource;
  confidence: number;
  source_detail?: string;
  original_value?: unknown;
}

export interface ProvenancePayload {
  fields: Record<string, ProvenanceField>;
}

export interface MergeConflictResponse {
  field_path: string;
  template_value: unknown;
  extracted_value: unknown;
  resolution?: string | null;
  resolved_by?: string | null;
}

export interface PipelineStageDetailResponse {
  stage: string;
  duration_ms: number;
  summary: string;
  details: Record<string, unknown>;
}

export interface ExtractResponse {
  job_id: string;
  status: string;
  filename: string;
  size_bytes: number;
  classification: ClassificationResult;
  mda_template: Record<string, unknown> | null;
  provenance?: ProvenancePayload;
  conflicts?: MergeConflictResponse[];
  stage_details?: PipelineStageDetailResponse[];
  pipeline_type: 'two_layer' | 'single_layer';
  test_type: ClassificationResult['test_type'];
  extraction_trace?: Record<string, unknown> | null;
  raw_extraction?: Record<string, unknown> | null;
  validated: boolean;
  validation_error?: string | null;
  mda_generation?: Record<string, unknown> | null;
}

export interface StatusResponse {
  job_id: string;
  status: string;
  created_at: string;
  updated_at: string;
  pdf_filename: string;
  extraction_trace?: Record<string, unknown> | null;
  mda_template?: Record<string, unknown> | null;
  classification?: ClassificationResult;
  provenance?: ProvenancePayload;
  conflicts?: MergeConflictResponse[];
  stage_details?: PipelineStageDetailResponse[];
  error?: string | null;
  chat_history_length: number;
  edit_log_length: number;
}
