import unittest
from collections import namedtuple

from evaluation.jobvalues.value import due, features, job_value, load_model, rank_cell_jobs

Job = namedtuple('Job', 'operation target owner')


class JobValueTest(unittest.TestCase):
    def setUp(self):
        self.tile = {'kind': 'PASTURE', 'animal': 'COW', 'fed_today': False,
                     'consecutive_unfed': 1, 'cared_today': False,
                     'fertilizer_available': 1, 'yield_units': 2}
        self.obs = {'player': 0, 'day': 7, 'hour': 12,
                    'farms': [{'tiles': [[self.tile]], 'farmer': [0, 0], 'hands': []}],
                    'private': {'inventories': [{'WHEAT': 2}]},
                    'market': {'prices': {'MILK': 120}}}
        # Two one-leaf trees make scaling and the same-cell route explicit.
        leaf = lambda score: {'feature': [-2], 'threshold': [-2], 'left': [-1],
                              'right': [-1], 'value': [score]}
        self.model = {'within': leaf(.7), 'next': leaf(.2), 'scale': 1000}

    def test_animal_due_and_features(self):
        self.assertEqual(due(self.tile, {'WHEAT': 2}, 7),
                         ['COLLECT_FERTILIZER', 'FEED', 'HARVEST', 'CARE'])
        row = features(self.obs, 'FEED', (0, 0), {'WHEAT': 2}, (0, 0))
        self.assertEqual((row[11], row[14], row[17], row[18]), (1, 2, 120, 0))

    def test_drop_in_signature_and_order(self):
        jobs = [Job('FEED', (0, 0), None), Job('CARE', (0, 0), None)]
        self.assertEqual(job_value(self.obs, jobs, self.model), 1400)
        self.assertEqual(rank_cell_jobs(self.obs, jobs, 0, self.model), jobs)

    def test_bundled_model_loads_and_scores(self):
        model = load_model()
        self.assertIn('within', model)
        self.assertIn('next', model)
        score = job_value(self.obs, [Job('FEED', (0, 0), None)], model)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, model['scale'])


if __name__ == '__main__':
    unittest.main()
