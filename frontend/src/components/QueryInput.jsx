export default function QueryInput({ query, onQueryChange, onSubmit, loading }) {
  function handleClick() {
    if (!query.trim() || loading) return
    onSubmit(query)
  }
  const disabled = loading || query.trim() === ''
  return (
    <div className="flex flex-col gap-3 mb-6">
      <textarea
        value={query}
        onChange={(e) => onQueryChange(e.target.value)}
        rows={3}
        placeholder="Enter a customer support query..."
        className="w-full resize-none rounded-lg border border-gray-300 p-3 text-sm"
      />
      <button
        type="button"
        onClick={handleClick}
        disabled={disabled}
        className={
          'min-h-[44px] bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 rounded-lg self-start ' +
          (disabled ? 'opacity-50 cursor-not-allowed' : '')
        }
      >
        Analyze Query
      </button>
    </div>
  )
}
