function urgencyBadgeClass(label) {
  if (label === 'URGENT') return 'bg-red-100 text-red-700 font-semibold'
  if (label === 'NORMAL') return 'bg-green-100 text-green-700 font-semibold'
  return 'bg-gray-100 text-gray-500'
}

function UnavailableCell() {
  return (
    <td className="px-3 py-2 border-b border-gray-100" colSpan={1}>
      <span className="inline-block bg-gray-100 text-gray-500 text-sm px-2 py-1 rounded">
        Service unavailable
      </span>
    </td>
  )
}

function labelCell(pred) {
  if (!pred) return <UnavailableCell />
  return (
    <td className="px-3 py-2 border-b border-gray-100">
      <span className={`px-2 py-0.5 rounded text-sm ${urgencyBadgeClass(pred.label)}`}>
        {pred.label}
      </span>
    </td>
  )
}

function textCell(value) {
  return (
    <td className="px-3 py-2 border-b border-gray-100 text-sm text-gray-700">
      {value}
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
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <h3 className="text-lg font-semibold text-gray-800 mb-3">
        ML Classifier vs LLM Zero-Shot Priority Prediction
      </h3>
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr>
            <th className="bg-gray-50 text-gray-600 font-semibold text-left px-3 py-2">Metric</th>
            <th className="bg-gray-50 text-gray-600 font-semibold text-left px-3 py-2">ML Classifier</th>
            <th className="bg-gray-50 text-gray-600 font-semibold text-left px-3 py-2">LLM Zero-Shot</th>
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
            {textCell(fmtMs(mlPrediction?.latency_ms))}
            {textCell(fmtMs(llmPrediction?.latency_ms))}
          </tr>
          <tr>
            {textCell('Cost')}
            {textCell(fmtCost(mlPrediction?.cost_usd))}
            {textCell(fmtCost(llmPrediction?.cost_usd))}
          </tr>
          <tr className="bg-gray-50">
            {textCell('At scale (10,000 tickets/hour)')}
            {textCell(fmtCost(atScaleProjection.ml_cost_per_hour, 2) + '/hr')}
            {textCell(fmtCost(atScaleProjection.llm_cost_per_hour, 2) + '/hr')}
          </tr>
        </tbody>
      </table>
    </div>
  )
}
