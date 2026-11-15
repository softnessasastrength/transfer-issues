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

    def test_hartford_line_only_plan_keeps_legacy_product_label(self):
        leg={'kind':'transit','route':'hartford:HART','from_stop':'a','to_stop':'b'}
        result=fares.for_plan({'found':True,'legs':[leg]}, {'a':'HARTFORD','b':'SPRINGFIELD'}, {})
        self.assertEqual(result['status'], 'supported')
        self.assertEqual(result['amount'], '6.75')
        self.assertEqual(result['product'], 'Adult CTrail Hartford Line one-way')
        self.assertNotIn('estimate', result)

    def test_local_only_plan_product_names_the_bus_fare(self):
        result=fares.for_plan({'found':True,'legs':[{'kind':'transit','route':'cttransit:100'}]}, {}, {'cttransit:100':{'short':'100'}})
        self.assertEqual(result['product'], 'Adult CTtransit local 2-hour fare')

    def test_untimed_local_legs_collapse_to_one_pass(self):
        legs=[{'kind':'transit','route':'cttransit:100'},{'kind':'transit','route':'cttransit:101'}]
        info={'cttransit:100':{'short':'100'},'cttransit:101':{'short':'101'}}
        result=fares.for_plan({'found':True,'legs':legs}, {}, info)
        self.assertEqual(result['status'], 'supported')
        self.assertEqual(result['amount'], '1.75')
        self.assertEqual(len(result['legs']), 1)

    def test_unverified_900_series_route_is_not_assumed_express(self):
        result=fares.for_plan({'found':True,'legs':[{'kind':'transit','route':'cttransit:902'}]}, {}, {'cttransit:902':{'short':'902'}})
        self.assertEqual(result['status'], 'unknown')
        self.assertIn('not a verified express route', result['unknown_reasons'][0])


class ShoreLineEastTests(unittest.TestCase):
    def test_matrix_is_symmetric(self):
        a=fares.shore_line_east_fare('NEW HAVEN UNION STATION','NEW LONDON')
        b=fares.shore_line_east_fare('NEW LONDON','NEW HAVEN UNION STATION')
        self.assertEqual(a['status'], 'supported')
        self.assertEqual(a['amount'], '11.75')
        self.assertEqual(a['amount'], b['amount'])
        self.assertEqual(a['basis'], 'station pair')
        self.assertEqual(a['estimate'], 'rough')

    def test_state_street_is_the_new_haven_fare_point(self):
        result=fares.shore_line_east_fare('STATE STREET STATION','BRANFORD')
        self.assertEqual(result['status'], 'supported')
        self.assertEqual(result['amount'], '4.00')

    def test_unknown_station_does_not_get_guessed(self):
        result=fares.shore_line_east_fare('BRANFORD','MYSTIC')
        self.assertEqual(result['status'], 'unknown')

    def test_sle_leg_prices_inside_a_plan(self):
        leg={'kind':'transit','route':'hartford:SLE','from_stop':'a','to_stop':'b'}
        result=fares.for_plan({'found':True,'legs':[leg]}, {'a':'NEW HAVEN UNION STATION','b':'OLD SAYBROOK'}, {})
        self.assertEqual(result['status'], 'supported')
        self.assertEqual(result['amount'], '8.50')
        self.assertEqual(result['estimate'], 'rough')
        self.assertEqual(result['as_of'], '2026-11-15')


class ExpressZoneTests(unittest.TestCase):
    def test_zones_traveled_matches_the_published_matrix(self):
        self.assertEqual(fares.zones_traveled('A','A'), 2)
        self.assertEqual(fares.zones_traveled('A','B'), 2)
        self.assertEqual(fares.zones_traveled('A','C'), 3)
        self.assertEqual(fares.zones_traveled('C','E'), 3)
        self.assertEqual(fares.zones_traveled('A','F'), 5)
        self.assertEqual(fares.zones_traveled('F','A'), 5)
        self.assertEqual(fares.zones_traveled('E','F'), 2)

    def test_zones_traveled_rejects_unpublished_zones(self):
        self.assertIsNone(fares.zones_traveled('G','A'))
        self.assertIsNone(fares.zones_traveled('','A'))
        self.assertIsNone(fares.zones_traveled(None,'A'))

    def test_express_fare_by_zone_count(self):
        result=fares.cttransit_express_fare('A','C')
        self.assertEqual(result['status'], 'supported')
        self.assertEqual(result['amount'], '4.10')
        self.assertEqual(result['zones_traveled'], 3)
        self.assertEqual(result['basis'], 'zone count')
        self.assertEqual(fares.cttransit_express_fare('a','f')['amount'], '6.00')
        self.assertEqual(fares.cttransit_express_fare('B','B')['amount'], '3.20')

    def test_express_fare_rejects_bad_zones(self):
        self.assertEqual(fares.cttransit_express_fare('A','Z')['status'], 'unknown')

    def test_route_classification_uses_the_verified_list(self):
        self.assertEqual(fares.cttransit_route_class('905'), 'express')
        self.assertEqual(fares.cttransit_route_class('921'), 'express')
        self.assertEqual(fares.cttransit_route_class('971'), 'express')
        self.assertEqual(fares.cttransit_route_class('902'), 'express-unverified')
        self.assertEqual(fares.cttransit_route_class('100'), 'local')
        self.assertEqual(fares.cttransit_route_class(''), 'local')


T0=8*3600  # 08:00 in service-day seconds


def _bus(route, dep):
    return {'kind':'transit','route':route,'from_stop':'x','to_stop':'y','departure':dep,'arrival':dep+600}


class TransferWindowTests(unittest.TestCase):
    INFO={'cttransit:905':{'short':'905'},'cttransit:100':{'short':'100'}}

    def test_express_purchase_covers_local_leg_inside_window(self):
        legs=[_bus('cttransit:905',T0),_bus('cttransit:100',T0+5400)]
        result=fares.for_plan({'found':True,'legs':legs}, {}, self.INFO, express_zones={0:('A','C')})
        self.assertEqual(result['status'], 'supported')
        self.assertEqual(result['amount'], '4.10')
        self.assertEqual(result['legs'][1]['amount'], '0.00')
        self.assertTrue(result['legs'][1]['covered'])

    def test_window_boundary_is_inclusive_then_expires(self):
        legs=[_bus('cttransit:905',T0),_bus('cttransit:100',T0+7200)]
        result=fares.for_plan({'found':True,'legs':legs}, {}, self.INFO, express_zones={0:('A','C')})
        self.assertEqual(result['amount'], '4.10')
        legs=[_bus('cttransit:905',T0),_bus('cttransit:100',T0+7201)]
        result=fares.for_plan({'found':True,'legs':legs}, {}, self.INFO, express_zones={0:('A','C')})
        self.assertEqual(result['amount'], '5.85')

    def test_local_to_express_inside_window_charges_the_difference(self):
        legs=[_bus('cttransit:100',T0),_bus('cttransit:905',T0+3600)]
        result=fares.for_plan({'found':True,'legs':legs}, {}, self.INFO, express_zones={1:('A','C')})
        self.assertEqual(result['status'], 'supported')
        self.assertEqual(result['amount'], '4.10')
        self.assertEqual(result['legs'][1]['amount'], '2.35')

    def test_express_to_express_higher_zone_charges_the_difference(self):
        legs=[_bus('cttransit:905',T0),_bus('cttransit:905',T0+3600)]
        result=fares.for_plan({'found':True,'legs':legs}, {}, self.INFO, express_zones={0:('A','C'),1:('A','E')})
        self.assertEqual(result['amount'], '6.00')
        self.assertEqual(result['legs'][1]['amount'], '1.90')

    def test_express_to_express_within_zones_paid_is_covered(self):
        legs=[_bus('cttransit:905',T0),_bus('cttransit:905',T0+3600)]
        result=fares.for_plan({'found':True,'legs':legs}, {}, self.INFO, express_zones={0:('A','C'),1:('A','B')})
        self.assertEqual(result['amount'], '4.10')
        self.assertEqual(result['legs'][1]['amount'], '0.00')
        self.assertTrue(result['legs'][1]['covered'])

    def test_second_local_leg_inside_window_is_covered(self):
        legs=[_bus('cttransit:100',T0),_bus('cttransit:100',T0+3600)]
        result=fares.for_plan({'found':True,'legs':legs}, {}, self.INFO)
        self.assertEqual(result['amount'], '1.75')
        self.assertEqual(result['legs'][1]['amount'], '0.00')

    def test_rail_leg_neither_uses_nor_extends_the_bus_pass(self):
        # The transfer policy speaks to bus-to-bus travel only: the rail
        # leg is priced in full, and the second bus leg boards more than
        # two hours after the pass purchase, so it is a new purchase.
        rail={'kind':'transit','route':'hartford:HART','from_stop':'a','to_stop':'b','departure':T0+1800,'arrival':T0+5400}
        legs=[_bus('cttransit:100',T0),rail,_bus('cttransit:100',T0+3*3600)]
        names={'a':'HARTFORD','b':'SPRINGFIELD'}
        result=fares.for_plan({'found':True,'legs':legs}, names, self.INFO)
        self.assertEqual(result['status'], 'supported')
        self.assertEqual(result['amount'], '10.25')

    def test_unpriced_express_leg_breaks_the_pass_chain(self):
        legs=[_bus('cttransit:100',T0),_bus('cttransit:905',T0+1800),_bus('cttransit:100',T0+3600)]
        result=fares.for_plan({'found':True,'legs':legs}, {}, self.INFO)
        self.assertEqual(result['status'], 'partial')
        self.assertIn('zone count', result['unknown_reasons'][0])
        amounts=[x['amount'] for x in result['supported_legs']]
        self.assertEqual(amounts, ['1.75','1.75'])
        self.assertIn('new purchase', result['supported_legs'][1]['note'])


class PvtaTests(unittest.TestCase):
    def test_fixed_route_is_fare_free_with_dated_provenance(self):
        result=fares.pvta_fare_free()
        self.assertEqual(result['status'], 'supported')
        self.assertEqual(result['amount'], '0.00')
        self.assertIn('fare-free', result['product'])
        self.assertEqual(result['as_of'], '2026-11-15')
        self.assertIn('2027-06-30', result['note'])

    def test_pvta_leg_prices_at_zero_inside_a_plan(self):
        leg={'kind':'transit','route':'pvta:R10','from_stop':'a','to_stop':'b'}
        result=fares.for_plan({'found':True,'legs':[leg]}, {'a':'Holyoke','b':'Springfield'}, {})
        self.assertEqual(result['status'], 'supported')
        self.assertEqual(result['amount'], '0.00')

    def test_b79_uses_its_published_town_table(self):
        result=fares.pvta_b79_fare('Amherst Common (N)','Union Station Garage - Worcester')
        self.assertEqual(result['status'], 'supported')
        self.assertEqual(result['amount'], '9.00')
        self.assertEqual(fares.pvta_b79_fare('Ware Town Hall','Amherst Common (S)')['amount'], '1.50')

    def test_b79_x_pairs_are_explicit_unknowns(self):
        result=fares.pvta_b79_fare('East Brookfield (E)','Union Station Garage - Worcester')
        self.assertEqual(result['status'], 'unknown')
        self.assertIn('no fare for this pair', result['reason'])

    def test_b79_stop_outside_the_table_is_unknown(self):
        result=fares.pvta_b79_fare('Haigis Mall','Ware Town Hall')
        self.assertEqual(result['status'], 'unknown')

    def test_b79_leg_prices_inside_a_plan(self):
        leg={'kind':'transit','route':'pvta:B79','from_stop':'a','to_stop':'b'}
        result=fares.for_plan({'found':True,'legs':[leg]}, {'a':'Amherst Common (N)','b':'Ware Town Hall'}, {})
        self.assertEqual(result['status'], 'supported')
        self.assertEqual(result['amount'], '1.50')


class MixedAgencyTests(unittest.TestCase):
    def test_hartford_line_plus_shore_line_east(self):
        legs=[{'kind':'transit','route':'hartford:HART','from_stop':'a','to_stop':'b'},
              {'kind':'transit','route':'hartford:SLE','from_stop':'c','to_stop':'d'}]
        names={'a':'HARTFORD','b':'SPRINGFIELD','c':'BRANFORD','d':'GUILFORD'}
        result=fares.for_plan({'found':True,'legs':legs}, names, {})
        self.assertEqual(result['status'], 'supported')
        self.assertEqual(result['amount'], '10.75')

    def test_rail_plus_fare_free_bus(self):
        legs=[{'kind':'transit','route':'hartford:HART','from_stop':'a','to_stop':'b'},
              {'kind':'transit','route':'pvta:G1','from_stop':'c','to_stop':'d'}]
        names={'a':'HARTFORD','b':'SPRINGFIELD','c':'Springfield','d':'Chicopee'}
        result=fares.for_plan({'found':True,'legs':legs}, names, {})
        self.assertEqual(result['status'], 'supported')
        self.assertEqual(result['amount'], '6.75')
        self.assertEqual(result['legs'][1]['amount'], '0.00')


if __name__ == '__main__':
    unittest.main()
