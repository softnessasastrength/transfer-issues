import unittest
import fares


class FareTests(unittest.TestCase):
    def test_hartford_line_adult_matrix_is_symmetric(self):
        a=fares.hartford_line_fare('HARTFORD','SPRINGFIELD')
        b=fares.hartford_line_fare('SPRINGFIELD','HARTFORD')
        self.assertEqual(a['status'], 'supported')
        self.assertEqual(a['amount'], '6.75')
        self.assertEqual(a['amount'], b['amount'])

    def test_unknown_station_does_not_get_guessed(self):
        result=fares.hartford_line_fare('Hartford','New York Penn')
        self.assertEqual(result['status'], 'unknown')

    def test_cttransit_local_fare_is_explicit(self):
        result=fares.for_plan({'found':True,'legs':[{'kind':'transit','route':'cttransit:100'}]}, {}, {'cttransit:100':{'short':'100'}})
        self.assertEqual(result['status'], 'supported')
        self.assertEqual(result['amount'], '1.75')

    def test_express_fare_requires_zone_context(self):
        result=fares.for_plan({'found':True,'legs':[{'kind':'transit','route':'cttransit:905'}]}, {}, {'cttransit:905':{'short':'905'}})
        self.assertEqual(result['status'], 'unknown')
        self.assertIn('zone count', result['unknown_reasons'][0])


if __name__ == '__main__':
    unittest.main()
