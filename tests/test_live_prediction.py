import unittest

from homtech.ml.live import LiveConsensus


class LiveConsensusTests(unittest.TestCase):
    def test_requires_three_agreeing_frames_over_at_least_one_second(self):
        consensus = LiveConsensus()
        self.assertIsNone(consensus.observe("happy", 0))
        self.assertIsNone(consensus.observe("happy", 0.25))
        self.assertIsNone(consensus.observe("happy", 0.5))
        self.assertEqual(consensus.observe("happy", 1), "happy")

    def test_one_different_or_uncertain_frame_does_not_change_a_confirmed_expression(self):
        consensus = LiveConsensus()
        for stamp in (0, 0.5, 1):
            consensus.observe("happy", stamp)
        self.assertEqual(consensus.observe("sad", 1.5), "happy")
        self.assertEqual(consensus.observe(None, 2), "happy")
        self.assertEqual(consensus.observe("sad", 2.5), "happy")
        self.assertEqual(consensus.observe("sad", 3), "happy")
        self.assertEqual(consensus.observe("sad", 3.5), "sad")

    def test_expires_old_results_without_using_frames_outside_the_window(self):
        consensus = LiveConsensus()
        for stamp in (0, 0.5, 1):
            consensus.observe("neutral", stamp)
        self.assertFalse(consensus.expire(2.9))
        self.assertTrue(consensus.expire(3.01))
        self.assertIsNone(consensus.observe("neutral", 4))
        consensus.reset()
        self.assertIsNone(consensus.label)


if __name__ == "__main__":
    unittest.main()
