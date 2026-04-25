function urgencyBadgeClass(label) {
  if (label === 'URGENT') return 'bg-amber-500/20 text-amber-400'
  if (label === 'NORMAL') return 'bg-emerald-500/20 text-emerald-400'
  return 'bg-slate-800 text-slate-500'
}

function UnavailableCell() {
  return (
    <td className="px-3 py-2 border-b border-slate-800" colSpan={1}>
      <span className="inline-block bg-slate-800 text-slate-500 text-sm px-2 py-1 rounded">
        Service unavailable
      </span>
    </td>
  )
}

function labelCell(pred) {
  if (!pred) return <UnavailableCell />
  return (
    <td className="px-3 py-2 border-b border-slate-800">
      <span className={`px-2 py-0.5 rounded text-sm font-semibold ${urgencyBadgeClass(pred.label)}`}>
        {pred.label}
      </span>
    </td>
  )
}

function textCell(value, winner = false) {
  return (
    <td className={`px-3 py-2 border-b border-slate-800 text-sm ${winner ? 'text-emerald-400 font-semibold' : 'text-slate-300'}`}>
      {winner
        ? <span className="flex items-center gap-1">{value} <span className="text-emerald-500">✓</span></span>
        : value}
    </td>
  )
}

function fmtPct(v) {
  return v === null || v === undefined ? 'N/A' : `${(v * 100).toFixed(1)}%`
}
function fmtMs(v) {
  return v === null || v === undefined ? '—' : `${v.toFixed(0)} ms`
}
function fmtCost(v, decimals = 5) {
  return v === null || v === undefined ? '—' : `$${v.toFixed(decimals)}`
}

export default function ComparisonTable({ mlPrediction, llmPrediction, atScaleProjection }) {
  return (
    <div className="bg-slate-900 rounded-xl border border-slate-800 p-4 shadow-md hover:shadow-xl hover:shadow-blue-500/10 hover:-translate-y-0.5 transition-all duration-200">
      <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
        ML Classifier vs LLM Zero-Shot
      </h3>
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr>
            <th className="bg-slate-800 text-slate-400 font-semibold text-left px-3 py-2">Metric</th>
            <th className="bg-slate-800 text-slate-400 font-semibold text-left px-3 py-2">ML Classifier</th>
            <th className="bg-slate-800 text-slate-400 font-semibold text-left px-3 py-2">LLM Zero-Shot</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            {textCell('Label')}
            {labelCell(mlPrediction)}
            {labelCell(llmPrediction)}
          </tr>
          <tr>
            {textCell('Confidence')}
            {textCell(fmtPct(mlPrediction?.confidence))}
            {textCell(fmtPct(llmPrediction?.confidence))}
          </tr>
          <tr>
            {textCell('Accuracy')}
            {textCell(fmtPct(mlPrediction?.accuracy))}
            {textCell('N/A')}
          </tr>
          <tr>
            {textCell('Latency')}
            {textCell(fmtMs(mlPrediction?.latency_ms), true)}
            {textCell(fmtMs(llmPrediction?.latency_ms))}
          </tr>
          <tr>
            {textCell('Cost')}
            {textCell(fmtCost(mlPrediction?.cost_usd), true)}
            {textCell(fmtCost(llmPrediction?.cost_usd))}
          </tr>
          <tr className="bg-slate-800/50">
            {textCell('At scale (10,000 tickets/hour)')}
            {textCell(fmtCost(atScaleProjection.ml_cost_per_hour, 2) + '/hr', true)}
            {textCell(fmtCost(atScaleProjection.llm_cost_per_hour, 2) + '/hr')}
          </tr>
        </tbody>
      </table>
    </div>
  )
}
