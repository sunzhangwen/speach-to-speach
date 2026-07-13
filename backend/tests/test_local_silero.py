import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from s2s_runtime.local_silero import install_local_silero_patch


class FakeHub:
    def __init__(self):
        self.calls = []

    def load(self, repo_or_dir, model, *args, **kwargs):
        self.calls.append((repo_or_dir, model, args, kwargs))
        return "loaded"


class LocalSileroTests(unittest.TestCase):
    def test_redirects_silero_github_request_to_local_repository(self):
        hub = FakeHub()
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        local_repo = Path(temp_dir.name)
        install_local_silero_patch(local_repo, hub)

        result = hub.load("snakers4/silero-vad", "silero_vad", trust_repo=True, skip_validation=True)

        self.assertEqual(result, "loaded")
        repo, model, _, kwargs = hub.calls[0]
        self.assertEqual(repo, str(local_repo.resolve()))
        self.assertEqual(model, "silero_vad")
        self.assertEqual(kwargs, {"source": "local"})

    def test_preserves_unrelated_torch_hub_requests(self):
        hub = FakeHub()
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        install_local_silero_patch(Path(temp_dir.name), hub)

        hub.load("another/repository", "model", trust_repo=True)

        self.assertEqual(hub.calls[0], ("another/repository", "model", (), {"trust_repo": True}))


if __name__ == "__main__":
    unittest.main()
