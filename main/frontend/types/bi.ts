export interface BIColumn {
  name: string;
  dtype: string;
  unique_count: number;
  null_count: number;
  sample_values: Array<string | number | boolean | null>;
}

export interface BISession {
  session_id: string;
  filename: string;
  total_rows: number;
  total_columns: number;
  columns: BIColumn[];
}

export interface BIDataResponse {
  rows: Array<Record<string, unknown>>;
  total_rows: number;
  total_filtered_rows: number;
  page: number;
  page_size: number;
  total_pages: number;
  active_filters?: BIFilterDef[];
}

export interface BIUploadResponse extends BISession {
  preview: BIDataResponse;
}

export interface BIFilterDef {
  column: string;
  operator: string;
  value: string | number | boolean | null | Array<string | number>;
}

export interface BIFilterResponse {
  total_filtered_rows: number;
  active_filters: BIFilterDef[];
  preview: BIDataResponse;
}

export interface BIChatMessage {
  role: 'user' | 'assistant';
  content: string;
  tool_calls?: BIToolCall[];
  filters_changed?: boolean;
}

export interface BIToolCall {
  tool: string;
  input: Record<string, unknown>;
  result: Record<string, unknown>;
  status: 'success' | 'error';
}

export interface BIChatResponse {
  response: string;
  tool_calls: BIToolCall[];
  filters_changed: boolean;
  active_filters: BIFilterDef[];
  filtered_row_count: number;
}
