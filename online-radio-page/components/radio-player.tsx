"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/* ─── i18n translations ─── */
const translations = {
  en: {
    title: "NAVO RADIO",
    nowPlaying: "Now Playing",
    loading: "Loading...",
    play: "Play",
    pause: "Pause",
    volume: "Volume",
    live: "LIVE",
    langLabel: "Language",
    offline: "Offline",
    connecting: "Connecting...",
  },
  ru: {
    title: "NAVO RADIO",
    nowPlaying: "Сейчас играет",
    loading: "Загрузка...",
    play: "Воспроизвести",
    pause: "Пауза",
    volume: "Громкость",
    live: "ЭФИР",
    langLabel: "Язык",
    offline: "Не в сети",
    connecting: "Подключение...",
  },
  tj: {
    title: "NAVO RADIO",
    nowPlaying: "Ҳоло мешунавед",
    loading: "Боргирӣ...",
    play: "Пахш",
    pause: "Таваққуф",
    volume: "Овоз",
    live: "МУСТАҚИМ",
    langLabel: "Забон",
    offline: "Офлайн",
    connecting: "Пайвастшавӣ...",
  },
} as const;

type Lang = keyof typeof translations;

/* ─── Demo stream URL (replace with your real radio stream) ─── */
const STREAM_URL =
  "https://stream.zeno.fm/0r0xa792kwzuv";

export default function RadioPlayer() {
  const [lang, setLang] = useState<Lang>("ru");
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentSong, setCurrentSong] = useState("");
  const [volume, setVolume] = useState(0.75);
  const [isConnecting, setIsConnecting] = useState(false);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const sourceRef = useRef<MediaElementAudioSourceNode | null>(null);
  const animFrameRef = useRef<number>(0);

  const t = translations[lang];

  /* ─── Setup audio ─── */
  useEffect(() => {
    const audio = new Audio();
    audio.crossOrigin = "anonymous";
    audio.preload = "none";
    audioRef.current = audio;

    return () => {
      audio.pause();
      audio.src = "";
      cancelAnimationFrame(animFrameRef.current);
      if (audioCtxRef.current) {
        audioCtxRef.current.close();
      }
    };
  }, []);

  /* ─── Volume control ─── */
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = volume;
    }
  }, [volume]);

  /* ─── Simulated song title (replace with metadata endpoint) ─── */
  useEffect(() => {
    const songs = [
      "Shahriyor - Modaram",
      "Farrux Xamrayev - Yor-Yor",
      "Manizha - Sabo",
      "Nigina Amonqulova - Oshiq",
      "Sadriddin - Majnun",
      "Talib Tale - Gozlerin",
    ];
    setCurrentSong(songs[0]);
    const interval = setInterval(() => {
      const idx = Math.floor(Math.random() * songs.length);
      setCurrentSong(songs[idx]);
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  /* ─── Equalizer canvas drawing ─── */
  const drawEqualizer = useCallback(() => {
    const canvas = canvasRef.current;
    const analyser = analyserRef.current;
    if (!canvas || !analyser) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const draw = () => {
      animFrameRef.current = requestAnimationFrame(draw);
      analyser.getByteFrequencyData(dataArray);

      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);

      const W = rect.width;
      const H = rect.height;

      ctx.clearRect(0, 0, W, H);

      const barCount = 64;
      const gap = 3;
      const barWidth = (W - gap * (barCount - 1)) / barCount;
      const step = Math.floor(bufferLength / barCount);

      for (let i = 0; i < barCount; i++) {
        const raw = dataArray[i * step] / 255;
        const barHeight = Math.max(raw * H * 0.85, 3);

        /* Purple gradient bar */
        const x = i * (barWidth + gap);
        const y = H - barHeight;

        const gradient = ctx.createLinearGradient(x, H, x, y);
        gradient.addColorStop(0, "hsl(270, 70%, 40%)");
        gradient.addColorStop(0.5, "hsl(270, 80%, 58%)");
        gradient.addColorStop(1, "hsl(280, 90%, 72%)");

        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.roundRect(x, y, barWidth, barHeight, [3, 3, 0, 0]);
        ctx.fill();

        /* Glow effect */
        ctx.shadowColor = "hsl(270, 80%, 58%)";
        ctx.shadowBlur = 8;
        ctx.fill();
        ctx.shadowBlur = 0;
      }
    };

    draw();
  }, []);

  /* ─── Idle equalizer animation (when not playing) ─── */
  const drawIdleEqualizer = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let time = 0;
    const drawIdle = () => {
      animFrameRef.current = requestAnimationFrame(drawIdle);
      time += 0.02;

      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);

      const W = rect.width;
      const H = rect.height;
      ctx.clearRect(0, 0, W, H);

      const barCount = 64;
      const gap = 3;
      const barWidth = (W - gap * (barCount - 1)) / barCount;

      for (let i = 0; i < barCount; i++) {
        const normalized = i / barCount;
        const wave =
          Math.sin(time + normalized * 4) * 0.15 +
          Math.sin(time * 1.5 + normalized * 6) * 0.1 +
          0.08;
        const barHeight = Math.max(wave * H, 3);

        const x = i * (barWidth + gap);
        const y = H - barHeight;

        const gradient = ctx.createLinearGradient(x, H, x, y);
        gradient.addColorStop(0, "hsl(270, 50%, 25%)");
        gradient.addColorStop(1, "hsl(270, 60%, 40%)");

        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.roundRect(x, y, barWidth, barHeight, [3, 3, 0, 0]);
        ctx.fill();
      }
    };
    drawIdle();
  }, []);

  /* ─── Start idle animation on mount ─── */
  useEffect(() => {
    if (!isPlaying) {
      cancelAnimationFrame(animFrameRef.current);
      drawIdleEqualizer();
    }
    return () => cancelAnimationFrame(animFrameRef.current);
  }, [isPlaying, drawIdleEqualizer]);

  /* ─── Play / Pause toggle ─── */
  const togglePlay = async () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
      audio.src = "";
      setIsPlaying(false);
      cancelAnimationFrame(animFrameRef.current);
      drawIdleEqualizer();
      return;
    }

    setIsConnecting(true);

    try {
      audio.src = STREAM_URL;
      audio.load();

      /* Init Web Audio API */
      if (!audioCtxRef.current) {
        const AudioCtx =
          window.AudioContext ||
          (window as unknown as { webkitAudioContext: typeof AudioContext })
            .webkitAudioContext;
        audioCtxRef.current = new AudioCtx();
      }

      if (audioCtxRef.current.state === "suspended") {
        await audioCtxRef.current.resume();
      }

      if (!sourceRef.current) {
        sourceRef.current =
          audioCtxRef.current.createMediaElementSource(audio);
        const analyser = audioCtxRef.current.createAnalyser();
        analyser.fftSize = 256;
        analyser.smoothingTimeConstant = 0.8;
        sourceRef.current.connect(analyser);
        analyser.connect(audioCtxRef.current.destination);
        analyserRef.current = analyser;
      }

      await audio.play();
      setIsPlaying(true);
      setIsConnecting(false);
      cancelAnimationFrame(animFrameRef.current);
      drawEqualizer();
    } catch (err) {
      console.error("[v0] Audio play error:", err);
      setIsConnecting(false);
    }
  };

  /* ─── Status text ─── */
  const statusText = isConnecting
    ? t.connecting
    : isPlaying
      ? t.live
      : t.offline;

  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-background px-4 py-8 selection:bg-primary/30">
      {/* Ambient background glow */}
      <div
        className="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2"
        style={{
          width: 600,
          height: 600,
          borderRadius: "50%",
          background:
            "radial-gradient(circle, hsl(270 70% 60% / 0.08) 0%, transparent 70%)",
          filter: "blur(60px)",
        }}
      />

      {/* Language selector */}
      <div className="absolute right-6 top-6 flex items-center gap-1 rounded-lg border border-border bg-card/60 p-1 backdrop-blur-sm">
        {(["ru", "tj", "en"] as Lang[]).map((l) => (
          <button
            key={l}
            onClick={() => setLang(l)}
            className={`rounded-md px-3 py-1.5 text-xs font-medium uppercase tracking-wider transition-all ${
              lang === l
                ? "bg-primary text-primary-foreground shadow-md shadow-primary/30"
                : "text-muted-foreground hover:text-foreground"
            }`}
            aria-label={`Switch language to ${l}`}
          >
            {l}
          </button>
        ))}
      </div>

      {/* Title */}
      <h1 className="mb-2 text-center text-5xl font-bold tracking-[0.3em] text-primary md:text-6xl lg:text-7xl">
        {t.title}
      </h1>

      {/* Live indicator */}
      <div className="mb-10 flex items-center gap-2">
        <span
          className={`inline-block h-2 w-2 rounded-full ${
            isPlaying
              ? "animate-pulse bg-emerald-400 shadow-lg shadow-emerald-400/50"
              : isConnecting
                ? "animate-pulse bg-amber-400"
                : "bg-muted-foreground/40"
          }`}
        />
        <span className="text-xs font-medium uppercase tracking-widest text-muted-foreground">
          {statusText}
        </span>
      </div>

      {/* Equalizer canvas */}
      <div className="relative w-full max-w-2xl px-4">
        <canvas
          ref={canvasRef}
          className="h-40 w-full md:h-48 lg:h-56"
          style={{ display: "block" }}
        />

        {/* Play button overlay */}
        <button
          onClick={togglePlay}
          disabled={isConnecting}
          className="absolute left-1/2 top-1/2 flex h-16 w-16 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border-2 border-primary/30 bg-card/80 text-primary shadow-2xl shadow-primary/20 backdrop-blur-sm transition-all hover:scale-110 hover:border-primary/60 hover:shadow-primary/40 active:scale-95 disabled:opacity-60 md:h-20 md:w-20"
          aria-label={isPlaying ? t.pause : t.play}
        >
          {isConnecting ? (
            <svg
              className="h-6 w-6 animate-spin"
              viewBox="0 0 24 24"
              fill="none"
            >
              <circle
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="2"
                opacity="0.3"
              />
              <path
                d="M4 12a8 8 0 018-8"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
            </svg>
          ) : isPlaying ? (
            <svg className="h-6 w-6 md:h-7 md:w-7" viewBox="0 0 24 24" fill="currentColor">
              <rect x="6" y="4" width="4" height="16" rx="1" />
              <rect x="14" y="4" width="4" height="16" rx="1" />
            </svg>
          ) : (
            <svg
              className="ml-1 h-6 w-6 md:h-7 md:w-7"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M8 5v14l11-7z" />
            </svg>
          )}
        </button>
      </div>

      {/* Now playing section */}
      <div className="mt-8 flex flex-col items-center gap-2">
        <span className="text-[10px] font-semibold uppercase tracking-[0.25em] text-muted-foreground">
          {t.nowPlaying}
        </span>
        <div className="overflow-hidden">
          <p
            key={currentSong}
            className="animate-fade-in text-balance text-center text-lg font-medium text-foreground md:text-xl"
          >
            {currentSong || t.loading}
          </p>
        </div>
      </div>

      {/* Volume control */}
      <div className="mt-8 flex w-full max-w-xs items-center gap-3">
        {/* Volume off icon */}
        <button
          onClick={() => setVolume(volume > 0 ? 0 : 0.75)}
          className="text-muted-foreground transition-colors hover:text-foreground"
          aria-label={volume === 0 ? "Unmute" : "Mute"}
        >
          {volume === 0 ? (
            <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M11 5L6 9H2v6h4l5 4V5z" />
              <line x1="23" y1="9" x2="17" y2="15" />
              <line x1="17" y1="9" x2="23" y2="15" />
            </svg>
          ) : (
            <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M11 5L6 9H2v6h4l5 4V5z" />
              {volume > 0.3 && <path d="M15.54 8.46a5 5 0 010 7.07" />}
              {volume > 0.6 && <path d="M19.07 4.93a10 10 0 010 14.14" />}
            </svg>
          )}
        </button>

        {/* Volume slider */}
        <div className="relative flex-1">
          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={volume}
            onChange={(e) => setVolume(parseFloat(e.target.value))}
            className="volume-slider w-full"
            aria-label={t.volume}
          />
        </div>
      </div>

      {/* Volume slider custom styles + fade-in animation */}
      <style jsx>{`
        .volume-slider {
          -webkit-appearance: none;
          appearance: none;
          height: 4px;
          border-radius: 2px;
          background: linear-gradient(
            to right,
            hsl(270, 70%, 60%) 0%,
            hsl(270, 70%, 60%) ${volume * 100}%,
            hsl(222, 30%, 18%) ${volume * 100}%,
            hsl(222, 30%, 18%) 100%
          );
          outline: none;
          cursor: pointer;
        }
        .volume-slider::-webkit-slider-thumb {
          -webkit-appearance: none;
          appearance: none;
          width: 14px;
          height: 14px;
          border-radius: 50%;
          background: hsl(270, 70%, 60%);
          box-shadow: 0 0 10px hsl(270, 70%, 60% / 0.5);
          cursor: pointer;
          transition: transform 0.15s;
        }
        .volume-slider::-webkit-slider-thumb:hover {
          transform: scale(1.2);
        }
        .volume-slider::-moz-range-thumb {
          width: 14px;
          height: 14px;
          border: none;
          border-radius: 50%;
          background: hsl(270, 70%, 60%);
          box-shadow: 0 0 10px hsl(270, 70%, 60% / 0.5);
          cursor: pointer;
        }
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(8px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-fade-in {
          animation: fadeIn 0.6s ease-out;
        }
      `}</style>
    </main>
  );
}
