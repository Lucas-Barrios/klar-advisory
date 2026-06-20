"""
Tests for fetch_job_description() in services/ausbildung_cache.py.

Covers:
  - Cache-hit path: returns cached text without making an HTTP call
  - Cache-hit when description is NULL (position has no text but was already tried)
  - Graceful failure: HTTP error → None returned, nothing raised
  - Graceful failure: 404 → None returned, nothing raised
  - Cache-miss path: HTTP fetch succeeds, description cached and returned
"""
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

import httpx


def _make_supabase(*, cached_row: dict | None = None, cache_miss_row: dict | None = None):
    """Build a minimal Supabase mock.

    cached_row: data returned when full_description_fetched_at IS set
    cache_miss_row: data returned when the row exists but fetched_at is None
    """
    sb = MagicMock()
    row = cached_row if cached_row is not None else (cache_miss_row or {})
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
        sb = _make_supabase(
            cached_row={
                "full_description": "Cached description text",
                "full_description_fetched_at": "2026-06-20T10:00:00Z",
            }
        )
        with patch("services.ausbildung_cache.get_supabase", return_value=sb), \
             patch("httpx.get") as mock_get:
            from services.ausbildung_cache import fetch_job_description
            result = fetch_job_description("10000-123456-S")

        self.assertEqual(result, "Cached description text")
        mock_get.assert_not_called()

    def test_returns_none_from_cache_when_description_is_null_but_already_fetched(self):
        """If fetched_at is set but description is NULL, honour the cache (position has no text)."""
        sb = _make_supabase(
            cached_row={
                "full_description": None,
                "full_description_fetched_at": "2026-06-20T10:00:00Z",
            }
        )
        with patch("services.ausbildung_cache.get_supabase", return_value=sb), \
             patch("httpx.get") as mock_get:
            from services.ausbildung_cache import fetch_job_description
            result = fetch_job_description("10000-nulldesc-S")

        self.assertIsNone(result)
        mock_get.assert_not_called()


class GracefulFailureTests(unittest.TestCase):
    def test_returns_none_on_network_error_without_raising(self):
        """Any exception from httpx.get must be caught; None returned, no raise."""
        sb = _make_supabase(
            cache_miss_row={"full_description": None, "full_description_fetched_at": None}
        )
        with patch("services.ausbildung_cache.get_supabase", return_value=sb), \
             patch("httpx.get", side_effect=httpx.ConnectError("Connection refused")):
            from services.ausbildung_cache import fetch_job_description
            result = fetch_job_description("bad-refnr")

        self.assertIsNone(result)

    def test_returns_none_on_http_404_without_raising(self):
        """HTTPStatusError (404) must be caught; None returned, no raise."""
        sb = _make_supabase(
            cache_miss_row={"full_description": None, "full_description_fetched_at": None}
        )
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found",
            request=MagicMock(),
            response=MagicMock(),
        )
        with patch("services.ausbildung_cache.get_supabase", return_value=sb), \
             patch("httpx.get", return_value=mock_response):
            from services.ausbildung_cache import fetch_job_description
            result = fetch_job_description("expired-refnr")

        self.assertIsNone(result)

    def test_returns_none_when_cache_lookup_raises_and_http_also_fails(self):
        """If both cache lookup and HTTP fail, still returns None without raising."""
        sb = MagicMock()
        (
            sb.table.return_value
            .select.return_value
            .eq.return_value
            .single.return_value
            .execute.side_effect
        ) = Exception("column does not exist")

        with patch("services.ausbildung_cache.get_supabase", return_value=sb), \
             patch("httpx.get", side_effect=Exception("network error")):
            from services.ausbildung_cache import fetch_job_description
            result = fetch_job_description("any-refnr")

        self.assertIsNone(result)


class CacheMissAndFetchTests(unittest.TestCase):
    def test_fetches_from_api_on_cache_miss_and_returns_description(self):
        """On cache miss, hits the detail API and returns stellenangebotsBeschreibung."""
        sb = MagicMock()
        # First call (cache check) returns cache miss
        (
            sb.table.return_value
            .select.return_value
            .eq.return_value
            .single.return_value
            .execute.return_value
        ) = SimpleNamespace(
            data={"full_description": None, "full_description_fetched_at": None}
        )

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "stellenangebotsBeschreibung": "Du lernst die Grundlagen der Pflege...",
            "stellenangebotsTitel": "Ausbildung Pflege",
        }

        with patch("services.ausbildung_cache.get_supabase", return_value=sb), \
             patch("httpx.get", return_value=mock_response):
            from services.ausbildung_cache import fetch_job_description
            result = fetch_job_description("10000-999999-S")

        self.assertEqual(result, "Du lernst die Grundlagen der Pflege...")

    def test_returns_none_when_description_field_absent_in_response(self):
        """If stellenangebotsBeschreibung is missing from the response, return None."""
        sb = MagicMock()
        (
            sb.table.return_value
            .select.return_value
            .eq.return_value
            .single.return_value
            .execute.return_value
        ) = SimpleNamespace(
            data={"full_description": None, "full_description_fetched_at": None}
        )

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"stellenangebotsTitel": "Ausbildung Pflege"}

        with patch("services.ausbildung_cache.get_supabase", return_value=sb), \
             patch("httpx.get", return_value=mock_response):
            from services.ausbildung_cache import fetch_job_description
            result = fetch_job_description("10000-nodesc-S")

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
