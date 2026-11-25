import unittest

from scopus_figure1_from_api import extract_year_counts, build_domain_queries


class FacetIntegrityTests(unittest.TestCase):
    def response(self, categories, total=3):
        return {"search-results": {"opensearch:totalResults": str(total), "facet": {"name": "pubyear", "category": categories}}}

    def test_missing_year_is_zero_only_when_reported_total_reconciles(self):
        data = self.response([{"value": "2025", "hitCount": "3"}])
        self.assertEqual(extract_year_counts(data, [2025, 2026]), {2025: 3, 2026: 0})

    def test_missing_facets_are_not_silent_zeroes(self):
        with self.assertRaises(ValueError):
            extract_year_counts(self.response([], total=3), [2025, 2026])

    def test_truncated_facets_are_rejected(self):
        with self.assertRaises(ValueError):
            extract_year_counts(self.response([{"value": "2025", "hitCount": "2"}]), [2025, 2026])

    def test_invalid_counts_and_years_are_rejected(self):
        for categories in [
            [{"value": "2027", "hitCount": "3"}],
            [{"value": "2025", "hitCount": "-3"}],
            [{"value": "2025", "hitCount": "1"}, {"value": "2025", "hitCount": "2"}],
        ]:
            with self.subTest(categories=categories), self.assertRaises(ValueError):
                extract_year_counts(self.response(categories), [2025, 2026])

    def test_year_range_contains_2026_without_changing_option_six_filters(self):
        for query in build_domain_queries(6, 2010, 2026).values():
            self.assertIn("PUBYEAR > 2009 AND PUBYEAR < 2027", query)
            self.assertIn("DOCTYPE(ar OR re)", query)


if __name__ == "__main__":
    unittest.main()
