from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any

import numpy as np
import torch

logger = logging.getLogger(__name__)


class NativeQwen3TTSAdapter:
    """Expose native qwen-tts generation through the streaming handler API."""

    def __init__(self, native_model: Any) -> None:
        self.model = native_model

    @classmethod
    def from_pretrained(
        cls,
        model_name: str,
        *,
        device: str,
        dtype: str | torch.dtype,
        attn_implementation: str,
    ) -> "NativeQwen3TTSAdapter":
        from qwen_tts import Qwen3TTSModel

        resolved_dtype = getattr(torch, dtype) if isinstance(dtype, str) else dtype
        native_model = Qwen3TTSModel.from_pretrained(
            model_name,
            device_map=device,
            dtype=resolved_dtype,
            attn_implementation=attn_implementation,
        )
        return cls(native_model)

    @staticmethod
    def _stream_result(result: tuple[list[np.ndarray], int]) -> Iterator[tuple[np.ndarray, int, None]]:
        wavs, sample_rate = result
        for wav in wavs:
            yield np.asarray(wav, dtype=np.float32), int(sample_rate), None

    def _warmup(self, prefill_len: int) -> None:
        del prefill_len

    def get_supported_speakers(self) -> list[str] | None:
        return self.model.get_supported_speakers()

    def generate_custom_voice_streaming(
        self,
        *,
        text: str,
        speaker: str,
        language: str,
        instruct: str | None,
        chunk_size: int,
        max_new_tokens: int,
        non_streaming_mode: bool | None,
    ) -> Iterator[tuple[np.ndarray, int, None]]:
        del chunk_size
        result = self.model.generate_custom_voice(
            text=text,
            speaker=speaker,
            language=language,
            instruct=instruct,
            max_new_tokens=max_new_tokens,
            non_streaming_mode=True if non_streaming_mode is None else non_streaming_mode,
        )
        yield from self._stream_result(result)

    def generate_voice_clone_streaming(
        self,
        *,
        text: str,
        language: str,
        ref_audio: Any,
        ref_text: str | None,
        xvec_only: bool,
        chunk_size: int,
        max_new_tokens: int,
        parity_mode: bool,
        non_streaming_mode: bool | None,
    ) -> Iterator[tuple[np.ndarray, int, None]]:
        del chunk_size, parity_mode
        result = self.model.generate_voice_clone(
            text=text,
            language=language,
            ref_audio=ref_audio,
            ref_text=ref_text,
            x_vector_only_mode=xvec_only,
            max_new_tokens=max_new_tokens,
            non_streaming_mode=False if non_streaming_mode is None else non_streaming_mode,
        )
        yield from self._stream_result(result)

    def generate_voice_design_streaming(
        self,
        *,
        text: str,
        instruct: str | None,
        language: str,
        chunk_size: int,
        max_new_tokens: int,
        non_streaming_mode: bool | None,
    ) -> Iterator[tuple[np.ndarray, int, None]]:
        del chunk_size
        result = self.model.generate_voice_design(
            text=text,
            instruct=instruct or "",
            language=language,
            max_new_tokens=max_new_tokens,
            non_streaming_mode=True if non_streaming_mode is None else non_streaming_mode,
        )
        yield from self._stream_result(result)


def install_cpu_backend_patch(handler_class: type | None = None) -> None:
    """Use native qwen-tts on CPU while preserving the CUDA implementation."""
    if handler_class is None:
        from speech_to_speech.TTS.qwen3_tts_handler import Qwen3TTSHandler

        handler_class = Qwen3TTSHandler

    if hasattr(handler_class, "_project_original_setup_faster"):
        return

    original_setup = handler_class._setup_faster
    handler_class._project_original_setup_faster = original_setup

    def setup_faster(self: Any, model_name: str, dtype: Any, attn_implementation: str, backend: str = "ggml") -> None:
        if self.device != "cpu":
            return original_setup(self, model_name, dtype, attn_implementation, backend=backend)

        logger.info("Loading Qwen3-TTS through native qwen-tts CPU backend")
        self.dtype = getattr(torch, dtype) if isinstance(dtype, str) else dtype
        self.model = NativeQwen3TTSAdapter.from_pretrained(
            model_name,
            device="cpu",
            dtype=dtype,
            attn_implementation=attn_implementation,
        )

    handler_class._setup_faster = setup_faster
