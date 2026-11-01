"""Routine retries continue without another approval and remain bounded."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from continuation import MAX_EXTENSIONS, MAX_ROUNDS, check_totals, extension


class ContinuationTests(unittest.TestCase):
    def test_scoped_reason_allows_retry_without_new_user_approval(self):
        record = extension([], {'attempts': 1, 'seconds': 300, 'invocations': 1}, 'Recheck the corrected renderer preflight against the frozen task.')
        self.assertTrue(record['automatic'])
        self.assertNotIn('authorization', record)
        self.assertEqual((record['round'],record['max_rounds']),(2,5))
        last = extension([record] * (MAX_EXTENSIONS - 1), {'attempts': 1}, 'Complete the fifth round within the same task.')
        self.assertEqual(last['round'], MAX_ROUNDS)

    def test_per_batch_and_cumulative_retries_are_bounded(self):
        record = extension([], {'attempts': 1}, 'Rerun affected checks after the scoped repair.')
        with self.assertRaisesRegex(ValueError, 'ceiling'):
            extension([record] * MAX_EXTENSIONS, {'attempts': 1}, 'Another retry.')
        for additions in ({'attempts': 3}, {'invocations': 5}, {'seconds': 901}, {'handoffs': 5}):
            with self.subTest(additions=additions), self.assertRaisesRegex(ValueError, 'ceiling'):
                extension([], additions, 'Retry.')

    def test_hard_limits_and_stalled_progress_block_automatic_extension(self):
        with self.assertRaisesRegex(ValueError, 'hard limit'):
            check_totals({'invocations': 5}, {'invocations': 4})
        with self.assertRaisesRegex(ValueError, 'hard limit'):
            extension([], {'invocations': 1}, 'Retry.', current={'invocations': 4}, hard_limits={'invocations': 4})
        with self.assertRaisesRegex(ValueError, 'stalled'):
            extension([], {'seconds': 60}, 'Retry.', stalled=True)

    def test_invalid_requests_do_not_mutate_history(self):
        history = []
        for additions, reason in (({'attempts': True}, 'Retry.'), ({'attempts': -1}, 'Retry.'), ({'attempts': 0}, 'Retry.'), ({'unknown': 1}, 'Retry.'), ({'attempts': 1}, '')):
            with self.subTest(additions=additions), self.assertRaises(ValueError):
                extension(history, additions, reason)
        self.assertEqual(history, [])
        for limits in (False, [], {'seconds': True}, {'unknown': 2}):
            with self.subTest(limits=limits), self.assertRaises(ValueError):
                check_totals({}, limits)
