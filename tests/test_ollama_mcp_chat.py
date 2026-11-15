"""The chat bridge must hand the model only §2 of personality.md.

personality.md's own §1 specifies the model receives the character prompt
between the BEGIN/END markers; the meta sections are for humans. When the
markers are absent the loader falls back to the whole file.
"""
import unittest

import scripts.ollama_mcp_chat as chat


class CharacterPromptExtractionTests(unittest.TestCase):
    def test_extracts_only_the_marked_section(self):
        text = (
            "# Personality\n\n## 1. How to use this file\nMeta instructions.\n\n"
            "## 2. The character prompt\n\n<!-- BEGIN CHARACTER PROMPT -->\n\n"
            "You are Percival, the steward.\nSpeak plainly.\n\n"
            "<!-- END CHARACTER PROMPT -->\n\n"
            "## 3. Rehearsal guide\nHuman-only notes.\n"
        )
        result = chat.extract_character_prompt(text)
        self.assertEqual(result, "You are Percival, the steward.\nSpeak plainly.")
        self.assertNotIn("Meta instructions", result)
        self.assertNotIn("Human-only notes", result)
        self.assertNotIn("BEGIN CHARACTER PROMPT", result)

    def test_falls_back_to_whole_file_without_markers(self):
        text = "You are Percival.\nNo markers here.\n"
        self.assertEqual(chat.extract_character_prompt(text), text)

    def test_falls_back_when_markers_are_reversed(self):
        text = "<!-- END CHARACTER PROMPT -->\nbody\n<!-- BEGIN CHARACTER PROMPT -->\n"
        self.assertEqual(chat.extract_character_prompt(text), text)

    def test_real_personality_file_loads_only_the_character(self):
        result = chat.load_personality()
        self.assertIn("You are Percival, the personal operations steward of one household.", result)
        self.assertNotIn("BEGIN CHARACTER PROMPT", result)
        self.assertNotIn("END CHARACTER PROMPT", result)
        with open(chat.PERSONALITY_PATH, encoding="utf-8") as fh:
            self.assertLess(len(result), len(fh.read()))


if __name__ == "__main__":
    unittest.main()
