export default function ResultCard({ label, answer, latencyMs, costUsd }) {
  return (
    <div className="bg-slate-900 rounded-xl border border-slate-800 p-4 shadow-md hover:shadow-xl hover:shadow-blue-500/10 hover:-translate-y-0.5 transition-all duration-200">
      <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">{label}</h2>
      {answer === null || answer === undefined ? (
        <span className="inline-block bg-slate-800 text-slate-500 text-sm px-2 py-1 rounded">
          Service unavailable
        </span>
      ) : (
        <>
          <p className="text-sm text-slate-300 leading-relaxed max-h-64 overflow-y-auto whitespace-pre-wrap">
            {answer}
          </p>
          <div className="mt-3 text-xs text-slate-500 flex gap-4">
            <span>{latencyMs !== null && latencyMs !== undefined ? `${latencyMs.toFixed(0)} ms` : '—'}</span>
            <span>{costUsd !== null && costUsd !== undefined ? `$${costUsd.toFixed(5)}` : '—'}</span>
          </div>
        </>
      )}
    </div>
  )
}
