export interface BIColumn {
  name: string;
  dtype: string;
  unique_count: number;
  null_count: number;
  sample_values: Array<string | number | boolean | null>;
  value_counts?: Record<string, number>;
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
  filtered_columns?: BIColumn[];
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
  langfuse_trace_id?: string | null;
  model?: string;
}

// ---------------------------------------------------------------------------
// Chart types
// ---------------------------------------------------------------------------

export interface BIKPICard {
  column: string;
  dtype: string;
  count: number;
  mean: number | null;
  min: number | null;
  max: number | null;
  sum: number | null;
}

export interface BIChartRecommendation {
  chart_id: string;
  chart_type: 'bar' | 'line' | 'scatter' | 'histogram' | 'heatmap';
  title: string;
  x_column: string;
  y_column: string | null;
  value_column?: string;
  aggregation: string | null;
  group_by?: string;
  reason: string;
}

export interface BIChartRecommendResponse {
  session_id: string;
  filtered_row_count: number;
  kpi_cards: BIKPICard[];
  recommended_charts: BIChartRecommendation[];
}

export interface BIChartDataRequest {
  chart_type: string;
  x_column: string;
  y_column?: string | null;
  aggregation?: string | null;
  group_by?: string | null;
  bins?: number;
  limit?: number;
}

export interface BIChartDataPoint {
  x: string | number;
  y: number;
  [key: string]: string | number | null | undefined;
}

export interface BIHistogramBin {
  bin_start: number;
  bin_end: number;
  count: number;
}

export interface BIHeatmapCell {
  x: string;
  y: string;
  value: number;
}

export interface BIChartDataResponse {
  chart_type: string;
  x_column: string;
  y_column?: string;
  value_column?: string;
  aggregation?: string;
  group_by?: string;
  groups?: string[];
  data: BIChartDataPoint[] | BIHistogramBin[] | BIHeatmapCell[];
  data_points: number;
  sampled?: boolean;
  sample_size?: number;
  bins?: number;
}

// ---------------------------------------------------------------------------
// Snowflake data source types
// ---------------------------------------------------------------------------

export interface SnowflakeConnectRequest {
  account: string;
  user: string;
  password: string;
  warehouse: string;
  database: string;
  schema_name: string;
}

export interface SnowflakeTable {
  name: string;
  kind: string;
  row_count: number | null;
}

export interface SnowflakeTablesResponse {
  tables: SnowflakeTable[];
  database: string;
  schema: string;
}

export interface SnowflakeStageFile {
  name: string;
  size: number;
  last_modified: string;
}

export interface SnowflakeStageFilesResponse {
  files: SnowflakeStageFile[];
  stage: string;
}

export interface SnowflakeLoadTableRequest extends SnowflakeConnectRequest {
  table_name: string;
}

export interface SnowflakeLoadStageFileRequest extends SnowflakeConnectRequest {
  stage_name: string;
  file_path: string;
}
