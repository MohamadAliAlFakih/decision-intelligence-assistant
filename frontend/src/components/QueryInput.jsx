export default function QueryInput({ query, onQueryChange, onSubmit, loading }) {
  function handleClick() {
    if (!query.trim() || loading) return
    onSubmit(query)
  }
  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (!query.trim() || loading) return
      onSubmit(query)
    }
  }
  const disabled = loading || query.trim() === ''
  return (
    <div className="flex flex-col gap-3 mb-6">
      <textarea
        value={query}
        onChange={(e) => onQueryChange(e.target.value)}
        onKeyDown={handleKeyDown}
        rows={3}
        placeholder="Enter your question"
        className="w-full resize-none rounded-xl border border-slate-700 bg-slate-800 p-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
      />
      <button
        type="button"
        onClick={handleClick}
        disabled={disabled}
        className={
          'min-h-[44px] bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold px-6 rounded-xl self-start transition-all duration-200 ' +
          (disabled
            ? 'opacity-40 cursor-not-allowed'
            : 'hover:from-blue-500 hover:to-indigo-500 shadow-lg shadow-blue-500/20 hover:shadow-blue-500/40')
        }
      >
        Analyze Query
      </button>
    </div>
  )
}
