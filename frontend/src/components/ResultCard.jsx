export default function ResultCard({ label, answer, latencyMs, costUsd }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <h2 className="text-lg font-semibold text-gray-800 mb-2">{label}</h2>
      {answer === null || answer === undefined ? (
        <span className="inline-block bg-gray-100 text-gray-500 text-sm px-2 py-1 rounded">
          Service unavailable
        </span>
      ) : (
        <>
          <p className="text-sm text-gray-700 leading-relaxed max-h-64 overflow-y-auto whitespace-pre-wrap">
            {answer}
          </p>
          <div className="mt-3 text-xs text-gray-500 flex gap-4">
            <span>{latencyMs !== null && latencyMs !== undefined ? `${latencyMs.toFixed(0)} ms` : '—'}</span>
            <span>{costUsd !== null && costUsd !== undefined ? `$${costUsd.toFixed(5)}` : '—'}</span>
          </div>
        </>
      )}
    </div>
  )
}
