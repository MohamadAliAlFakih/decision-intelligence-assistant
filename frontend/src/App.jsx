import { useState } from 'react'
import QueryInput from './components/QueryInput.jsx'
import ResultCard from './components/ResultCard.jsx'
import ComparisonTable from './components/ComparisonTable.jsx'

export default function App() {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showSources, setShowSources] = useState(false)
  const [showComparison, setShowComparison] = useState(false)

  async function handleSubmit(queryText) {
    setLoading(true)
    setError(null)
    setResult(null)
    setShowSources(false)
    setShowComparison(false)

    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: queryText }),
      })

      if (!response.ok) {
        throw new Error('Request failed: ' + response.status)
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError('Request failed. Check that the backend is running and try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-slate-950 min-h-screen">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Decision Intelligence Assistant</h1>
          <p className="text-sm text-slate-500 mt-1">Customer support triage — RAG · Direct · ML · Zero-shot</p>
        </div>

        <QueryInput
          query={query}
          onQueryChange={setQuery}
          onSubmit={handleSubmit}
          loading={loading}
        />

        {loading && (
          <div className="flex flex-col items-center justify-center py-6 mb-6">
            <div className="animate-spin h-6 w-6 border-2 border-blue-500 border-t-transparent rounded-full"></div>
            <p className="text-sm text-slate-500 mt-2">Analyzing…</p>
          </div>
        )}

        {error && (
          <div className="bg-red-950/50 border border-red-800 text-red-400 rounded-xl p-3 mb-6 text-sm">
            {error}
          </div>
        )}

        {!loading && !error && !result && (
          <div className="text-center py-10">
            <p className="font-semibold text-slate-500">No results yet</p>
            <p className="text-sm text-slate-600 mt-1">Enter a customer support query above to see the four-way comparison.</p>
          </div>
        )}

        {result && (
          <>
            <div className="grid grid-cols-2 gap-4 mb-4">
              {/* Left col: RAG card + sources dropdown */}
              <div className="flex flex-col gap-2">
                <ResultCard
                  label="RAG Answer"
                  answer={result.rag_answer}
                  latencyMs={result.rag_latency_ms}
                  costUsd={result.rag_cost_usd}
                />
                <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden shadow-sm transition-all duration-200">
                  <button
                    onClick={() => setShowSources(v => !v)}
                    className="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-slate-800/50 transition-colors duration-150"
                  >
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Sources ({result.retrieved_tickets.length} retrieved)
                    </span>
                    <span className={`text-slate-500 transition-transform duration-200 ${showSources ? 'rotate-180' : ''}`}>
                      ▾
                    </span>
                  </button>
                  {showSources && (
                    <div className="px-3 pb-3">
                      {result.retrieved_tickets.length === 0 ? (
                        <p className="text-sm text-slate-500">No sources retrieved.</p>
                      ) : (
                        <ol className="space-y-3">
                          {result.retrieved_tickets.map((ticket, i) => (
                            <li key={i}>
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-xs text-slate-600 w-4">{i + 1}.</span>
                                <div className="flex-1 bg-slate-800 rounded-full h-1.5">
                                  <div
                                    className="h-1.5 rounded-full bg-blue-500"
                                    style={{ width: `${(ticket.similarity * 100).toFixed(1)}%` }}
                                  />
                                </div>
                                <span className="text-xs text-slate-500 w-14 text-right">{(ticket.similarity * 100).toFixed(1)}%</span>
                              </div>
                              <p className="text-xs text-slate-500 pl-6 line-clamp-2">{ticket.text}</p>
                            </li>
                          ))}
                        </ol>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Right col: Direct Answer card */}
              <ResultCard
                label="Direct Answer"
                answer={result.non_rag_answer}
                latencyMs={result.non_rag_latency_ms}
                costUsd={result.non_rag_cost_usd}
              />
            </div>

            {/* Priority banner + comparison table — collapsed by default */}
            {(() => {
              const pred = result.ml_prediction
              if (!pred) return null
              const urgent = pred.label === 'URGENT'
              return (
                <div className={`rounded-xl border overflow-hidden shadow-md transition-all duration-200 ${urgent ? 'border-amber-500/30' : 'border-emerald-500/30'}`}>
                  <button
                    onClick={() => setShowComparison(v => !v)}
                    className={`w-full flex items-center justify-between px-4 py-3 text-left transition-colors duration-150 ${urgent ? 'bg-amber-500/10 hover:bg-amber-500/15' : 'bg-emerald-500/10 hover:bg-emerald-500/15'}`}
                  >
                    <div className="flex items-center gap-3">
                      <span className={`text-xs font-bold uppercase tracking-wide px-2 py-1 rounded ${urgent ? 'bg-amber-500/20 text-amber-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
                        {pred.label}
                      </span>
                      <span className="text-sm text-slate-400">
                        ML priority prediction — <strong className="text-slate-200">{(pred.confidence * 100).toFixed(1)}% confidence</strong>
                      </span>
                    </div>
                    <span className={`text-slate-500 transition-transform duration-200 ${showComparison ? 'rotate-180' : ''}`}>
                      ▾
                    </span>
                  </button>
                  {showComparison && (
                    <div className="bg-slate-900 p-4">
                      <ComparisonTable
                        mlPrediction={result.ml_prediction}
                        llmPrediction={result.llm_prediction}
                        atScaleProjection={result.at_scale_projection}
                      />
                    </div>
                  )}
                </div>
              )
            })()}
          </>
        )}
      </div>
    </div>
  )
}
