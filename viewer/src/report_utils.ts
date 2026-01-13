import type { UnitMetrics } from "./report_types"

export type StatusLevel = "ok" | "warning" | "critical"

type Issue = {
  label: string
  level: StatusLevel
}

const thresholds = {
  csa: {
    warning: 5,
    critical: 10
  },
  idMax: {
    warning: 3,
    critical: 5
  },
  bps: {
    warning: 0.7,
    critical: 0.5
  }
}

const levelScore: Record<StatusLevel, number> = {
  ok: 0,
  warning: 1,
  critical: 2
}

export function evaluateMetrics(metrics: UnitMetrics): {
  level: StatusLevel
  score: number
  issues: Issue[]
} {
  const issues: Issue[] = []

  if (metrics.csa_main >= thresholds.csa.critical) {
    issues.push({ label: "CSA >= 10", level: "critical" })
  } else if (metrics.csa_main >= thresholds.csa.warning) {
    issues.push({ label: "CSA >= 5", level: "warning" })
  }

  if (metrics.id_max >= thresholds.idMax.critical) {
    issues.push({ label: "ID max >= 5", level: "critical" })
  } else if (metrics.id_max >= thresholds.idMax.warning) {
    issues.push({ label: "ID max >= 3", level: "warning" })
  }

  if (metrics.bps <= thresholds.bps.critical) {
    issues.push({ label: "BPS <= 0.5", level: "critical" })
  } else if (metrics.bps <= thresholds.bps.warning) {
    issues.push({ label: "BPS <= 0.7", level: "warning" })
  }

  if (metrics.unresolved_calls.length > 0) {
    issues.push({ label: "Chiamate non risolte", level: "warning" })
  }

  let level: StatusLevel = "ok"
  for (const issue of issues) {
    if (levelScore[issue.level] > levelScore[level]) {
      level = issue.level
    }
  }

  return {
    level,
    score: levelScore[level],
    issues
  }
}
