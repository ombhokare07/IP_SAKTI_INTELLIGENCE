'use client';

import { useEffect, useRef, useState } from 'react';
import { LoaderCircle, Mic, Square, Upload } from 'lucide-react';
import { api, fileBase64 } from '@/services/api';

const supportedAudioTypes = new Set(['audio/webm', 'audio/wav', 'audio/mpeg', 'audio/ogg']);

function uploadMime(file: File) {
  const declared = file.type.split(';')[0];
  if (supportedAudioTypes.has(declared)) return declared;
  const extension = file.name.toLowerCase().split('.').pop();
  return extension === 'wav' ? 'audio/wav'
    : extension === 'mp3' || extension === 'mpeg' ? 'audio/mpeg'
      : extension === 'ogg' ? 'audio/ogg'
        : 'audio/webm';
}

export default function VoiceInput({ language, onTranscript }: { language: string; onTranscript: (text: string) => void }) {
  const [busy, setBusy] = useState(false);
  const [recording, setRecording] = useState(false);
  const [message, setMessage] = useState('');
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const stopTracks = () => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  };

  useEffect(() => () => {
    const recorder = recorderRef.current;
    if (recorder && recorder.state !== 'inactive') {
      recorder.onstop = null;
      recorder.stop();
    }
    stopTracks();
  }, []);

  const transcribe = async (blob: Blob, mimeType: string) => {
    if (!blob.size) {
      setMessage('No audio was captured. Type your question or try recording again.');
      return;
    }
    if (blob.size > 5_000_000) {
      setMessage('Voice recordings are limited to 5 MB. Try a shorter recording.');
      return;
    }
    setBusy(true);
    setMessage('');
    try {
      const file = new File([blob], 'voice-question', { type: mimeType });
      const response: any = await api('/voice/transcribe', {
        audio_base64: await fileBase64(file),
        language,
        mime_type: mimeType,
      });
      if (response.transcript) onTranscript(response.transcript);
      setMessage(response.message || (response.transcript ? 'Transcript added to your question.' : response.status));
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : 'Speech transcription is unavailable.');
    } finally {
      setBusy(false);
    }
  };

  const startRecording = async () => {
    if (busy || recording) return;
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      setMessage('Live recording is not supported in this browser. Upload an audio file or type your question.');
      return;
    }
    setMessage('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      chunksRef.current = [];
      const preferred = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus'].find((type) => MediaRecorder.isTypeSupported(type));
      const recorder = new MediaRecorder(stream, preferred ? { mimeType: preferred } : undefined);
      recorderRef.current = recorder;
      recorder.ondataavailable = (event) => { if (event.data.size) chunksRef.current.push(event.data); };
      recorder.onerror = () => {
        setMessage('Recording failed. Upload an audio file or type your question.');
        setRecording(false);
        stopTracks();
      };
      recorder.onstop = () => {
        const mimeType = recorder.mimeType.split(';')[0] || 'audio/webm';
        const audio = new Blob(chunksRef.current, { type: mimeType });
        recorderRef.current = null;
        setRecording(false);
        stopTracks();
        void transcribe(audio, supportedAudioTypes.has(mimeType) ? mimeType : 'audio/webm');
      };
      recorder.start();
      setRecording(true);
      setMessage('Recording… select Stop when your question is complete.');
    } catch {
      stopTracks();
      setMessage('Microphone access was not available. Upload an audio file or type your question.');
    }
  };

  const stopRecording = () => {
    if (recorderRef.current?.state !== 'inactive') recorderRef.current?.stop();
  };

  return <div className="voice-input">
    <div className="voice-actions">
      <button className={`button ghost small${recording ? ' recording' : ''}`} type="button" disabled={busy} onClick={recording ? stopRecording : startRecording}>
        {recording ? <><Square size={14} />Stop recording</> : busy ? <><LoaderCircle className="spin" size={14} />Transcribing…</> : <><Mic size={14} />Microphone</>}
      </button>
      <label className="button ghost small"><Upload size={14} />Upload audio<input type="file" accept="audio/wav,audio/mpeg,audio/ogg,audio/webm" disabled={busy || recording} onChange={async (event) => {
        const file = event.target.files?.[0];
        if (!file) return;
        await transcribe(file, uploadMime(file));
        event.target.value = '';
      }} /></label>
    </div>
    <small role="status" aria-live="polite">{message || 'Voice uses the configured speech provider. Typing is always available.'}</small>
  </div>;
}
