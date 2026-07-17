from __future__ import annotations

import logging
from copy import copy
from typing import Any

from rich.console import Console

from speech_to_speech.pipeline.messages import PartialTranscription, Transcription
from speech_to_speech.STT.whisper_stt_handler import SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)
console = Console()


def resolve_language_code(pred_ids: Any, tokenizer: Any, fallback: str | None) -> str | None:
    """Read Whisper's language token when present, otherwise use the configured language."""
    if pred_ids.ndim >= 2 and pred_ids.shape[1] > 1:
        token_text = tokenizer.decode(pred_ids[0, 1])
        language = token_text.removeprefix("<|").removesuffix("|>")
        if language in SUPPORTED_LANGUAGES:
            return language
    return fallback


def install_whisper_short_output_patch(handler_class: type | None = None) -> None:
    """Prevent short/empty Whisper generations from indexing a missing token."""
    if handler_class is None:
        from speech_to_speech.STT.whisper_stt_handler import WhisperSTTHandler

        handler_class = WhisperSTTHandler

    if hasattr(handler_class, "_project_original_process"):
        return

    handler_class._project_original_process = getattr(handler_class, "process", None)

    def process(self: Any, vad_audio: Any):
        logger.debug("inferring whisper...")
        input_features = self.prepare_model_inputs(vad_audio.audio)
        pred_ids = self.model.generate(input_features, **self.gen_kwargs)
        fallback_language = self.last_language or (
            self.start_language if self.start_language != "auto" else None
        )
        language_code = resolve_language_code(pred_ids, self.processor.tokenizer, fallback_language)

        if language_code is None and fallback_language is not None:
            retry_kwargs = copy(self.gen_kwargs)
            retry_kwargs["language"] = fallback_language
            pred_ids = self.model.generate(input_features, **retry_kwargs)
            language_code = resolve_language_code(pred_ids, self.processor.tokenizer, fallback_language)

        pred_text = self.processor.batch_decode(
            pred_ids,
            skip_special_tokens=True,
            decode_with_timestamps=False,
        )[0].strip()
        if not pred_text:
            logger.debug("Whisper returned no text; skipping segment")
            return

        language_code = language_code or fallback_language or "en"
        self.last_language = language_code

        if self.start_language == "auto":
            language_code += "-auto"

        mode = getattr(vad_audio, "mode", None)
        if mode == "progressive":
            console.print(f"[cyan]USER (partial): {pred_text}")
            yield PartialTranscription(
                text=pred_text,
                turn_id=vad_audio.turn_id,
                turn_revision=vad_audio.turn_revision,
            )
        else:
            console.print(f"[yellow]USER: {pred_text}")
            yield Transcription(
                text=pred_text,
                language_code=language_code,
                turn_id=vad_audio.turn_id,
                turn_revision=vad_audio.turn_revision,
                speech_stopped_at_s=vad_audio.created_at_s,
            )

    handler_class.process = process
