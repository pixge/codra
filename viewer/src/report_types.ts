export type ReportSummary = {
  total_files: number
  total_units: number
}

export type UnitDefinition = {
  file_path: string
  qualified_id: string
  kind: string
  start_line: number
  end_line: number
}

export type UnitMetrics = {
  csa_main: number
  external_symbols: string[]
  self_fields_read: string[]
  id_max: number
  id_avg: number
  unresolved_calls: string[]
  bps: number
}

export type UnitReport = {
  unit: UnitDefinition
  metrics: UnitMetrics
}

export type FileReport = {
  file_path: string
  units: UnitReport[]
}

export type Report = {
  schema_version: string
  language: string
  summary: ReportSummary
  files: FileReport[]
}
