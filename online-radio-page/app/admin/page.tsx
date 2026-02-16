'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { format, addDays, subDays } from 'date-fns'
import { ru } from 'date-fns/locale'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Textarea } from '@/components/ui/textarea'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { useToast } from '@/hooks/use-toast'

// Прямое подключение к backend — прокси Next.js имеет таймаут 30 сек, генерация дольше
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

type Entity = {
  type: string
  text?: string | null
  audio?: string | null
  file?: string | null
  duration?: number
  id?: string
  name?: string
  artist?: string
  linkedTo?: string
}

type Playlist = {
  date: string
  createdAt: string | null
  entities: Entity[]
  timings: string[]
}

function entityIsReady(e: Entity): boolean {
  if (['dj', 'news', 'weather'].includes(e.type)) {
    return Boolean(e.text?.trim() && e.audio)
  }
  if (['song', 'podcast', 'intro'].includes(e.type)) {
    return Boolean(e.file)
  }
  return false
}

function computeTimings(entities: Entity[]): string[] {
  const result: string[] = []
  let total = 0
  for (const e of entities) {
    result.push(formatDuration(total))
    total += e.duration ?? 0
  }
  return result
}

function formatDuration(seconds: number): string {
  const s = Math.floor(seconds)
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  if (h > 0) return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`
  return `${m.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`
}

function entityLabel(e: Entity): string {
  switch (e.type) {
    case 'song':
      return e.artist && e.name ? `${e.artist} — ${e.name}` : 'Песня'
    case 'dj':
      return e.text?.slice(0, 50) + (e.text && e.text.length > 50 ? '...' : '') || 'DJ'
    case 'news':
      return e.text?.slice(0, 50) + (e.text && e.text.length > 50 ? '...' : '') || 'Новости'
    case 'weather':
      return e.text?.slice(0, 50) + (e.text && e.text.length > 50 ? '...' : '') || 'Погода'
    case 'podcast':
      return e.file?.split('/').pop() || 'Подкаст'
    case 'intro':
      return e.file?.split('/').pop() || 'Интро'
    default:
      return e.type
  }
}

export default function AdminPage() {
  const [selectedDate, setSelectedDate] = useState(format(new Date(), 'yyyy-MM-dd'))
  const [playlist, setPlaylist] = useState<Playlist | null>(null)
  const [loading, setLoading] = useState(false)
  const [confirmOverwrite, setConfirmOverwrite] = useState(false)
  const [pendingGenerate, setPendingGenerate] = useState(false)
  const [selectedIndices, setSelectedIndices] = useState<Set<number>>(new Set())
  const [editingIndex, setEditingIndex] = useState<number | null>(null)
  const [editText, setEditText] = useState('')
  const tableRef = useRef<HTMLDivElement>(null)
  const { toast } = useToast()

  const handleReorder = async (fromIndex: number, direction: 'up' | 'down') => {
    if (!playlist) return
    const toIndex = direction === 'up' ? fromIndex - 1 : fromIndex + 1
    if (toIndex < 0 || toIndex >= playlist.entities.length) return
    const entities = [...playlist.entities]
    ;[entities[fromIndex], entities[toIndex]] = [entities[toIndex], entities[fromIndex]]
    try {
      const res = await fetch(`${API_BASE}/api/playlists/${selectedDate}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ entities }),
      })
      if (res.ok) {
        const timings = computeTimings(entities)
        setPlaylist((p) => (p ? { ...p, entities, timings } : null))
        toast({ title: 'Порядок изменён' })
      }
    } catch {
      toast({ title: 'Ошибка', variant: 'destructive' })
    }
  }

  const fetchPlaylist = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/playlists/${selectedDate}`)
      if (res.ok) {
        const data = await res.json()
        setPlaylist(data)
        if (data.entities?.length > 0) {
          setTimeout(() => tableRef.current?.scrollIntoView({ behavior: 'smooth' }), 100)
        }
      } else {
        setPlaylist(null)
      }
    } catch {
      setPlaylist(null)
      toast({ title: 'Ошибка', description: 'API недоступен. Запустите: cd backend && python -m uvicorn api_main:app --port 8001', variant: 'destructive' })
    } finally {
      setLoading(false)
    }
  }, [selectedDate, toast])

  useEffect(() => {
    fetchPlaylist()
  }, [fetchPlaylist])

  const handleGenerate = async (overwrite: boolean, quick = false) => {
    setLoading(true)
    toast({ title: 'Генерация...', description: quick ? 'Быстрый тест (1 час)' : 'Может занять 5–10 минут' })
    try {
      const url = `${API_BASE}/api/playlists/${selectedDate}/generate?overwrite=${overwrite}${quick ? '&hours=1' : ''}`
      const res = await fetch(url, { method: 'POST' })
      if (res.ok) {
        const data = await res.json()
        const count = data.entitiesCount ?? 0
        toast({
          title: count > 0 ? 'Готово' : 'Пустой результат',
          description: count > 0
            ? `Сгенерировано ${count} сущностей`
            : 'Добавьте jingles/jingle.mp3 и проверьте JAMENDO_CLIENT_ID в .env',
        })
        fetchPlaylist()
      } else {
        const err = await res.json().catch(() => ({}))
        if (res.status === 409) {
          setPendingGenerate(true)
          toast({ title: 'Плейлист уже существует', description: 'Подтвердите перезапись в диалоге' })
        } else {
          toast({ title: 'Ошибка', description: err.detail || 'Ошибка генерации', variant: 'destructive' })
        }
      }
    } catch (e) {
      toast({ title: 'Ошибка', description: String(e) || 'Не удалось сгенерировать', variant: 'destructive' })
    } finally {
      setLoading(false)
    }
  }

  const handleVoice = async (indices?: number[]) => {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/playlists/${selectedDate}/voice`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ indices: indices ?? [] }),
      })
      if (res.ok) {
        const data = await res.json()
        toast({ title: 'Готово', description: `Озвучено: ${data.voiced}` })
        fetchPlaylist()
      } else {
        toast({ title: 'Ошибка', description: 'Ошибка озвучки', variant: 'destructive' })
      }
    } catch {
      toast({ title: 'Ошибка', description: 'Не удалось озвучить', variant: 'destructive' })
    } finally {
      setLoading(false)
    }
  }

  const handleSaveText = async (index: number, text: string) => {
    if (!playlist) return
    try {
      const res = await fetch(`${API_BASE}/api/playlists/${selectedDate}/entities/${index}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })
      if (res.ok) {
        setPlaylist((p) =>
          p
            ? {
                ...p,
                entities: p.entities.map((e, i) => (i === index ? { ...e, text } : e)),
              }
            : null
        )
        setEditingIndex(null)
        toast({ title: 'Сохранено' })
      }
    } catch {
      toast({ title: 'Ошибка', variant: 'destructive' })
    }
  }

  const toggleSelect = (i: number) => {
    setSelectedIndices((prev) => {
      const next = new Set(prev)
      if (next.has(i)) next.delete(i)
      else next.add(i)
      return next
    })
  }

  const selectAllTextEntities = () => {
    if (!playlist) return
    const indices = new Set<number>()
    playlist.entities.forEach((e, i) => {
      if (['dj', 'news', 'weather'].includes(e.type) && e.text?.trim()) indices.add(i)
    })
    setSelectedIndices(indices)
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">NAVO RADIO — Админка</h1>
          <a
            href="/"
            className="text-sm text-zinc-400 hover:text-zinc-200"
          >
            ← На главную
          </a>
        </div>

        <div className="flex flex-wrap gap-4 items-center">
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSelectedDate(format(subDays(new Date(selectedDate), 1), 'yyyy-MM-dd'))}
            >
              ←
            </Button>
            <Input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="w-40 bg-zinc-900 border-zinc-700"
            />
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSelectedDate(format(addDays(new Date(selectedDate), 1), 'yyyy-MM-dd'))}
            >
              →
            </Button>
          </div>
          <Button
            variant="outline"
            onClick={async () => {
              try {
                const res = await fetch(`${API_BASE}/api/test-stream`, { method: 'POST' })
                if (res.ok) {
                  toast({ title: 'Тестовый стрим запущен', description: '2 мин тишины на http://localhost:8000/stream' })
                }
              } catch {
                toast({ title: 'Ошибка', variant: 'destructive' })
              }
            }}
          >
            Тестовый стрим (2 мин)
          </Button>
          <Button
            onClick={() => handleGenerate(false)}
            disabled={loading}
          >
            Сгенерировать эфир на день
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => fetchPlaylist()}
            disabled={loading}
          >
            Обновить
          </Button>
          <Button
            variant="outline"
            onClick={() => handleGenerate(true, true)}
            disabled={loading}
            title="Только 1 час — для быстрой проверки"
          >
            Быстрый тест (1 час)
          </Button>
          {playlist && (
            <Button
              variant="outline"
              onClick={() => handleGenerate(true)}
              disabled={loading}
            >
              Перезаписать эфир
            </Button>
          )}
          {playlist && playlist.entities.length > 0 && (
            <>
              <Button
                variant="secondary"
                onClick={() => handleVoice()}
                disabled={loading}
              >
                Озвучить эфир
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={selectAllTextEntities}
              >
                Выбрать все текстовые
              </Button>
              <Button
                variant="secondary"
                onClick={() => handleVoice(Array.from(selectedIndices))}
                disabled={loading || selectedIndices.size === 0}
              >
                Озвучить выбранное ({selectedIndices.size})
              </Button>
            </>
          )}
        </div>

        {loading && (
          <div className="rounded-lg bg-amber-950/50 border border-amber-700/50 p-4 text-amber-200">
            Генерация идёт... Подождите, это может занять несколько минут.
          </div>
        )}
        {!loading && (!playlist || playlist.entities.length === 0) && (
          <p className="text-zinc-400">
            {playlist ? 'Плейлист на выбранный день пуст. ' : ''}
            Нажмите «Сгенерировать эфир на день».
          </p>
        )}

        {playlist && playlist.entities.length > 0 && (
          <div ref={tableRef} className="border border-zinc-700 rounded-lg overflow-hidden">
            <div className="px-4 py-2 bg-zinc-900/80 border-b border-zinc-700 text-sm text-zinc-400">
              Расписание эфира — {playlist.entities.length} сущностей
            </div>
            <Table>
              <TableHeader>
                <TableRow className="border-zinc-700 hover:bg-transparent">
                    <TableHead className="w-16 text-zinc-400">#</TableHead>
                  <TableHead className="w-16 text-zinc-400"></TableHead>
                  <TableHead className="w-24 text-zinc-400">Тайминг</TableHead>
                  <TableHead className="w-24 text-zinc-400">Тип</TableHead>
                  <TableHead className="text-zinc-400">Содержимое</TableHead>
                  <TableHead className="w-20 text-zinc-400">Готово</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {playlist.entities.map((entity, i) => (
                  <TableRow
                    key={i}
                    className={`border-zinc-700 ${
                      entityIsReady(entity)
                        ? 'bg-emerald-950/30 border-l-4 border-l-emerald-600'
                        : 'hover:bg-zinc-900/50'
                    }`}
                  >
                    <TableCell className="font-mono text-sm text-zinc-500">{i + 1}</TableCell>
                    <TableCell className="space-x-1">
                      {['dj', 'news', 'weather'].includes(entity.type) && entity.text?.trim() && (
                        <input
                          type="checkbox"
                          checked={selectedIndices.has(i)}
                          onChange={() => toggleSelect(i)}
                          className="mr-1"
                        />
                      )}
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6"
                        onClick={() => handleReorder(i, 'up')}
                        disabled={i === 0}
                      >
                        ↑
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6"
                        onClick={() => handleReorder(i, 'down')}
                        disabled={i === playlist.entities.length - 1}
                      >
                        ↓
                      </Button>
                    </TableCell>
                    <TableCell className="font-mono text-sm text-zinc-400">
                      {playlist.timings[i] ?? '—'}
                    </TableCell>
                    <TableCell>
                      <span className="px-2 py-0.5 rounded text-xs bg-zinc-800 text-zinc-300">
                        {entity.type}
                      </span>
                    </TableCell>
                    <TableCell>
                      {editingIndex === i ? (
                        <div className="space-y-2">
                          <Textarea
                            value={editText}
                            onChange={(e) => setEditText(e.target.value)}
                            className="min-h-20 bg-zinc-900 border-zinc-700"
                          />
                          <div className="flex gap-2">
                            <Button size="sm" onClick={() => handleSaveText(i, editText)}>
                              Сохранить
                            </Button>
                            <Button size="sm" variant="outline" onClick={() => setEditingIndex(null)}>
                              Отмена
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <div
                          className="cursor-pointer hover:bg-zinc-800/50 rounded px-1 -mx-1"
                          onClick={() => {
                            if (['dj', 'news', 'weather'].includes(entity.type) && entity.text) {
                              setEditingIndex(i)
                              setEditText(entity.text)
                            }
                          }}
                        >
                          {entityLabel(entity)}
                        </div>
                      )}
                    </TableCell>
                    <TableCell>
                      {entityIsReady(entity) ? (
                        <span className="text-emerald-400 text-sm">✓</span>
                      ) : (
                        <span className="text-zinc-500 text-sm">—</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>

      <AlertDialog open={pendingGenerate} onOpenChange={setPendingGenerate}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Плейлист уже существует</AlertDialogTitle>
            <AlertDialogDescription>
              Перезаписать плейлист на {format(new Date(selectedDate), 'd MMMM yyyy', { locale: ru })}?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                handleGenerate(true)
                setPendingGenerate(false)
              }}
            >
              Перезаписать
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
