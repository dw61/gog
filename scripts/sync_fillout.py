"""Fetch completed Fillout reviews and publish only the map's public fields.

Uses the Python standard library. Raw submissions stay in memory, never in Git,
artifacts, or logs. An unsuccessful fetch/validation leaves the last map intact.
"""

import argparse
import calendar
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import statistics
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
API = "https://api.fillout.com/v1/api"
FIELDS = {
    "address": "What is the street address of your apartment?",
    "month": "Which month did you sign your lease?",
    "roommates": "Did you apply with roommates?",
    "deposit": "How much was your security deposit?",
    "people": "How many people are in your apartment / suite / hall?",
    "bedrooms": "How many bedrooms do you have?",
    "toilets": "How many toilets do you have in total?",
    "rent": "How much rent + utility do you pay per month?",
    "rent_basis": "Untitled MultipleChoice field",
    "deal": "Do you think you got a good deal?",
    "temperature": "Does your room get too hot or cold?",
    "noise": "Do you suffer from noise?",
    "room": "Any problems in your room?",
    "building": "Any problems with your apartment?",
    "management": "Any problems with management?",
    "rating": "Overall rating of your apartment",
    "comment": "what do you wish you had known before moving in?",
}
REQUIRED = {"address", "people", "bedrooms", "toilets", "rent", "rent_basis", "rating", "comment"}
TAG_OPTIONS = {
    "roommates": {"no": "can apply without roommate"},
    "deal": {"good deal": "good deal", "too expensive": "too expensive"},
    "temperature": {"no": "comfortable temperature", "too hot": "gets too hot", "too cold": "gets too cold"},
    "noise": {"no": "quiet place", "parties": "party noise", "car traffic": "traffic noise", "train": "train noise", "fire alarm": "fire alarm noise", "roommate": "roommate noise", "thin wall": "thin walls"},
    "room": {"no": "good room", "mold": "mold in room", "bugs": "bugs in room", "too dark": "dark room", "spotty wifi": "spotty wifi", "bad smell": "bad smell", "leaks water": "water leaks"},
    "building": {"no": "good apartment", "too old": "apartment too old", "outside-unit laundry": "outside-unit laundry", "difficult laundry": "difficult laundry", "lost package": "lost packages", "lost packages": "lost packages", "unsafe location": "feels unsafe", "feel unsafe": "feels unsafe", "far from class": "far from class", "far from work": "far from work"},
    "management": {"no": "good management", "slow response": "slow management", "slow maintenance": "slow maintenance", "expensive lease termination": "expensive lease termination"},
}
DEPOSITS = {"0": "no security deposit", "< monthly rent": "small security deposit", "monthly rent": "one monthly rent deposit", "> monthly rent": "large security deposit"}


class SyncError(Exception):
    """A safe error message that contains no submission or credential values."""


def stamp(value):
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None:
            raise ValueError()
        return result.astimezone(timezone.utc)
    except (ValueError, AttributeError, TypeError):
        raise SyncError("A submission has an invalid timestamp.") from None


def iso(value):
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


def label(value):
    return re.sub(r"\s+", " ", str(value).strip()).casefold()


def request_json(path, key):
    request = Request(API + path, headers={"Authorization": "Bearer " + key, "Accept": "application/json"})
    for attempt in range(4):
        try:
            with urlopen(request, timeout=40) as response:
                return json.load(response)
        except HTTPError as error:
            # Never include HTTP response bodies, request URLs, or tokens in logs.
            if error.code not in (429, 500, 502, 503, 504) or attempt == 3:
                raise SyncError(f"Fillout request failed (HTTP {error.code}).") from None
        except (URLError, TimeoutError):
            if attempt == 3:
                raise SyncError("Fillout could not be reached; keeping the previous map.") from None
        except (ValueError, UnicodeError):
            raise SyncError("Fillout returned an invalid JSON response.") from None
        time.sleep(2 ** (attempt + 1))


def fetch_submissions(get, form_id):
    responses, total = [], None
    for _ in range(1000):
        page = get(f"/forms/{form_id}/submissions?" + urlencode({"limit": 150, "offset": len(responses), "status": "finished", "includePreview": "false"}))
        if not isinstance(page, dict) or not isinstance(page.get("responses"), list):
            raise SyncError("Unexpected Fillout submissions format.")
        count = page.get("totalResponses")
        if type(count) is not int or count < 0 or (total is not None and count != total):
            raise SyncError("Fillout changed during pagination; retry the sync.")
        total = count
        batch = page["responses"]
        if len(batch) > 150 or len(responses) + len(batch) > total:
            raise SyncError("Inconsistent Fillout pagination; keeping the previous map.")
        responses.extend(batch)
        if len(responses) == total:
            if not responses:
                raise SyncError("Fillout returned no reviews; refusing to erase the map automatically.")
            return responses
        if not batch:
            raise SyncError("Incomplete Fillout response; keeping the previous map.")
        time.sleep(0.25)
    raise SyncError("Fillout pagination exceeded the safety limit.")


def resolve_fields(metadata, configured):
    if not isinstance(metadata, dict) or not isinstance(metadata.get("questions"), list):
        raise SyncError("Unexpected Fillout form format.")
    questions = metadata["questions"]
    by_id = {str(q["id"]): q for q in questions if isinstance(q, dict) and q.get("id")}
    resolved = {}
    for field, name in FIELDS.items():
        if field in configured:
            field_id = configured[field]
            if field_id not in by_id:
                raise SyncError(f"Configured Fillout field is missing: {field}.")
            resolved[field] = field_id
            continue
        matches = [str(q["id"]) for q in by_id.values() if label(q.get("name", "")) == label(name)]
        if len(matches) > 1 or (not matches and field in REQUIRED):
            raise SyncError(f"Fillout field needs an explicit ID in config/fillout.json: {field}.")
        if matches:
            resolved[field] = matches[0]
    if len(set(resolved.values())) != len(resolved):
        raise SyncError("Fillout fields must have distinct IDs.")
    return resolved


def address_key(value):
    if not isinstance(value, str):
        return ""
    value = value.strip().splitlines()[0].split(",")[0].casefold()
    value = re.sub(r"\b(apt|apartment|unit|suite|ste)\b.*|#.*", "", value)
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\bjpa\b", "jefferson park ave", value)
    aliases = {"road": "rd", "avenue": "ave", "street": "st", "drive": "dr", "lane": "ln", "circle": "cir", "boulevard": "blvd", "north": "n", "south": "s", "east": "e", "west": "w", "northwest": "nw"}
    return " ".join(aliases.get(word, word) for word in value.split())


def building_index(buildings):
    result = {}
    for building in buildings:
        key = address_key(building["street_address"])
        # This project is for UVA housing: do not automatically publish unrelated
        # cities or vague addresses inherited from the historical geocoder.
        lat, lng = building["lat"], building["lng"]
        if not re.match(r"^\d+\s", key) or not (37.95 <= lat <= 38.15 and -78.65 <= lng <= -78.35):
            continue
        for alias in [building["street_address"], *building.get("aliases", [])]:
            normalized = address_key(alias)
            if normalized in result and result[normalized] != building:
                raise SyncError("Ambiguous building alias in config/buildings.json.")
            result[normalized] = building
    return result


def number(value, low, high):
    try:
        if isinstance(value, bool):
            raise ValueError()
        # Dollar signs/commas are accepted, arbitrary text is not guessed.
        value = float(str(value).replace("$", "").replace(",", "").strip())
        if not math.isfinite(value) or not low <= value <= high:
            raise ValueError()
        return value
    except (ValueError, TypeError):
        raise SyncError("invalid_numbers") from None


def selections(value):
    if value is None:
        return []
    if not isinstance(value, list):
        value = str(value).split(",")
    return [label(item) for item in value if isinstance(item, str) and item.strip()]


def review_values(submission, fields):
    questions = submission.get("questions")
    if not isinstance(questions, list):
        raise SyncError("A submission has no question list; keeping the previous map.")
    by_id = {}
    for q in questions:
        if not isinstance(q, dict) or not q.get("id") or str(q["id"]) in by_id:
            raise SyncError("A submission has malformed question IDs.")
        by_id[str(q["id"])] = q.get("value")
    return {field: by_id.get(field_id) for field, field_id in fields.items()}


def validate_review(values, buildings, config):
    building = buildings.get(address_key(values.get("address")))
    if building is None:
        raise SyncError("unknown_address")
    # If a city is supplied, don't confuse a same-named street in another city.
    address = label(values["address"])
    if re.search(r"\b(san francisco|sunnyvale|norfolk|new york|los angeles)\b", address):
        raise SyncError("unknown_address")
    rent = number(values.get("rent"), 1, 100000)
    basis = label(values.get("rent_basis", ""))
    if basis not in {"entire apartment", "just me"}:
        raise SyncError("invalid_rent_basis")
    people = number(values.get("people"), 1, 30)
    if people != int(people):
        raise SyncError("invalid_numbers")
    if basis == "entire apartment":
        rent /= people
    if not config["min_rent_per_person"] <= rent <= config["max_rent_per_person"]:
        raise SyncError("unusual_rent")
    beds = number(values.get("bedrooms"), 0, 30)
    toilets = number(values.get("toilets"), 0.5, 30)
    rating = values.get("rating")
    rating = None if rating is None or rating == "" else number(rating, 1, 5)
    comment = values.get("comment") or ""
    if not isinstance(comment, str) or len(comment) > 10000:
        raise SyncError("invalid_comment")
    # Hold obvious contact details/credentials for review instead of publishing
    # them accidentally in free text. This is a guard, not a full moderation tool.
    if re.search(r"[\w.+-]+@[\w.-]+\.[a-z]{2,}|(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}|AIza[\w-]{30,}|-----BEGIN .*PRIVATE KEY", comment, re.I):
        raise SyncError("comment_needs_review")
    tags = sorted({options[choice] for field, options in TAG_OPTIONS.items() for choice in selections(values.get(field)) if choice in options})
    month = values.get("month")
    try:
        month = calendar.month_name[int(month)] if 1 <= int(month) <= 12 else None
    except (ValueError, TypeError):
        month = None
    return {"building": building, "rent": rent, "bed_toilet": f"{beds:g},{toilets:g}", "rating": rating, "comment": comment.strip(), "tags": tags, "month": month, "deposit": DEPOSITS.get(label(values.get("deposit", "")))}


def transform(responses, fields, buildings, config):
    unique = {}
    for submission in responses:
        if not isinstance(submission, dict) or not isinstance(submission.get("submissionId"), str) or not submission["submissionId"]:
            raise SyncError("A submission has no ID; keeping the previous map.")
        # Fetch requests completed reviews only; reject an explicit contradictory
        # status rather than accidentally publishing a draft.
        if submission.get("status", "finished") != "finished":
            raise SyncError("Fillout returned an unfinished submission.")
        submitted = stamp(submission.get("submissionTime"))
        updated = stamp(submission.get("lastUpdatedAt") or submission.get("submissionTime"))
        sid = submission["submissionId"]
        if sid not in unique or updated > unique[sid][0]:
            unique[sid] = (updated, submitted, submission)
    index, groups, pending = building_index(buildings), defaultdict(list), Counter()
    latest = None
    for _, submitted, submission in sorted(unique.values(), key=lambda item: (item[1], item[2]["submissionId"])):
        values = review_values(submission, fields)
        try:
            review = validate_review(values, index, config)
        except SyncError as error:
            pending[str(error)] += 1
            continue
        latest = max(latest, submitted) if latest else submitted
        groups[review["building"]["street_address"]].append(review)
    apartments = []
    for address, reviews in sorted(groups.items()):
        ratings = [r["rating"] for r in reviews if r["rating"] is not None]
        deposits = Counter(r["deposit"] for r in reviews if r["deposit"])
        apartments.append({
            "street_address": address,
            "lease_month": dict(sorted(Counter(r["month"] for r in reviews if r["month"]).items())),
            "security_deposit": deposits.most_common(1)[0][0] if deposits else "",
            "bed_toilet": ";".join(sorted({r["bed_toilet"] for r in reviews})),
            "rent_per_person": round(statistics.median(r["rent"] for r in reviews)),
            "tags": sorted({tag for r in reviews for tag in r["tags"]}),
            "rating": round(statistics.mean(ratings), 1) if ratings else None,
            "comment": "\n\n".join(r["comment"] for r in reviews if r["comment"]) or "no comments yet",
            "lat": reviews[0]["building"]["lat"], "lng": reviews[0]["building"]["lng"],
            "count": len(reviews),
        })
    if not apartments:
        raise SyncError("No valid reviews; refusing to erase the published map.")
    return apartments, {"source": "fillout", "latest_review_at": iso(latest), "published_reviews": sum(a["count"] for a in apartments), "pending_reviews": sum(pending.values())}, pending


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + "\n").encode()


def sync(config_path, buildings_path, data_path, status_path, get):
    config = json.loads(config_path.read_text())
    fields = resolve_fields(get(f"/forms/{config['form_id']}"), config.get("field_ids", {}))
    responses = fetch_submissions(get, config["form_id"])
    apartments, status, pending = transform(responses, fields, json.loads(buildings_path.read_text()), config)
    old_status = json.loads(status_path.read_text()) if status_path.exists() else {}
    # Large unexpected drops usually mean a form/schema change. Do not silently
    # replace most of the website; investigate before accepting such a migration.
    previous_count = old_status.get("published_reviews", 0)
    if previous_count and status["published_reviews"] < previous_count * 0.75:
        raise SyncError("More than 25% of published reviews would disappear. Investigate the form/schema before replacing the map.")
    data = json_bytes(apartments)
    comparable_old = {k: v for k, v in old_status.items() if k != "published_at"}
    changed = not data_path.exists() or data_path.read_bytes() != data or status != comparable_old
    if changed:
        status["published_at"] = iso(datetime.now(timezone.utc))
        data_path.write_bytes(data)
        status_path.write_bytes(json_bytes(status))
    config_changed = config.get("field_ids") != fields
    if config_changed:
        config["field_ids"] = fields
        config_path.write_bytes(json_bytes(config))
    return changed or config_changed, status, pending


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    key = os.environ.get("FILLOUT_API_KEY", "").strip()
    if not key:
        raise SyncError("Set the private FILLOUT_API_KEY GitHub Actions secret first.")
    changed, status, pending = sync(args.root / "config/fillout.json", args.root / "config/buildings.json", args.root / "static/apartments.json", args.root / "static/data-status.json", lambda path: request_json(path, key))
    summary = f"Published reviews: {status['published_reviews']}. Held for review: {status['pending_reviews']}. Data changed: {str(changed).lower()}."
    print(summary)
    for reason, count in sorted(pending.items()):
        print(f"Held: {reason}: {count}")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            output.write(f"changed={str(changed).lower()}\n")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as output:
            output.write("### Fillout review sync\n\n" + summary + "\n\n")
            output.writelines(f"- {reason}: {count}\n" for reason, count in sorted(pending.items()))
            output.write("\nInspect held reviews privately in Fillout. New buildings need an approved address and map coordinates in config/buildings.json.\n")


if __name__ == "__main__":
    try:
        main()
    except SyncError as error:
        print(f"Sync stopped: {error}", file=sys.stderr)
        sys.exit(1)
    except Exception:
        # Unexpected API data must not be copied into public runner tracebacks.
        print("Sync stopped unexpectedly; the previous published map is unchanged. Check the schema and tests.", file=sys.stderr)
        sys.exit(1)
