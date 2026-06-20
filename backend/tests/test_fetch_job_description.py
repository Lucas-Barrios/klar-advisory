"""
Tests for fetch_job_description() in services/ausbildung_cache.py.

The function accepts its supabase client as a parameter (not get_supabase() internally),
so tests pass mock clients directly — no global get_supabase() patching required.

Covers:
  - Cache-hit path: returns cached text without making an HTTP call
  - Cache-hit when description is NULL (position has no text but was already tried)
  - Graceful failure: HTTP error → None returned, nothing raised
  - Graceful failure: 404 → None returned, nothing raised
  - Graceful failure: both cache and HTTP fail → None, nothing raised
  - Cache-miss path: HTTP fetch succeeds, description cached and returned
  - Missing description field in response → None returned
"""
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx

from services.ausbildung_cache import fetch_job_description


def _make_supabase(*, row: dict):
    """Return a Supabase mock whose single-row select always returns `row`."""
    sb = MagicMock()
    (
        sb.table.return_value
        .select.return_value
        .eq.return_value
        .single.return_value
        .execute.return_value
    ) = SimpleNamespace(data=row)
    return sb


class CacheHitTests(unittest.TestCase):
    def test_returns_cached_description_without_http_call(self):
        sb = _make_supabase(row={
            "full_description": "Cached description text",
            "full_description_fetched_at": "2026-06-20T10:00:00Z",
        })
        with patch("httpx.get") as mock_get:
            result = fetch_job_description("10000-123456-S", sb)

        self.assertEqual(result, "Cached description text")
        mock_get.assert_not_called()

    def test_returns_none_from_cache_when_description_is_null_but_already_fetched(self):
        """fetched_at set but description NULL — honour the cache (position has no text)."""
        sb = _make_supabase(row={
            "full_description": None,
            "full_description_fetched_at": "2026-06-20T10:00:00Z",
        })
        with patch("httpx.get") as mock_get:
            result = fetch_job_description("10000-nulldesc-S", sb)

        self.assertIsNone(result)
        mock_get.assert_not_called()


class GracefulFailureTests(unittest.TestCase):
    def test_returns_none_on_network_error_without_raising(self):
        """Any exception from httpx.get must be caught; None returned, no raise."""
        sb = _make_supabase(row={"full_description": None, "full_description_fetched_at": None})
        with patch("httpx.get", side_effect=httpx.ConnectError("Connection refused")):
            result = fetch_job_description("bad-refnr", sb)

        self.assertIsNone(result)

    def test_returns_none_on_http_404_without_raising(self):
        """HTTPStatusError (e.g. 404) must be caught; None returned, no raise."""
        sb = _make_supabase(row={"full_description": None, "full_description_fetched_at": None})
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=MagicMock(), response=MagicMock()
        )
        with patch("httpx.get", return_value=mock_response):
            result = fetch_job_description("expired-refnr", sb)

        self.assertIsNone(result)

    def test_returns_none_when_cache_lookup_raises_and_http_also_fails(self):
        """Both cache and HTTP fail → None, nothing raised."""
        sb = MagicMock()
        (
            sb.table.return_value
            .select.return_value
            .eq.return_value
            .single.return_value
            .execute.side_effect
        ) = Exception("column does not exist")

        with patch("httpx.get", side_effect=Exception("network error")):
            result = fetch_job_description("any-refnr", sb)

        self.assertIsNone(result)


class CacheMissAndFetchTests(unittest.TestCase):
    def test_fetches_from_api_on_cache_miss_and_returns_description(self):
        """Cache miss → hits detail API → returns stellenangebotsBeschreibung."""
        sb = _make_supabase(row={"full_description": None, "full_description_fetched_at": None})

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "stellenangebotsBeschreibung": "Du lernst die Grundlagen der Pflege...",
            "stellenangebotsTitel": "Ausbildung Pflege",
        }

        with patch("httpx.get", return_value=mock_response):
            result = fetch_job_description("10000-999999-S", sb)

        self.assertEqual(result, "Du lernst die Grundlagen der Pflege...")

    def test_returns_none_when_description_field_absent_in_response(self):
        """stellenangebotsBeschreibung missing → None returned."""
        sb = _make_supabase(row={"full_description": None, "full_description_fetched_at": None})

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"stellenangebotsTitel": "Ausbildung Pflege"}

        with patch("httpx.get", return_value=mock_response):
            result = fetch_job_description("10000-nodesc-S", sb)

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
