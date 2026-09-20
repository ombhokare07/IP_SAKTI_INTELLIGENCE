"""Edge TTS adapter for IP-SAKTI."""
import base64
import os
import tempfile

from services.provider_gateway import ProviderUnavailable


class EdgeTTSGateway:
    configured = True

    VOICES = {
        "en": "en-IN-NeerjaNeural",
        "hi": "hi-IN-SwaraNeural",
        "mr": "mr-IN-AarohiNeural",
    }

    def call(self, payload):
        if payload.get("operation") != "synthesize":
            raise ProviderUnavailable("unsupported_operation")

        text = payload.get("text")
        language = payload.get("language")

        if not isinstance(text, str) or not text.strip():
            raise ProviderUnavailable("invalid_text")

        if language not in self.VOICES:
            raise ProviderUnavailable("unsupported_language")

        path = None

        try:
            import edge_tts

            fd, path = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)

            communicate = edge_tts.Communicate(
                text,
                self.VOICES[language],
            )

            communicate.save_sync(path)

            with open(path, "rb") as f:
                audio = f.read()

            if not audio:
                raise ProviderUnavailable("empty_audio")

            return {
                "audio_base64": base64.b64encode(audio).decode("ascii"),
                "mime_type": "audio/mpeg",
                "language": language,
            }

        except ProviderUnavailable:
            raise
        except Exception as exc:
            raise ProviderUnavailable("edge_tts_failed") from exc

        finally:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
