"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { withAuthQuery } from "@/lib/auth";

interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  quizType?: "question" | "feedback";
  flashcardId?: number;
  note?: number;
}

interface OllamaModel {
  name: string;
  size: string;
}

interface VocalChatProps {
  onClose?: () => void;
}

function ProfessorAvatar() {
  return (
    <div className="w-9 h-9 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shrink-0 shadow-lg shadow-violet-900/30 ring-2 ring-violet-500/20">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="8" r="4" stroke="white" strokeWidth="1.5" />
        <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
        <rect x="8" y="1" width="8" height="3" rx="1.5" stroke="white" strokeWidth="1" opacity="0.6" />
      </svg>
    </div>
  );
}

function UserAvatar() {
  return (
    <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center shrink-0 shadow-lg shadow-blue-900/30 ring-2 ring-blue-500/20">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="8" r="4" stroke="white" strokeWidth="1.5" />
        <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    </div>
  );
}

function ThinkingDots() {
  return (
    <div className="flex items-center gap-1.5 px-2 py-1">
      <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: "0ms", animationDuration: "0.8s" }} />
      <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: "150ms", animationDuration: "0.8s" }} />
      <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: "300ms", animationDuration: "0.8s" }} />
    </div>
  );
}

function SoundWave() {
  return (
    <div className="flex items-center gap-0.5 h-5">
      {[1, 2, 3, 4, 5].map((i) => (
        <div
          key={i}
          className="w-1 bg-red-400 rounded-full animate-pulse"
          style={{
            height: `${8 + Math.sin(i * 1.2) * 8}px`,
            animationDelay: `${i * 100}ms`,
            animationDuration: "0.6s",
          }}
        />
      ))}
    </div>
  );
}

function MicIcon({ className }: { className?: string }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" className={className}>
      <rect x="9" y="2" width="6" height="11" rx="3" stroke="currentColor" strokeWidth="1.5" />
      <path d="M5 11a7 7 0 0 0 14 0" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="12" y1="18" x2="12" y2="22" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <path d="M22 2L11 13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
    </svg>
  );
}

function formatTime(date: Date) {
  return date.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
}

export default function VocalChat({ onClose }: VocalChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [quizMode, setQuizMode] = useState(false);
  const [availableModels, setAvailableModels] = useState<OllamaModel[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [waitingHint, setWaitingHint] = useState(false);

  // Streaming state
  const [streamingText, setStreamingText] = useState<string>("");
  const [isStreaming, setIsStreaming] = useState(false);
  const audioQueueRef = useRef<{ data: string; index: number }[]>([]);
  const isPlayingAudioRef = useRef(false);

  // Web Speech API
  const [useBrowserSTT] = useState(true);
  const recognitionRef = useRef<any>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const retriesRef = useRef(0);
  const waitingTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const maxRetries = 5;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages, streamingText]);

  const mountedRef = useRef(true);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const addMessage = useCallback((role: Message["role"], content: string) => {
    setMessages((prev) => [...prev, { role, content, timestamp: new Date() }]);
  }, []);

  // Sequential audio queue player
  const playNextAudio = useCallback(() => {
    if (isPlayingAudioRef.current || audioQueueRef.current.length === 0) return;
    isPlayingAudioRef.current = true;
    const chunk = audioQueueRef.current.shift()!;
    const audio = new Audio(`data:audio/wav;base64,${chunk.data}`);
    audio.onended = () => {
      isPlayingAudioRef.current = false;
      playNextAudio();
    };
    audio.onerror = () => {
      isPlayingAudioRef.current = false;
      playNextAudio();
    };
    audio.play().catch(() => {
      isPlayingAudioRef.current = false;
      playNextAudio();
    });
  }, []);

  const connect = useCallback((modelOverride?: string) => {
    if (!mountedRef.current) return;
    if (wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) return;

    const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
    const base = withAuthQuery(`${wsProtocol}://${window.location.hostname}:8000/api/vocal/ws`);
    const wsUrl = new URL(base);
    const model = modelOverride || selectedModel;
    if (model) {
      wsUrl.searchParams.set("model", model);
    }
    const ws = new WebSocket(wsUrl.toString());

    ws.onopen = () => {
      if (!mountedRef.current) { ws.close(); return; }
      setIsConnected(true);
      setIsReconnecting(false);
      retriesRef.current = 0;
    };

    ws.onclose = (event) => {
      if (!mountedRef.current) return;
      setIsConnected(false);
      setIsLoading(false);
      setIsStreaming(false);
      setStreamingText("");
      if (event.code !== 1000 && retriesRef.current < maxRetries) {
        retriesRef.current++;
        setIsReconnecting(true);
        reconnectTimerRef.current = setTimeout(() => {
          if (mountedRef.current) connect();
        }, 2000);
      } else if (retriesRef.current >= maxRetries) {
        setIsReconnecting(false);
        addMessage("system", "Connexion perdue. Rechargez la page pour réessayer.");
      }
    };

    ws.onerror = () => {};

    ws.onmessage = (event) => {
      if (!mountedRef.current) return;
      const data = JSON.parse(event.data);

      // --- Nouveaux messages streaming ---
      if (data.type === "text_chunk") {
        setStreamingText((prev) => prev + data.token);
        setIsStreaming(true);
        setIsLoading(false);

      } else if (data.type === "text_done") {
        addMessage("assistant", data.message);
        setStreamingText("");
        setIsStreaming(false);
        setWaitingHint(false);
        if (waitingTimerRef.current) clearTimeout(waitingTimerRef.current);
        waitingTimerRef.current = setTimeout(() => {
          if (mountedRef.current) setWaitingHint(true);
        }, 5000);
        setTimeout(() => inputRef.current?.focus(), 100);

      } else if (data.type === "audio_chunk") {
        audioQueueRef.current.push({ data: data.data, index: data.index });
        audioQueueRef.current.sort((a, b) => a.index - b.index);
        playNextAudio();

      } else if (data.type === "audio_done") {
        // Fin de stream audio — rien de spécial à faire

      // --- Anciens messages (compatibilité) ---
      } else if (data.type === "transcription") {
        addMessage("user", data.message);
      } else if (data.type === "text") {
        addMessage("assistant", data.message);
        setIsLoading(false);
        setWaitingHint(false);
        if (waitingTimerRef.current) clearTimeout(waitingTimerRef.current);
        waitingTimerRef.current = setTimeout(() => {
          if (mountedRef.current) setWaitingHint(true);
        }, 5000);
        setTimeout(() => inputRef.current?.focus(), 100);
      } else if (data.type === "audio") {
        const audio = new Audio(`data:audio/wav;base64,${data.data}`);
        audio.play().catch(() => {});
      } else if (data.type === "error") {
        addMessage("system", data.message);
        setIsLoading(false);
        setIsStreaming(false);
        setStreamingText("");
      } else if (data.type === "quiz_question") {
        setMessages((prev) => [...prev, {
          role: "assistant",
          content: data.question,
          timestamp: new Date(),
          quizType: "question",
          flashcardId: data.flashcard_id,
        }]);
        setIsLoading(false);
      } else if (data.type === "quiz_feedback") {
        setMessages((prev) => [...prev, {
          role: "assistant",
          content: data.feedback,
          timestamp: new Date(),
          quizType: "feedback",
          note: data.note,
        }]);
        setIsLoading(false);
      } else if (data.type === "ping") {
        ws.send(JSON.stringify({ type: "pong" }));
      }
    };

    wsRef.current = ws;
  }, [addMessage, playNextAudio, selectedModel]);

  useEffect(() => {
    fetch("/api/vocal/models")
      .then((r) => r.ok ? r.json() : null)
      .then((data) => {
        if (data?.models?.length) {
          setAvailableModels(data.models);
          setSelectedModel(data.active || data.models[0].name);
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (waitingTimerRef.current) clearTimeout(waitingTimerRef.current);
      recognitionRef.current?.stop();
      if (wsRef.current) {
        wsRef.current.close(1000);
        wsRef.current = null;
      }
    };
  }, [connect]);

  const toggleQuizMode = () => {
    const newMode = !quizMode;
    setQuizMode(newMode);
    if (newMode && wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "start_quiz" }));
      setIsLoading(true);
    }
  };

  const switchModel = (newModel: string) => {
    setSelectedModel(newModel);
    setMessages([]);
    setStreamingText("");
    setIsStreaming(false);
    if (wsRef.current) {
      wsRef.current.close(1000);
      wsRef.current = null;
    }
    retriesRef.current = 0;
    setTimeout(() => connect(newModel), 300);
  };

  // --- Web Speech API STT ---
  const startBrowserSTT = useCallback(() => {
    setWaitingHint(false);
    if (waitingTimerRef.current) clearTimeout(waitingTimerRef.current);

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      // Fallback sur MediaRecorder + Whisper
      startRecording();
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "fr-FR";
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onresult = (event: any) => {
      let finalTranscript = "";
      let interimTranscript = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }
      if (finalTranscript) {
        addMessage("user", finalTranscript);
        wsRef.current?.send(JSON.stringify({ type: "text", message: finalTranscript }));
        setIsLoading(true);
        setInputText("");
      }
      if (interimTranscript) {
        setInputText(interimTranscript);
      }
    };

    recognition.onerror = (event: any) => {
      if (event.error !== "no-speech") {
        console.error("Speech recognition error:", event.error);
      }
      setIsRecording(false);
    };

    recognition.onend = () => {
      setIsRecording(false);
    };

    recognition.start();
    recognitionRef.current = recognition;
    setIsRecording(true);
  }, [addMessage]);

  const stopBrowserSTT = useCallback(() => {
    recognitionRef.current?.stop();
    setIsRecording(false);
  }, []);

  // --- MediaRecorder fallback (Whisper) ---
  const startRecording = async () => {
    setWaitingHint(false);
    if (waitingTimerRef.current) clearTimeout(waitingTimerRef.current);
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const recorder = new MediaRecorder(stream);
    audioChunksRef.current = [];
    recorder.ondataavailable = (e) => audioChunksRef.current.push(e.data);
    recorder.onstop = async () => {
      const blob = new Blob(audioChunksRef.current, { type: "audio/wav" });
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64 = (reader.result as string).split(",")[1];
        wsRef.current?.send(JSON.stringify({ type: "audio", data: base64 }));
        setIsLoading(true);
      };
      reader.readAsDataURL(blob);
      stream.getTracks().forEach((t) => t.stop());
    };
    recorder.start();
    mediaRecorderRef.current = recorder;
    setIsRecording(true);
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
  };

  const handleMicClick = () => {
    if (isRecording) {
      if (useBrowserSTT && recognitionRef.current) {
        stopBrowserSTT();
      } else {
        stopRecording();
      }
    } else {
      startBrowserSTT();
    }
  };

  const sendText = () => {
    if (!inputText.trim() || !wsRef.current) return;
    setWaitingHint(false);
    if (waitingTimerRef.current) clearTimeout(waitingTimerRef.current);
    addMessage("user", inputText);
    wsRef.current.send(JSON.stringify({ type: "text", message: inputText }));
    setInputText("");
    setIsLoading(true);
  };

  return (
    <div className="flex flex-col h-full bg-slate-900 rounded-2xl border border-slate-700/80 shadow-2xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-700/80 bg-slate-800/60 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <ProfessorAvatar />
          <div>
            <h2 className="text-sm font-semibold text-white leading-tight">Prof Vocal IA</h2>
            <span className="text-xs text-slate-400 flex items-center gap-1.5">
              {isConnected && messages.length > 0 ? (
                <>
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  Conversation en cours
                </>
              ) : isConnected ? "Connecté" : isReconnecting ? "Reconnexion..." : "Déconnecté"}
            </span>
          </div>
        </div>

        {/* Indicateur connexion + sélecteur modèle */}
        <div className="flex items-center gap-2">
          <button
            onClick={toggleQuizMode}
            disabled={!isConnected}
            title={quizMode ? "Désactiver le mode révision" : "Activer le mode révision"}
            className={`flex items-center gap-1.5 text-xs font-medium px-2.5 py-1.5 rounded-lg transition-all disabled:opacity-40 ${
              quizMode
                ? "bg-violet-600/30 text-violet-300 border border-violet-500/40"
                : "bg-slate-700/50 text-slate-400 border border-slate-600/40 hover:text-violet-300 hover:border-violet-500/30"
            }`}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
              <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="1.5" />
              <line x1="3" y1="12" x2="21" y2="12" stroke="currentColor" strokeWidth="1.5" />
              <path d="M8 7h8M8 17h8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
            Révision
          </button>
          {availableModels.length > 1 && (
            <select
              value={selectedModel}
              onChange={(e) => switchModel(e.target.value)}
              className="text-xs bg-slate-700/80 text-slate-300 border border-slate-600/60 rounded-lg px-2 py-1 focus:outline-none focus:border-violet-500/60 cursor-pointer"
              title="Changer de modèle IA"
            >
              {availableModels.map((m) => (
                <option key={m.name} value={m.name}>
                  {m.name} ({m.size})
                </option>
              ))}
            </select>
          )}
          <div className="flex items-center gap-1.5">
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                isConnected
                  ? "bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.6)]"
                  : isReconnecting
                  ? "bg-yellow-400 animate-pulse"
                  : "bg-red-500"
              }`}
            />
            <span className={`text-xs font-medium ${
              isConnected ? "text-emerald-400" : isReconnecting ? "text-yellow-400" : "text-red-400"
            }`}>
              {isConnected ? "En ligne" : isReconnecting ? "..." : "Hors ligne"}
            </span>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white transition-colors p-1.5 rounded-lg hover:bg-slate-700"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        {messages.length === 0 && !isStreaming && (
          <div className="text-center mt-16 space-y-3">
            <div className="mx-auto w-14 h-14 rounded-full bg-violet-500/15 border border-violet-500/20 flex items-center justify-center">
              <ProfessorAvatar />
            </div>
            <p className="text-slate-400 text-sm">Commencez une conversation avec le professeur</p>
            <p className="text-slate-600 text-xs">Posez une question et le prof vous guidera naturellement</p>
          </div>
        )}
        {messages.map((msg, i) => {
          if (msg.role === "system") {
            return (
              <div key={i} className="flex justify-center">
                <div className="flex items-center gap-2 bg-red-900/30 text-red-300 border border-red-800/40 rounded-xl px-4 py-2 text-sm">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" className="shrink-0">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.5" />
                    <line x1="12" y1="8" x2="12" y2="13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                    <circle cx="12" cy="16.5" r="1" fill="currentColor" />
                  </svg>
                  {msg.content}
                </div>
              </div>
            );
          }

          const isUser = msg.role === "user";

          if (msg.quizType === "question") {
            return (
              <div key={i} className="flex items-end gap-2.5">
                <ProfessorAvatar />
                <div className="max-w-[75%] space-y-1 items-start flex flex-col">
                  <div className="flex items-center gap-1.5 px-1">
                    <span className="badge-amber text-[10px]">RÉVISION</span>
                  </div>
                  <div className="rounded-2xl px-4 py-3 text-sm leading-relaxed border bg-amber-500/10 text-amber-100 border-amber-500/20 rounded-bl-sm">
                    <p className="font-semibold mb-1">{msg.content}</p>
                    <p className="text-xs text-amber-300/60 italic">Répondez à voix haute ou par écrit</p>
                  </div>
                  <span className="text-[10px] text-slate-600 px-1">{formatTime(msg.timestamp)}</span>
                </div>
              </div>
            );
          }

          if (msg.quizType === "feedback") {
            const note = msg.note ?? 0;
            const isGood = note >= 3;
            return (
              <div key={i} className="flex items-end gap-2.5">
                <ProfessorAvatar />
                <div className="max-w-[75%] space-y-1 items-start flex flex-col">
                  <div className="flex items-center gap-1.5 px-1">
                    <span className={isGood ? "badge-green text-[10px]" : "badge-rose text-[10px]"}>
                      {note}/5
                    </span>
                  </div>
                  <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed border rounded-bl-sm ${
                    isGood
                      ? "bg-emerald-500/10 text-emerald-100 border-emerald-500/20"
                      : "bg-rose-500/10 text-rose-100 border-rose-500/20"
                  }`}>
                    {msg.content}
                  </div>
                  <span className="text-[10px] text-slate-600 px-1">{formatTime(msg.timestamp)}</span>
                </div>
              </div>
            );
          }

          return (
            <div key={i} className={`flex items-end gap-2.5 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
              {isUser ? <UserAvatar /> : <ProfessorAvatar />}
              <div className={`max-w-[75%] space-y-1 ${isUser ? "items-end" : "items-start"} flex flex-col`}>
                <div className="text-[10px] font-semibold px-1 text-slate-500 uppercase tracking-wide">
                  {isUser ? "Vous" : "Prof"}
                </div>
                <div
                  className={`rounded-2xl px-4 py-3 text-sm leading-relaxed border ${
                    isUser
                      ? "bg-blue-500/10 text-blue-100 border-blue-500/20 rounded-br-sm"
                      : "bg-violet-500/10 text-violet-100 border-violet-500/20 rounded-bl-sm"
                  }`}
                >
                  {msg.content}
                </div>
                <span className="text-[10px] text-slate-600 px-1">
                  {formatTime(msg.timestamp)}
                </span>
              </div>
            </div>
          );
        })}

        {/* Texte en streaming */}
        {isStreaming && streamingText && (
          <div className="flex items-end gap-2.5">
            <ProfessorAvatar />
            <div className="max-w-[75%] space-y-1 items-start flex flex-col">
              <div className="text-[10px] font-semibold px-1 text-slate-500 uppercase tracking-wide">Prof</div>
              <div className="rounded-2xl px-4 py-3 text-sm leading-relaxed border bg-violet-500/10 text-violet-100 border-violet-500/20 rounded-bl-sm">
                {streamingText}
                <span className="inline-block w-0.5 h-4 bg-violet-400 ml-0.5 animate-pulse" />
              </div>
            </div>
          </div>
        )}

        {isLoading && !isStreaming && (
          <div className="flex items-end gap-2.5">
            <ProfessorAvatar />
            <div className="bg-violet-500/10 border border-violet-500/20 rounded-2xl rounded-bl-sm px-4 py-3">
              <ThinkingDots />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Recording indicator */}
      {isRecording && (
        <div className="flex items-center justify-center gap-3 py-2.5 bg-red-900/25 border-t border-red-800/30 text-red-300 text-sm font-medium">
          <SoundWave />
          <span>Enregistrement en cours…</span>
          <SoundWave />
        </div>
      )}

      {/* Waiting hint */}
      {waitingHint && !isLoading && !isStreaming && isConnected && (
        <div className="flex items-center justify-center gap-2 py-2 bg-violet-900/15 border-t border-violet-800/20 text-violet-300/70 text-xs animate-pulse">
          <span className="w-1.5 h-1.5 rounded-full bg-violet-400/60" />
          Le prof attend votre réponse...
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-slate-700/80 bg-slate-800/30">
        <div className="flex items-center gap-2 bg-slate-800/80 rounded-2xl border border-slate-600/60 focus-within:border-violet-500/60 transition-colors px-4">
          <input
            ref={inputRef}
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendText()}
            placeholder={
              isRecording
                ? "Parlez maintenant…"
                : waitingHint
                ? "Continuez la conversation..."
                : "Posez votre question au professeur..."
            }
            autoFocus
            className="flex-1 bg-transparent text-white py-4 text-sm focus:outline-none placeholder-slate-500"
          />
          <button
            onClick={handleMicClick}
            disabled={!isConnected}
            title={isRecording ? "Arrêter l'enregistrement" : "Enregistrer un message vocal"}
            className={`p-2.5 rounded-xl transition-all disabled:opacity-40 ${
              isRecording
                ? "bg-red-600 text-white hover:bg-red-700 shadow-lg shadow-red-900/40 animate-pulse"
                : "text-slate-400 hover:text-violet-400 hover:bg-violet-500/10"
            }`}
          >
            <MicIcon />
          </button>
          <button
            onClick={sendText}
            disabled={!inputText.trim() || !isConnected}
            title="Envoyer"
            className="p-2.5 rounded-xl text-slate-400 hover:text-blue-400 hover:bg-blue-500/10 transition-all disabled:opacity-40 disabled:hover:text-slate-400 disabled:hover:bg-transparent"
          >
            <SendIcon />
          </button>
        </div>
      </div>
    </div>
  );
}
