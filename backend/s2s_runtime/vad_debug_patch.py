from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


def install_vad_debug_patch(vad_handler_class: type | None = None) -> None:
    """Add detailed logging to VAD handler for debugging speech detection issues."""
    if vad_handler_class is None:
        from speech_to_speech.VAD.vad_handler import VADHandler
        vad_handler_class = VADHandler

    if hasattr(vad_handler_class, "_debug_patched"):
        return

    vad_handler_class._debug_patched = True

    # Patch the process method to add detailed logging
    original_process = vad_handler_class.process

    def process(self: Any, audio_chunk: Any) -> Any:
        # Log audio chunk info
        if hasattr(audio_chunk, '__len__'):
            if isinstance(audio_chunk, tuple):
                chunk_bytes, rt_cfg = audio_chunk
                chunk_len = len(chunk_bytes)
            else:
                chunk_len = len(audio_chunk)
            logger.debug(f"VAD DEBUG: Received audio chunk of {chunk_len} bytes")

        # Call original process
        result = list(original_process(self, audio_chunk))

        # Log VAD output
        for item in result:
            if hasattr(item, 'mode'):
                if hasattr(item, 'audio'):
                    duration_ms = len(item.audio) / self.sample_rate * 1000
                    logger.info(f"VAD DEBUG: Yielding {item.mode} audio of {duration_ms:.0f}ms")
                else:
                    logger.info(f"VAD DEBUG: Yielding {item.mode} output")

        return iter(result)

    vad_handler_class.process = process

    # Patch the _process_realtime method to add more logging
    original_process_realtime = vad_handler_class._process_realtime

    def _process_realtime(self: Any, vad_output: Any) -> Any:
        # Log speech buffer state
        if hasattr(self.iterator, 'buffer') and len(self.iterator.buffer) > 0:
            buffer_samples = sum(len(t) for t in self.iterator.buffer)
            buffer_ms = buffer_samples / self.sample_rate * 1000
            active_ms = self._current_active_speech_duration_ms()
            logger.debug(f"VAD DEBUG: Speech buffer={buffer_ms:.0f}ms, active={active_ms:.0f}ms, triggered={self.iterator.triggered}")

        # Log when speech ends
        if vad_output is not None:
            if len(vad_output) > 0:
                array_len = sum(len(t) for t in vad_output)
                duration_ms = array_len / self.sample_rate * 1000
                logger.info(f"VAD DEBUG: Speech ended, duration={duration_ms:.0f}ms")
            else:
                logger.info("VAD DEBUG: Phantom trigger (empty buffer)")

        # Call original method
        yield from original_process_realtime(self, vad_output)

    vad_handler_class._process_realtime = _process_realtime

    # Patch the _process_normal method to add more logging
    original_process_normal = vad_handler_class._process_normal

    def _process_normal(self: Any, vad_output: Any) -> Any:
        # Log when speech ends
        if vad_output is not None:
            if len(vad_output) > 0:
                array_len = sum(len(t) for t in vad_output)
                duration_ms = array_len / self.sample_rate * 1000
                logger.info(f"VAD DEBUG: Speech ended (normal), duration={duration_ms:.0f}ms")
            else:
                logger.info("VAD DEBUG: Phantom trigger (empty buffer, normal)")

        # Call original method
        yield from original_process_normal(self, vad_output)

    vad_handler_class._process_normal = _process_normal

    logger.info("VAD debug patch installed - detailed logging enabled")
