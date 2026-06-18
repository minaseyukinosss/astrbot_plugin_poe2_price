import unittest

from models import TradeListing
from services.price_estimator import estimate_price


class PriceEstimatorTest(unittest.TestCase):
    def test_filters_obvious_low_outlier_and_uses_median_range(self):
        listings = [
            TradeListing(amount=1, currency="exalted"),
            TradeListing(amount=10, currency="exalted"),
            TradeListing(amount=12, currency="exalted"),
            TradeListing(amount=14, currency="exalted"),
            TradeListing(amount=16, currency="exalted"),
            TradeListing(amount=18, currency="exalted"),
        ]

        estimate = estimate_price("風暴 行靴", "Runes of Aldur", listings, min_valid_listings=5)

        self.assertEqual(estimate.valid_count, 5)
        self.assertEqual(estimate.median, 14)
        self.assertEqual(estimate.low, 12)
        self.assertEqual(estimate.high, 16)
        self.assertEqual(estimate.confidence, "高")
        self.assertEqual(estimate.currency, "exalted")

    def test_low_confidence_when_sample_count_is_too_small(self):
        listings = [
            TradeListing(amount=20, currency="exalted"),
            TradeListing(amount=24, currency="exalted"),
        ]

        estimate = estimate_price("水井之心", "Runes of Aldur", listings, min_valid_listings=5)

        self.assertEqual(estimate.valid_count, 2)
        self.assertEqual(estimate.confidence, "低")
        self.assertIn("样本不足", estimate.warnings)


if __name__ == "__main__":
    unittest.main()
