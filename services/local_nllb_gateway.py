"""Local NLLB translation adapter for IP-SAKTI."""
import re
import threading

from services.provider_gateway import ProviderUnavailable


class LocalNLLBGateway:
    configured = True

    LANGS = {
        "en": "eng_Latn",
        "hi": "hin_Deva",
        "mr": "mar_Deva",
    }

    TOKEN_RE = re.compile(r"(IPSAKTI_TOKEN_\d+_END)")

    def __init__(self, model_name="facebook/nllb-200-distilled-600M"):
        self.model_name = model_name
        self._model = None
        self._tokenizers = {}
        self._device = None
        self._lock = threading.Lock()

    def _load(self):
        if self._model is not None:
            return

        with self._lock:
            if self._model is not None:
                return

            try:
                import torch
                from transformers import AutoModelForSeq2SeqLM

                self._device = "cuda" if torch.cuda.is_available() else "cpu"
                dtype = torch.float16 if self._device == "cuda" else torch.float32

                self._model = AutoModelForSeq2SeqLM.from_pretrained(
                    self.model_name,
                    dtype=dtype,
                ).to(self._device)

                self._model.eval()

            except Exception as exc:
                raise ProviderUnavailable("local_translation_model_unavailable") from exc

    def _tokenizer(self, language):
        if language not in self._tokenizers:
            try:
                from transformers import AutoTokenizer

                self._tokenizers[language] = AutoTokenizer.from_pretrained(
                    self.model_name,
                    src_lang=self.LANGS[language],
                )
            except Exception as exc:
                raise ProviderUnavailable("local_translation_tokenizer_unavailable") from exc

        return self._tokenizers[language]

    def _translate_piece(self, text, source, target):
        if not text.strip():
            return text

        import torch

        leading = text[: len(text) - len(text.lstrip())]
        trailing = text[len(text.rstrip()):]
        core = text.strip()

        tokenizer = self._tokenizer(source)

        inputs = tokenizer(
            core,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        ).to(self._device)

        with torch.inference_mode():
            output = self._model.generate(
                **inputs,
                forced_bos_token_id=tokenizer.convert_tokens_to_ids(
                    self.LANGS[target]
                ),
                max_new_tokens=512,
            )

        translated = tokenizer.batch_decode(
            output,
            skip_special_tokens=True,
        )[0]

        return leading + translated + trailing

    def call(self, payload):
        if payload.get("operation") != "translate":
            raise ProviderUnavailable("unsupported_operation")

        text = payload.get("text")
        source = payload.get("source_language")
        target = payload.get("target_language")

        if (
            not isinstance(text, str)
            or source not in self.LANGS
            or target not in self.LANGS
        ):
            raise ProviderUnavailable("provider_malformed_request")

        if source == target:
            return {
                "text": text,
                "target_language": target,
            }

        self._load()

        try:
            parts = self.TOKEN_RE.split(text)
            translated_parts = []

            for part in parts:
                if not part:
                    continue

                if self.TOKEN_RE.fullmatch(part):
                    translated_parts.append(part)
                else:
                    translated_parts.append(
                        self._translate_piece(part, source, target)
                    )

            return {
                "text": "".join(translated_parts),
                "target_language": target,
            }

        except ProviderUnavailable:
            raise
        except Exception as exc:
            raise ProviderUnavailable("local_translation_failed") from exc
