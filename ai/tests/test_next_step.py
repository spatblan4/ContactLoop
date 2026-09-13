import importlib.util
from pathlib import Path
import unittest


module_path = Path(__file__).parents[1] / "contact_brief" / "next_step.py"
spec = importlib.util.spec_from_file_location("contact_brief_next_step", module_path)
next_step = importlib.util.module_from_spec(spec)
spec.loader.exec_module(next_step)
grounded_suggested_next_step = next_step.grounded_suggested_next_step


class GroundedSuggestedNextStepTests(unittest.TestCase):
    def test_uses_earliest_open_follow_up_when_model_returns_default(self):
        result = grounded_suggested_next_step(
            "No suggested next step recorded.",
            [
                {"due_at": "2026-09-22T16:00:00+00:00", "status": "open"},
                {"due_at": "2026-09-15T16:00:00+00:00", "status": "open"},
            ],
        )

        self.assertEqual(result, "Follow up with the parent on Tuesday, September 15, 2026.")

    def test_preserves_a_grounded_model_suggestion(self):
        result = grounded_suggested_next_step(
            "Send the teacher-approved reading plan before the next call.",
            [{"due_at": "2026-09-15T16:00:00+00:00", "status": "open"}],
        )

        self.assertEqual(result, "Send the teacher-approved reading plan before the next call.")

    def test_keeps_default_when_there_is_no_open_follow_up(self):
        result = grounded_suggested_next_step("", [])

        self.assertEqual(result, "No suggested next step recorded.")


if __name__ == "__main__":
    unittest.main()
