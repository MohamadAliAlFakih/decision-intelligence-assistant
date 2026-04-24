import { useState } from 'react'
import QueryInput from './components/QueryInput.jsx'
import ResultCard from './components/ResultCard.jsx'
import ComparisonTable from './components/ComparisonTable.jsx'

export default function App() {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(queryText) {
    setLoading(true)
    setError(null)
    setResult(null)

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
    <div className="bg-gray-50 min-h-screen">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-semibold text-gray-800 mb-6">Decision Intelligence Assistant</h1>
        <QueryInput
          query={query}
          onQueryChange={setQuery}
          onSubmit={handleSubmit}
          loading={loading}
        />
        {loading && (
          <div className="flex flex-col items-center justify-center py-6 mb-6">
            <div className="animate-spin h-6 w-6 border-2 border-blue-500 border-t-transparent rounded-full"></div>
            <p className="text-sm text-gray-500 mt-2">Analyzing...</p>
          </div>
        )}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-3 mb-6">
            {error}
          </div>
        )}
        {!loading && !error && !result && (
          <div className="text-center text-gray-500 py-6">
            <p className="font-semibold">No results yet</p>
            <p className="text-sm mt-1">Enter a customer support query above and click Analyze Query to see the four-way comparison.</p>
          </div>
        )}
        {result && (
          <>
            <div className="grid grid-cols-2 gap-4 mb-6">
              <ResultCard
                label="RAG Answer"
                answer={result.rag_answer}
                latencyMs={result.rag_latency_ms}
                costUsd={result.rag_cost_usd}
              />
              <ResultCard
                label="Direct Answer"
                answer={result.non_rag_answer}
                latencyMs={result.non_rag_latency_ms}
                costUsd={result.non_rag_cost_usd}
              />
            </div>

            <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">
                Sources ({result.retrieved_tickets.length} retrieved tickets)
              </h3>
              {result.retrieved_tickets.length === 0 ? (
                <p className="text-sm text-gray-500">No sources retrieved.</p>
              ) : (
                <ol className="list-decimal list-inside space-y-2">
                  {result.retrieved_tickets.map((ticket, i) => (
                    <li key={i} className="text-sm text-gray-700">
                      <span className="line-clamp-2 inline">{ticket.text}</span>
                      <span className="text-xs text-gray-500 ml-2">
                        {(ticket.similarity * 100).toFixed(1)}% match
                      </span>
                    </li>
                  ))}
                </ol>
              )}
            </div>

            <ComparisonTable
              mlPrediction={result.ml_prediction}
              llmPrediction={result.llm_prediction}
              atScaleProjection={result.at_scale_projection}
            />
          </>
        )}
      </div>
    </div>
  )
}
