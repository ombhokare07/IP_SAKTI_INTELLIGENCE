"""Local faster-whisper adapter for IP-SAKTI."""
import base64
import os
import tempfile
import threading

from services.provider_gateway import ProviderUnavailable


class LocalWhisperGateway:
    configured = True

    MIME_SUFFIX = {
        "audio/wav": ".wav",
        "audio/mpeg": ".mp3",
        "audio/ogg": ".ogg",
        "audio/webm": ".webm",
    }

    def __init__(self):
        self.model_name = os.getenv("IPSAKTI_WHISPER_MODEL", "small")
        self.download_root = os.getenv(
            "IPSAKTI_WHISPER_MODELS",
            r"D:\whisper-models",
        )
        self._model = None
        self._lock = threading.Lock()

    def _load(self):
        if self._model is not None:
            return

        with self._lock:
            if self._model is not None:
                return

            try:
                from faster_whisper import WhisperModel

                self._model = WhisperModel(
                    self.model_name,
                    device="cpu",
                    compute_type="int8",
                    download_root=self.download_root,
                )
            except Exception as exc:
                raise ProviderUnavailable(
                    "local_stt_model_unavailable"
                ) from exc

    def call(self, payload):
        if payload.get("operation") != "transcribe":
            raise ProviderUnavailable("unsupported_operation")

        audio_b64 = payload.get("audio_base64")
        language = payload.get("language")
        mime_type = payload.get("mime_type")

        if language not in {"en", "hi", "mr"}:
            raise ProviderUnavailable("unsupported_language")

        if mime_type not in self.MIME_SUFFIX:
            raise ProviderUnavailable("unsupported_audio_format")

        try:
            audio = base64.b64decode(audio_b64, validate=True)
        except Exception as exc:
            raise ProviderUnavailable("invalid_audio") from exc

        if not audio:
            raise ProviderUnavailable("invalid_audio")

        self._load()

        path = None

        try:
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=self.MIME_SUFFIX[mime_type],
            ) as f:
                f.write(audio)
                path = f.name

            segments, info = self._model.transcribe(
                path,
                language=language,
                beam_size=5,
                vad_filter=True,
            )

            transcript = " ".join(
                x.text.strip()
                for x in segments
                if x.text.strip()
            ).strip()

            if not transcript:
                raise ProviderUnavailable("empty_transcript")

            return {
                "transcript": transcript,
                "language": language,
            }

        except ProviderUnavailable:
            raise
        except Exception as exc:
            raise ProviderUnavailable("local_stt_failed") from exc

        finally:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
