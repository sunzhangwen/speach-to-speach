from pathlib import Path

from s2s_runtime.local_silero import install_local_silero_patch
from s2s_runtime.qwen3_cpu_backend import install_cpu_backend_patch
from s2s_runtime.whisper_short_output import install_whisper_short_output_patch
from speech_to_speech.s2s_pipeline import main


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    install_local_silero_patch(project_root / ".cache" / "torch" / "hub" / "snakers4_silero-vad_master")
    install_cpu_backend_patch()
    install_whisper_short_output_patch()
    main()
