export type STTAlt = { transcript: string; confidence?: number };

export default class GoogleStreamingProvider {
  private ws: WebSocket | null = null;
  private listening = false;
  private onResultCb?: (final: boolean, alts: STTAlt[]) => void;
  private onErrorCb?: (err: { code: string; message?: string }) => void;
  private media: MediaStream | null = null;
  private processor?: ScriptProcessorNode;
  private audioCtx?: AudioContext;

  onResult(cb: (final: boolean, alts: STTAlt[]) => void) { this.onResultCb = cb; }
  onError(cb: (err: { code: string; message?: string }) => void) { this.onErrorCb = cb; }
  isListening() { return this.listening; }

  async start() {
    if (this.listening) return;
    this.listening = true;
    try {
      const url = import.meta.env.VITE_STT_WS_URL as string;
      if (!url) throw new Error('VITE_STT_WS_URL is not set');
      this.ws = new WebSocket(url);
      this.ws.binaryType = 'arraybuffer';
      this.ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(String(e.data));
          if (msg.type === 'result' && this.onResultCb) {
            const alts: STTAlt[] = Array.isArray(msg.alternatives) ? msg.alternatives : [];
            this.onResultCb(!!msg.final, alts);
          } else if (msg.type === 'error' && this.onErrorCb) {
            this.onErrorCb({ code: 'remote', message: msg.error });
          }
        } catch {
          /* no-op */
        }
      };
      this.ws.onerror = () => this.onErrorCb?.({ code: 'ws_error' });
      await this.initMic();
    } catch (e: any) {
      this.onErrorCb?.({ code: 'start_failed', message: e?.message });
      this.listening = false;
    }
  }

  stop() {
    this.listening = false;
    try { this.processor?.disconnect(); } catch {}
    try { this.audioCtx?.close(); } catch {}
    try { this.media?.getTracks().forEach(t => t.stop()); } catch {}
    try { this.ws?.close(); } catch {}
    this.ws = null;
  }

  private async initMic() {
    this.audioCtx = new AudioContext({ sampleRate: 16000 });
    this.media = await navigator.mediaDevices.getUserMedia({ audio: true });
    const src = this.audioCtx.createMediaStreamSource(this.media);
    this.processor = this.audioCtx.createScriptProcessor(4096, 1, 1);
    src.connect(this.processor);
    this.processor.connect(this.audioCtx.destination);
    this.processor.onaudioprocess = (e) => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
      const input = e.inputBuffer.getChannelData(0);
      const buf = new ArrayBuffer(input.length * 2);
      const view = new DataView(buf);
      for (let i = 0; i < input.length; i++) {
        let s = Math.max(-1, Math.min(1, input[i]));
        view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
      }
      try { this.ws.send(buf); } catch { /* no-op */ }
    };
  }
}


