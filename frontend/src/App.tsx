import { useRef, useState } from "react"
import UrlForm from "./components/UrlForm"
import PreviewCard from "./components/PreviewCard"
import { fetchPreview } from "./lib/api"
import type { PreviewResponse } from "./types"

export default function App() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<PreviewResponse | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const handleSubmit = async (url: string) => {
    abortRef.current?.abort()
    const ctrl = new AbortController()
    abortRef.current = ctrl

    setLoading(true)
    setError(null)
    setData(null)

    try {
      const res = await fetchPreview(url, ctrl.signal)
      setData(res)
    } catch (e: any) {
      setError(e?.message || "Failed to fetch preview")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen p-6">
      <header className="max-w-2xl mx-auto mb-4">
        <h1 className="text-2xl font-bold">IGniter</h1>
        <p className="text-sm text-gray-600">Enter a URL to fetch title, description, image, site name, and full article content.</p>
      </header>

      <UrlForm onSubmit={handleSubmit} loading={loading} />
      <PreviewCard data={data} loading={loading} error={error} />
    </div>
  )
}