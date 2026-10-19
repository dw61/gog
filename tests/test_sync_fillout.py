import copy
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.sync_fillout import (
    FIELDS, SyncError, address_key, fetch_submissions, json_bytes,
    main, resolve_fields, sync, transform,
)


CONFIG = {"form_id": "test-form", "min_rent_per_person": 200, "max_rent_per_person": 10000, "field_ids": {}}
BUILDINGS = [{"street_address": "100 Stadium Rd", "lat": 38.032, "lng": -78.509}]
FIELD_IDS = {name: f"field-{name}" for name in FIELDS}
METADATA = {"questions": [{"id": FIELD_IDS[key], "name": name} for key, name in FIELDS.items()]}


def submission(sid="review-1", **values):
    answers = {"address": "100 Stadium Road, Charlottesville, VA", "people": 2,
               "bedrooms": 2, "toilets": 1, "rent": 2000,
               "rent_basis": "entire apartment", "rating": 4,
               "comment": "Great place", "noise": ["train", "parties"], "month": 3}
    answers.update(values)
    return {"submissionId": sid, "submissionTime": "2026-10-18T10:00:00Z",
            "lastUpdatedAt": "2026-10-18T10:00:00Z",
            "questions": [{"id": FIELD_IDS[key], "value": value} for key, value in answers.items()],
            # These private fields must never get into the public output.
            "login": {"email": "private@example.org"}, "editLink": "https://private.example/edit"}


class ReviewsTest(unittest.TestCase):
    def process(self, reviews):
        return transform(reviews, FIELD_IDS, BUILDINGS, CONFIG)

    def test_latest_edit_wins_and_duplicates_do_not_inflate_count(self):
        old = submission()
        edited = submission(rent=2400, comment="Updated review")
        edited["lastUpdatedAt"] = "2026-10-18T11:00:00Z"
        data, status, _ = self.process([edited, old, submission("review-2", rent=1600)])
        self.assertEqual(data[0]["count"], 2)
        self.assertEqual(data[0]["rent_per_person"], 1000)
        self.assertIn("Updated review", data[0]["comment"])
        self.assertNotIn("Great place\n\nGreat place", data[0]["comment"])
        self.assertEqual(status["published_reviews"], 2)

    def test_personal_rent_is_not_divided_again(self):
        data, _, _ = self.process([submission(rent=900, rent_basis="just me")])
        self.assertEqual(data[0]["rent_per_person"], 900)

    def test_missing_rating_and_multiselect_and_private_allowlist(self):
        data, _, _ = self.process([submission(rating=None)])
        self.assertIsNone(data[0]["rating"])
        self.assertEqual(data[0]["tags"], ["party noise", "train noise"])
        self.assertEqual(data[0]["lease_month"], {"March": 1})
        output = json_bytes(data).decode()
        for private in ["private@example.org", "editLink", "submissionId", "field-address", "lastUpdatedAt"]:
            self.assertNotIn(private, output)

    def test_invalid_rows_are_held_without_changing_other_reviews(self):
        cases = [
            ({"rent": 125, "rent_basis": "just me"}, "unusual_rent"),
            ({"people": 0}, "invalid_numbers"),
            ({"rent": "NaN"}, "invalid_numbers"),
            ({"rent_basis": "something new"}, "invalid_rent_basis"),
            ({"address": "9 Unknown St"}, "unknown_address"),
            ({"comment": "Email me at private@example.org"}, "comment_needs_review"),
            ({"comment": "Call 555-222-3333"}, "comment_needs_review"),
        ]
        for values, reason in cases:
            with self.subTest(reason=reason, values=values):
                data, status, pending = self.process([submission(), submission("invalid", **values)])
                self.assertEqual(data[0]["count"], 1)
                self.assertEqual(status["pending_reviews"], 1)
                self.assertEqual(pending, {reason: 1})

    def test_no_valid_reviews_never_erases_map(self):
        with self.assertRaises(SyncError):
            self.process([submission(address="unknown")])

    def test_missing_schema_or_bad_timestamps_fail_closed(self):
        for changed in [{"submissionId": None}, {"questions": None}, {"submissionTime": "invalid"}, {"status": "in_progress"}]:
            review = submission()
            review.update(changed)
            with self.subTest(changed=changed), self.assertRaises(SyncError):
                self.process([review])

    def test_address_aliases_and_unit_numbers(self):
        self.assertEqual(address_key("100 Stadium Road Apt 2\nCharlottesville VA"), "100 stadium rd")
        self.assertEqual(address_key("1800 JPA #4"), "1800 jefferson park ave")
        self.assertEqual(address_key("100 Stadium Rd, Apartment 2"), "100 stadium rd")

    def test_ids_survive_label_changes_and_missing_ids_fail(self):
        renamed = copy.deepcopy(METADATA)
        renamed["questions"][0]["name"] = "New address label"
        self.assertEqual(resolve_fields(renamed, FIELD_IDS), FIELD_IDS)
        with self.assertRaises(SyncError):
            resolve_fields(renamed, {})
        duplicate = copy.deepcopy(METADATA)
        duplicate["questions"].append({"id": "other", "name": FIELDS["rent"]})
        with self.assertRaises(SyncError):
            resolve_fields(duplicate, {})

    def test_pagination_and_partial_results(self):
        responses = [submission(f"id-{i}") for i in range(151)]
        pages = [{"responses": responses[:150], "totalResponses": 151},
                 {"responses": responses[150:], "totalResponses": 151}]
        with patch("scripts.sync_fillout.time.sleep"):
            self.assertEqual(len(fetch_submissions(lambda _: pages.pop(0), "form")), 151)
        for pages in [
            [{"responses": [], "totalResponses": 0}],
            [{"responses": [], "totalResponses": 151}],
            [{"responses": responses[:150], "totalResponses": 151}, {"responses": responses[150:], "totalResponses": 152}],
        ]:
            with self.subTest(pages=len(pages)), patch("scripts.sync_fillout.time.sleep"), self.assertRaises(SyncError):
                fetch_submissions(lambda _: pages.pop(0), "form")


class SyncTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.paths = [self.root / name for name in ("config.json", "buildings.json", "data.json", "status.json")]
        self.paths[0].write_bytes(json_bytes(CONFIG))
        self.paths[1].write_bytes(json_bytes(BUILDINGS))
        self.responses = [submission(), submission("review-2", rent=2400)]

    def run_sync(self):
        def get(path):
            return {"responses": self.responses, "totalResponses": len(self.responses)} if "submissions?" in path else METADATA
        return sync(*self.paths, get)

    def test_unchanged_runs_do_not_update_timestamp_or_require_deploy(self):
        self.assertTrue(self.run_sync()[0])
        first = [path.read_bytes() for path in self.paths]
        self.assertFalse(self.run_sync()[0])
        self.assertEqual(first, [path.read_bytes() for path in self.paths])
        self.assertEqual(json.loads(self.paths[0].read_text())["field_ids"], FIELD_IDS)

    def test_schema_inspection_never_fetches_answers_or_logs_private_metadata(self):
        (self.root / "config").mkdir()
        (self.root / "config/fillout.json").write_bytes(json_bytes(CONFIG))
        metadata = copy.deepcopy(METADATA)
        metadata["private"] = "private-metadata"
        metadata["questions"][0]["private"] = "private-question-property"
        output = io.StringIO()
        with patch("sys.argv", ["sync_fillout.py", "--root", str(self.root), "--inspect-schema"]), patch.dict(os.environ, {"FILLOUT_API_KEY": "test-private-key"}), patch("scripts.sync_fillout.request_json", return_value=metadata) as request, redirect_stdout(output):
            main()
        request.assert_called_once_with("/forms/test-form", "test-private-key")
        parsed = json.loads(output.getvalue())
        self.assertTrue(all(set(q) == {"id", "name", "type"} for q in parsed))
        self.assertNotIn("private-", output.getvalue())
        self.assertFalse(self.paths[2].exists())

    def test_full_fetch_applies_deletions_and_no_partial_fetch_overwrites(self):
        self.run_sync()
        original = self.paths[2].read_bytes()
        self.responses = []
        with self.assertRaises(SyncError):
            self.run_sync()
        self.assertEqual(original, self.paths[2].read_bytes())
        # A normal deletion is reflected, but a sudden >25% loss is held.
        self.responses = [submission(str(i)) for i in range(8)]
        self.run_sync()
        self.responses.pop()
        self.assertTrue(self.run_sync()[0])
        self.assertEqual(json.loads(self.paths[2].read_text())[0]["count"], 7)
        original = self.paths[2].read_bytes()
        self.responses = self.responses[:1]
        with self.assertRaises(SyncError):
            self.run_sync()
        self.assertEqual(original, self.paths[2].read_bytes())


if __name__ == "__main__":
    unittest.main()
