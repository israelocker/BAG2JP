"""Coverage contract for the bounded Strike acceptance batch."""
import unittest

from tools.test.strike_acceptance_batch import CASES, validate_cases, batch_status


class BatchCoverageTests(unittest.TestCase):
    def test_last_failure_or_unrestored_case_cannot_pass_batch(self):
        results = [dict(status='machine_complete_awaiting_review',
                        restoration={'verified': True}) for _ in CASES]
        self.assertEqual(batch_status(results), 'finished_awaiting_review')
        self.assertEqual(batch_status(results[:-1]), 'stopped_on_failure')
        results[-1]['status'] = 'failed'
        self.assertEqual(batch_status(results), 'stopped_on_failure')
        results[-1]['status'] = 'incomplete'
        self.assertEqual(batch_status(results), 'stopped_on_failure')
        results[-1]['status'] = 'machine_complete_awaiting_review'
        results[-1]['restoration']['verified'] = False
        self.assertEqual(batch_status(results), 'stopped_on_failure')

    def test_covers_both_sides_costumes_and_heat_stages(self):
        validate_cases(CASES)
        self.assertEqual({(c['side'], c['costume']) for c in CASES},
                         {(1, 'A'), (1, 'B'), (2, 'A'), (2, 'B')})
        self.assertEqual({c['stage'] for c in CASES}, {'HeatBAG1', 'HeatBAG2'})

    def test_rejects_missing_case_or_duplicate_label(self):
        with self.assertRaises(ValueError):
            validate_cases(CASES[:-1])
        with self.assertRaises(ValueError):
            validate_cases([CASES[0], CASES[0], *CASES[2:]])


if __name__ == '__main__':
    unittest.main()
