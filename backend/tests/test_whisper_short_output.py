import unittest
from types import SimpleNamespace

import torch

from s2s_runtime.whisper_short_output import install_whisper_short_output_patch, resolve_language_code


class FakeTokenizer:
    def __init__(self, decoded_token="<|endoftext|>"):
        self.decoded_token = decoded_token

    def decode(self, token):
        return self.decoded_token


class FakeProcessor:
    def __init__(self, text, decoded_token="<|endoftext|>"):
        self.tokenizer = FakeTokenizer(decoded_token)
        self.text = text

    def batch_decode(self, *args, **kwargs):
        return [self.text]


class FakeModel:
    def __init__(self, pred_ids):
        self.pred_ids = pred_ids

    def generate(self, *args, **kwargs):
        return self.pred_ids


class WhisperShortOutputTests(unittest.TestCase):
    def test_single_token_uses_fixed_language_fallback(self):
        language = resolve_language_code(torch.tensor([[1]]), FakeTokenizer(), "zh")
        self.assertEqual(language, "zh")

    def test_language_token_is_decoded_when_present(self):
        language = resolve_language_code(torch.tensor([[1, 2]]), FakeTokenizer("<|zh|>"), "en")
        self.assertEqual(language, "zh")

    def test_patched_process_emits_text_for_single_token_without_index_error(self):
        class FakeHandler:
            pass

        install_whisper_short_output_patch(FakeHandler)
        handler = FakeHandler()
        handler.model = FakeModel(torch.tensor([[1]]))
        handler.processor = FakeProcessor("你好")
        handler.gen_kwargs = {"language": "zh"}
        handler.last_language = "zh"
        handler.start_language = "zh"
        handler.prepare_model_inputs = lambda audio: torch.tensor([0.0])
        vad_audio = SimpleNamespace(
            audio=torch.tensor([0.0]),
            turn_id="turn-1",
            turn_revision=0,
            created_at_s=1.5,
        )

        outputs = list(handler.process(vad_audio))

        self.assertEqual(len(outputs), 1)
        self.assertEqual(outputs[0].text, "你好")
        self.assertEqual(outputs[0].language_code, "zh")

    def test_patched_process_skips_empty_transcription(self):
        class FakeHandler:
            pass

        install_whisper_short_output_patch(FakeHandler)
        handler = FakeHandler()
        handler.model = FakeModel(torch.tensor([[1]]))
        handler.processor = FakeProcessor("   ")
        handler.gen_kwargs = {"language": "zh"}
        handler.last_language = "zh"
        handler.start_language = "zh"
        handler.prepare_model_inputs = lambda audio: torch.tensor([0.0])
        vad_audio = SimpleNamespace(audio=torch.tensor([0.0]))

        self.assertEqual(list(handler.process(vad_audio)), [])


if __name__ == "__main__":
    unittest.main()
