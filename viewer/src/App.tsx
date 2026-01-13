import { useMemo, useState } from "react"
import type { Report } from "./report_types"
import { ReportTable } from "./report_table"
import { evaluateMetrics, type StatusLevel } from "./report_utils"

export function App() {
  const [report, setReport] = useState<Report | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [filterText, setFilterText] = useState("")
  const [statusFilter, setStatusFilter] = useState<StatusLevel | "all">("all")
  const [onlyIssues, setOnlyIssues] = useState(false)

  const handleFile = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) {
      return
    }
    const reader = new FileReader()
    reader.onload = () => {
      try {
        const parsed = JSON.parse(String(reader.result)) as Report
        setReport(parsed)
        setError(null)
      } catch (err) {
        setReport(null)
        setError("Invalid JSON report")
      }
    }
    reader.onerror = () => {
      setReport(null)
      setError("Failed to read file")
    }
    reader.readAsText(file)
  }

  const globalStats = useMemo(() => {
    if (!report) {
      return null
    }
    const stats = {
      ok: 0,
      warning: 0,
      critical: 0
    }
    for (const file of report.files) {
      for (const unit of file.units) {
        const evaluation = evaluateMetrics(unit.metrics)
        stats[evaluation.level] += 1
      }
    }
    const issues = stats.warning + stats.critical
    const overall: StatusLevel =
      stats.critical > 0 ? "critical" : stats.warning > 0 ? "warning" : "ok"
    return { ...stats, issues, overall }
  }, [report])

  return (
    <div className="app">
      <header>
        <h1>Codra Report Viewer</h1>
        <p>Load a JSON report to explore CSA, ID, and BPS metrics.</p>
      </header>
      <section className="controls">
        <label className="file-input">
          <span>Report JSON</span>
          <input type="file" accept="application/json" onChange={handleFile} />
        </label>
        <label className="filter-input">
          <span>Filter</span>
          <input
            type="text"
            value={filterText}
            onChange={(event) => setFilterText(event.target.value)}
            placeholder="Search by file, unit, kind, or issue"
          />
        </label>
        <label className="filter-input">
          <span>Status</span>
          <select
            value={statusFilter}
            onChange={(event) =>
              setStatusFilter(event.target.value as StatusLevel | "all")
            }
          >
            <option value="all">All</option>
            <option value="critical">Critical</option>
            <option value="warning">Warning</option>
            <option value="ok">OK</option>
          </select>
        </label>
        <label className="checkbox-input">
          <input
            type="checkbox"
            checked={onlyIssues}
            onChange={(event) => setOnlyIssues(event.target.checked)}
          />
          Only issues
        </label>
      </section>
      {error ? <div className="error">{error}</div> : null}
      {report ? (
        <section className="report">
          <div className="summary">
            <div>
              <strong>Schema</strong>
              <span>{report.schema_version}</span>
            </div>
            <div>
              <strong>Language</strong>
              <span>{report.language}</span>
            </div>
            <div>
              <strong>Files</strong>
              <span>{report.summary.total_files}</span>
            </div>
            <div>
              <strong>Units</strong>
              <span>{report.summary.total_units}</span>
            </div>
            <div>
              <strong>Critical</strong>
              <span>{globalStats?.critical ?? 0}</span>
            </div>
            <div>
              <strong>Warning</strong>
              <span>{globalStats?.warning ?? 0}</span>
            </div>
            <div>
              <strong>OK</strong>
              <span>{globalStats?.ok ?? 0}</span>
            </div>
            <div>
              <strong>Issues</strong>
              <span>{globalStats?.issues ?? 0}</span>
            </div>
            <div className="summary-status">
              <strong>Health</strong>
              <span className={`status status-${globalStats?.overall ?? "ok"}`}>
                <span className="status-dot" />
                {globalStats?.overall ?? "ok"}
              </span>
            </div>
          </div>
          <ReportTable
            files={report.files}
            filterText={filterText}
            statusFilter={statusFilter}
            onlyIssues={onlyIssues}
          />
        </section>
      ) : (
        <section className="empty">
          <p>No report loaded.</p>
        </section>
      )}
    </div>
  )
}
