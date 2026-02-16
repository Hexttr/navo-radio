import Link from 'next/link'

export default function Page() {
  return (
    <div className="relative h-screen w-screen">
      <iframe
        src="/radio.html"
        className="h-full w-full border-0"
        title="NAVO RADIO"
        allow="autoplay"
      />
      <Link
        href="/admin"
        className="absolute top-4 right-4 px-3 py-1.5 text-sm bg-zinc-800/80 hover:bg-zinc-700 text-zinc-200 rounded-md"
      >
        Админка
      </Link>
    </div>
  )
}
