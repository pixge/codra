import { useState } from "react"
import type { Report } from "./report_types"
import { ReportTable } from "./report_table"

export function App() {
  const [report, setReport] = useState<Report | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [filterText, setFilterText] = useState("")

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
            placeholder="Search by file, unit, or kind"
          />
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
          </div>
          <ReportTable files={report.files} filterText={filterText} />
        </section>
      ) : (
        <section className="empty">
          <p>No report loaded.</p>
        </section>
      )}
    </div>
  )
}
