import unittest
from unittest.mock import patch

import numpy as np

from s2s_runtime.qwen3_cpu_backend import NativeQwen3TTSAdapter, install_cpu_backend_patch


class FakeNativeModel:
    def __init__(self):
        self.calls = []

    def generate_custom_voice(self, **kwargs):
        self.calls.append(("custom", kwargs))
        return [np.array([0.25, -0.25], dtype=np.float32)], 24000

    def generate_voice_clone(self, **kwargs):
        self.calls.append(("clone", kwargs))
        return [np.array([0.1], dtype=np.float32)], 22050

    def generate_voice_design(self, **kwargs):
        self.calls.append(("design", kwargs))
        return [np.array([0.2], dtype=np.float32)], 16000

    def get_supported_speakers(self):
        return ["Aiden"]


class NativeQwen3TTSAdapterTests(unittest.TestCase):
    def setUp(self):
        self.native = FakeNativeModel()
        self.adapter = NativeQwen3TTSAdapter(self.native)

    def test_custom_voice_converts_native_result_to_stream_item(self):
        chunks = list(
            self.adapter.generate_custom_voice_streaming(
                text="你好",
                speaker="Aiden",
                language="chinese",
                instruct=None,
                chunk_size=8,
                max_new_tokens=360,
                non_streaming_mode=True,
            )
        )

        np.testing.assert_array_equal(chunks[0][0], np.array([0.25, -0.25], dtype=np.float32))
        self.assertEqual(chunks[0][1], 24000)
        self.assertIsNone(chunks[0][2])
        _, kwargs = self.native.calls[0]
        self.assertNotIn("chunk_size", kwargs)
        self.assertEqual(kwargs["max_new_tokens"], 360)

    def test_voice_clone_maps_xvec_argument(self):
        list(
            self.adapter.generate_voice_clone_streaming(
                text="测试",
                language="chinese",
                ref_audio="reference.wav",
                ref_text="参考文本",
                xvec_only=True,
                chunk_size=8,
                max_new_tokens=400,
                parity_mode=False,
                non_streaming_mode=True,
            )
        )

        _, kwargs = self.native.calls[0]
        self.assertTrue(kwargs["x_vector_only_mode"])
        self.assertNotIn("xvec_only", kwargs)
        self.assertNotIn("parity_mode", kwargs)

    def test_voice_design_and_supported_speakers_delegate(self):
        chunks = list(
            self.adapter.generate_voice_design_streaming(
                text="测试",
                instruct="温柔",
                language="chinese",
                chunk_size=8,
                max_new_tokens=360,
                non_streaming_mode=True,
            )
        )

        self.assertEqual(chunks[0][1], 16000)
        self.assertEqual(self.adapter.get_supported_speakers(), ["Aiden"])

    def test_patch_uses_native_backend_only_for_cpu(self):
        class FakeHandler:
            def _setup_faster(self, model_name, dtype, attn_implementation):
                self.original_call = (model_name, dtype, attn_implementation)

        install_cpu_backend_patch(FakeHandler)

        cpu_handler = FakeHandler()
        cpu_handler.device = "cpu"
        with patch.object(NativeQwen3TTSAdapter, "from_pretrained", return_value=self.adapter) as load:
            cpu_handler._setup_faster("local-model", "float32", "eager")
            load.assert_called_once_with("local-model", device="cpu", dtype="float32", attn_implementation="eager")
            self.assertIs(cpu_handler.model, self.adapter)

        gpu_handler = FakeHandler()
        gpu_handler.device = "cuda"
        gpu_handler._setup_faster("gpu-model", "auto", "eager")
        self.assertEqual(gpu_handler.original_call, ("gpu-model", "auto", "eager"))


if __name__ == "__main__":
    unittest.main()
