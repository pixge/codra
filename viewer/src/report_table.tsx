import { useMemo, useState } from "react"
import type { FileReport, UnitReport } from "./report_types"
import { evaluateMetrics, type StatusLevel } from "./report_utils"

export type SortKey = "file" | "unit" | "kind" | "status" | "csa" | "id" | "bps"

type ReportTableProps = {
  files: FileReport[]
  filterText: string
  statusFilter: StatusLevel | "all"
  onlyIssues: boolean
}

type Row = {
  file: string
  unit: string
  kind: string
  status: StatusLevel
  statusScore: number
  issues: string[]
  csa: number
  idMax: number
  bps: number
  raw: UnitReport
}

export function ReportTable({
  files,
  filterText,
  statusFilter,
  onlyIssues
}: ReportTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("file")
  const [direction, setDirection] = useState<"asc" | "desc">("asc")

  const rows = useMemo(() => {
    const entries: Row[] = []
    for (const file of files) {
      for (const unit of file.units) {
        const evaluation = evaluateMetrics(unit.metrics)
        entries.push({
          file: file.file_path,
          unit: unit.unit.qualified_id,
          kind: unit.unit.kind,
          status: evaluation.level,
          statusScore: evaluation.score,
          issues: evaluation.issues.map((issue) => issue.label),
          csa: unit.metrics.csa_main,
          idMax: unit.metrics.id_max,
          bps: unit.metrics.bps,
          raw: unit
        })
      }
    }
    const needle = filterText.trim().toLowerCase()
    const filtered = entries.filter((row) => {
      const matchesText = needle
        ? [row.file, row.unit, row.kind, row.issues.join(" ")]
            .join(" ")
            .toLowerCase()
            .includes(needle)
        : true
      const matchesStatus =
        statusFilter === "all" ? true : row.status === statusFilter
      const matchesIssues = onlyIssues ? row.status !== "ok" : true
      return matchesText && matchesStatus && matchesIssues
    })
    const sorted = [...filtered].sort((left, right) => {
      const factor = direction === "asc" ? 1 : -1
      if (sortKey === "file") {
        return left.file.localeCompare(right.file) * factor
      }
      if (sortKey === "unit") {
        return left.unit.localeCompare(right.unit) * factor
      }
      if (sortKey === "kind") {
        return left.kind.localeCompare(right.kind) * factor
      }
      if (sortKey === "status") {
        return (left.statusScore - right.statusScore) * factor
      }
      if (sortKey === "csa") {
        return (left.csa - right.csa) * factor
      }
      if (sortKey === "id") {
        return (left.idMax - right.idMax) * factor
      }
      return (left.bps - right.bps) * factor
    })
    return sorted
  }, [files, filterText, sortKey, direction])

  const setSort = (key: SortKey) => {
    if (sortKey === key) {
      setDirection(direction === "asc" ? "desc" : "asc")
      return
    }
    setSortKey(key)
    setDirection("asc")
  }

  return (
    <table className="report-table">
      <thead>
        <tr>
          <th>
            <button type="button" onClick={() => setSort("file")}>
              File
            </button>
          </th>
          <th>
            <button type="button" onClick={() => setSort("unit")}>
              Unit
            </button>
          </th>
          <th>
            <button type="button" onClick={() => setSort("kind")}>
              Kind
            </button>
          </th>
          <th>
            <button type="button" onClick={() => setSort("status")}>
              Status
            </button>
          </th>
          <th>
            <button type="button" onClick={() => setSort("csa")}>
              CSA
            </button>
          </th>
          <th>
            <button type="button" onClick={() => setSort("id")}>
              ID Max
            </button>
          </th>
          <th>
            <button type="button" onClick={() => setSort("bps")}>
              BPS
            </button>
          </th>
          <th>Issues</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={`${row.file}:${row.unit}:${row.kind}`}>
            <td>{row.file}</td>
            <td>{row.unit}</td>
            <td>{row.kind}</td>
            <td>
              <span className={`status status-${row.status}`}>
                <span className="status-dot" />
                {row.status}
              </span>
            </td>
            <td>{row.csa}</td>
            <td>{row.idMax}</td>
            <td>{row.bps.toFixed(2)}</td>
            <td>
              <div className="issue-list">
                {row.issues.length ? (
                  row.issues.map((issue) => (
                    <span key={issue} className="issue-pill">
                      {issue}
                    </span>
                  ))
                ) : (
                  <span className="issue-pill issue-ok">OK</span>
                )}
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
