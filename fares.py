"""Source-backed fare calculations for supported scheduled services.

Every fare figure in this module comes from an official agency source
recorded next to the data, together with the date it was retrieved.
Anything that cannot be priced from published material returns an
explicit unknown instead of a guess. All amounts are rough planning
estimates, not ticket guarantees.
"""
from decimal import Decimal

# Date the fare data in this module was retrieved from the official
# sources cited beside each table.
RETRIEVED = '2026-11-15'

HARTFORD_LINE_SOURCE = 'https://hartfordline.com/fares-schedules/ticketing/'
HARTFORD_LINE_FARE_TABLE = 'https://hartfordline.com/wp-content/uploads/2026/06/CTrail-Fares-2026-updates.xlsx-Hartford-Line-Fares.pdf'
HARTFORD_LINE_EFFECTIVE = '2026-07-01'
CTTRANSIT_SOURCE = 'https://www.cttransit.com/fares'
STATIONS = ('new haven', 'wallingford', 'meriden', 'berlin', 'hartford', 'windsor', 'windsor locks', 'springfield')
# Adult regular one-way fares, lower triangle of the official station matrix.
ONE_WAY = {
 ('new haven','wallingford'): Decimal('4.25'),
 ('new haven','meriden'): Decimal('5.50'), ('wallingford','meriden'): Decimal('3.50'),
 ('new haven','berlin'): Decimal('6.75'), ('wallingford','berlin'): Decimal('4.25'), ('meriden','berlin'): Decimal('3.50'),
 ('new haven','hartford'): Decimal('9.25'), ('wallingford','hartford'): Decimal('6.25'), ('meriden','hartford'): Decimal('5.25'), ('berlin','hartford'): Decimal('4.00'),
 ('new haven','windsor'): Decimal('10.50'), ('wallingford','windsor'): Decimal('7.50'), ('meriden','windsor'): Decimal('6.50'), ('berlin','windsor'): Decimal('5.25'), ('hartford','windsor'): Decimal('3.50'),
 ('new haven','windsor locks'): Decimal('11.50'), ('wallingford','windsor locks'): Decimal('8.75'), ('meriden','windsor locks'): Decimal('7.25'), ('berlin','windsor locks'): Decimal('6.00'), ('hartford','windsor locks'): Decimal('4.00'), ('windsor','windsor locks'): Decimal('3.50'),
 ('new haven','springfield'): Decimal('14.75'), ('wallingford','springfield'): Decimal('11.75'), ('meriden','springfield'): Decimal('10.50'), ('berlin','springfield'): Decimal('9.25'), ('hartford','springfield'): Decimal('6.75'), ('windsor','springfield'): Decimal('5.50'), ('windsor locks','springfield'): Decimal('4.75'),
}


def station_key(name):
    value=' '.join(str(name).lower().replace('-', ' ').split())
    if 'new haven' in value and 'state' not in value:return 'new haven'
    for station in STATIONS[1:]:
        if station in value:return station
    return None


def hartford_line_fare(from_name, to_name):
    origin,destination=station_key(from_name),station_key(to_name)
    if not origin or not destination or origin==destination:
        return {'status':'unknown','reason':'Both stops must be distinct published Hartford Line fare stations.'}
    pair=tuple(sorted((origin,destination),key=STATIONS.index))
    amount=ONE_WAY.get(pair)
    if amount is None:
        return {'status':'unknown','reason':'No published adult one-way fare is available for this station pair.'}
    return {'status':'supported','amount':str(amount),'currency':'USD','product':'Adult CTrail Hartford Line one-way','effective_from':HARTFORD_LINE_EFFECTIVE,'source_url':HARTFORD_LINE_FARE_TABLE,'purchase_url':HARTFORD_LINE_SOURCE}


# ---------------------------------------------------------------------------
# CTrail Shore Line East — adult one-way station-pair matrix.
# Source: CTDOT "CTrail Fares (2026 updates) — Shore Line East Fares",
# effective 2026-07-01, retrieved 2026-11-15. The published form is a
# station-pair matrix (not zones), so it is modelled the same way as the
# Hartford Line table.
SHORE_LINE_EAST_FARE_TABLE = 'https://portal.ct.gov/dot/-/media/dot/public-transportation/proposed-transit-changes/ctrail-fares-2026-updatesxlsx-shore-line-east-fares.pdf?rev=19e881c997a949c3947660c2dffefe6d'
SHORE_LINE_EAST_EFFECTIVE = '2026-07-01'
SLE_STATIONS = ('new haven', 'branford', 'guilford', 'madison', 'clinton', 'westbrook', 'old saybrook', 'new london')
SLE_ONE_WAY = {
 ('new haven','branford'): Decimal('4.00'),
 ('new haven','guilford'): Decimal('5.00'), ('branford','guilford'): Decimal('4.00'),
 ('new haven','madison'): Decimal('5.75'), ('branford','madison'): Decimal('4.00'), ('guilford','madison'): Decimal('4.00'),
 ('new haven','clinton'): Decimal('6.50'), ('branford','clinton'): Decimal('5.25'), ('guilford','clinton'): Decimal('5.25'), ('madison','clinton'): Decimal('5.25'),
 ('new haven','westbrook'): Decimal('7.25'), ('branford','westbrook'): Decimal('5.25'), ('guilford','westbrook'): Decimal('5.25'), ('madison','westbrook'): Decimal('5.25'), ('clinton','westbrook'): Decimal('4.00'),
 ('new haven','old saybrook'): Decimal('8.50'), ('branford','old saybrook'): Decimal('5.25'), ('guilford','old saybrook'): Decimal('5.25'), ('madison','old saybrook'): Decimal('5.25'), ('clinton','old saybrook'): Decimal('4.00'), ('westbrook','old saybrook'): Decimal('4.00'),
 ('new haven','new london'): Decimal('11.75'), ('branford','new london'): Decimal('8.50'), ('guilford','new london'): Decimal('8.50'), ('madison','new london'): Decimal('8.50'), ('clinton','new london'): Decimal('5.25'), ('westbrook','new london'): Decimal('5.25'), ('old saybrook','new london'): Decimal('5.25'),
}


def sle_station_key(name):
    value=' '.join(str(name).lower().replace('-', ' ').split())
    # Both New Haven stations (Union Station and State Street) are the
    # published "New Haven" fare point for Shore Line East.
    if 'state street' in value:return 'new haven'
    for station in SLE_STATIONS:
        if station in value:return station
    return None


def shore_line_east_fare(from_name, to_name):
    origin,destination=sle_station_key(from_name),sle_station_key(to_name)
    if not origin or not destination or origin==destination:
        return {'status':'unknown','reason':'Both stops must be distinct published Shore Line East fare stations.'}
    pair=tuple(sorted((origin,destination),key=SLE_STATIONS.index))
    amount=SLE_ONE_WAY.get(pair)
    if amount is None:
        return {'status':'unknown','reason':'No published adult one-way fare is available for this station pair.'}
    return {'status':'supported','amount':str(amount),'currency':'USD','product':'Adult CTrail Shore Line East one-way','basis':'station pair','effective_from':SHORE_LINE_EAST_EFFECTIVE,'as_of':RETRIEVED,'estimate':'rough','source_url':SHORE_LINE_EAST_FARE_TABLE,'note':'Rough estimate from the official CTrail Shore Line East fare table.'}


# ---------------------------------------------------------------------------
# CTtransit express zone fares.
# Official structure (CTtransit express timetable/map fare panels, e.g. the
# route 921 map, retrieved 2026-11-15): "Express service fares are
# distance-based and are determined by the number of fare zones traveled.
# Fare zones are labeled A thru F. ... The minimum express bus fare is
# 2 zones and the maximum fare is 5 zones." The published boarding/exit
# matrix is exactly zones = min(5, max(2, |boarding - exit| + 1)).
# One-way fares by zones traveled, identical across the official express
# timetable fare panels checked (routes 901, 903, 905, 907, 918, 921):
# 2 zones $3.20, 3 zones $4.10, 4 zones $5.00, 5 zones $6.00.
# GAP: which zone a particular stop sits in is published only as geography
# on the printed route maps. CTtransit's GTFS ships an empty zone_id for
# every stop and no fare_attributes/fare_rules, so stop-level zone pricing
# inside itinerary plans stays an explicit unknown; zone pairs supplied by
# the caller can be priced exactly.
EXPRESS_ZONE_SOURCE = 'https://www.cttransit.com/sites/default/files/maps/route/e_921mddltwnoldsybrk_map_1_0.pdf'
EXPRESS_ZONE_LETTERS = 'ABCDEF'
EXPRESS_ZONE_ONE_WAY = {2: Decimal('3.20'), 3: Decimal('4.10'), 4: Decimal('5.00'), 5: Decimal('6.00')}
# Express routes verified route-by-route against CTtransit's current
# official GTFS route list and express timetable fare panels, retrieved
# 2026-11-15. Every 9xx route in the current feed is one of these; a 9xx
# short name outside this set is NOT assumed to be express.
EXPRESS_ROUTES = frozenset({'901','903','904','905','906','910','912','913','914','918','919','921','923','926','927','928','940','950','971'})
# CTtransit 2-Hour Pass (transfer) policy, official text at
# https://www.cttransit.com/fares/transfers (retrieved 2026-11-15):
# fareboxes issue 2-Hour Passes; local passes include unlimited FREE local
# transfers with additional payment required on express services (the
# difference in fares, per CTtransit's Token Transit guidance); "Express
# 2-Hour passes retain the full value of the original zone fare paid,
# providing unlimited local and express rides for the number of zones
# paid. Travel on a route that charges a higher zone fare would require
# additional payment." The window is anchored at the original purchase;
# the official text does not say a top-up restarts it, so it is not
# restarted here. Rail fares never interact with the bus pass.
CTTRANSIT_TRANSFERS_SOURCE = 'https://www.cttransit.com/fares/transfers'
TRANSFER_WINDOW_SECONDS = 7200


def zones_traveled(board_zone, exit_zone):
    board=str(board_zone or '').strip().upper()
    exit_=str(exit_zone or '').strip().upper()
    if len(board)!=1 or len(exit_)!=1 or board not in EXPRESS_ZONE_LETTERS or exit_ not in EXPRESS_ZONE_LETTERS:
        return None
    return min(5, max(2, abs(EXPRESS_ZONE_LETTERS.index(board)-EXPRESS_ZONE_LETTERS.index(exit_))+1))


def cttransit_express_fare(board_zone, exit_zone):
    count=zones_traveled(board_zone, exit_zone)
    if count is None:
        return {'status':'unknown','reason':'Express zone fares require published fare zones A-F for both boarding and exit.'}
    amount=EXPRESS_ZONE_ONE_WAY[count]
    return {'status':'supported','amount':str(amount),'currency':'USD','product':f'Adult CTtransit express one-way ({count} zones)','basis':'zone count','zones_traveled':count,'as_of':RETRIEVED,'estimate':'rough','source_url':EXPRESS_ZONE_SOURCE,'note':'Rough estimate from the official CTtransit express zone fare table; the fare depends on the published per-route fare zones (A-F) boarded and exited.'}


def cttransit_route_class(short):
    short=str(short or '')
    if short in EXPRESS_ROUTES:return 'express'
    if short.isdigit() and 901<=int(short)<=971:return 'express-unverified'
    return 'local'


def _local_fare_entry():
    return {'status':'supported','amount':'1.75','currency':'USD','product':'Adult CTtransit local 2-hour fare','source_url':CTTRANSIT_SOURCE,'note':'Includes unlimited transfers during the two-hour validity window.'}


def cttransit_local_fare():
    return _local_fare_entry()


def _price_cttransit(ct_legs, route_info, express_zones):
    """Price the CTtransit legs of an itinerary in order.

    ct_legs is a list of (position, leg) where position indexes the
    itinerary's legs list (used to look up caller-supplied express zones).
    Returns (outcomes, legacy_local_seen): outcomes maps position to
    ('entry', fare dict) or ('reason', text) or ('skip', None).

    When no leg carries a departure time and no express zones were
    supplied, the historical behaviour is preserved exactly: local legs
    collapse into a single 2-hour fare entry and express legs are an
    explicit unknown. With times (or supplied zones) the official 2-Hour
    Pass policy is applied leg by leg.
    """
    window = express_zones is not None or all(isinstance(leg.get('departure'), (int, float)) for _, leg in ct_legs)
    outcomes={}
    if not window:
        local_seen=False
        for position, leg in ct_legs:
            short=str((route_info or {}).get(leg.get('route',''),{}).get('short',''))
            cls=cttransit_route_class(short)
            if cls=='local':
                local_seen=True;outcomes[position]=('skip',None)
            elif cls=='express':
                outcomes[position]=('reason',f'CTtransit express route {short} needs a zone count.')
            else:
                outcomes[position]=('reason',f'CTtransit route {short} is in the 900 express series but is not a verified express route in current official material; fare not priced.')
        return outcomes, local_seen
    pass_state=None  # {'expires': seconds|None, 'kind': 'local'|'express', 'value': Decimal, 'zones': int|None}
    pass_broken=False
    for position, leg in ct_legs:
        short=str((route_info or {}).get(leg.get('route',''),{}).get('short',''))
        cls=cttransit_route_class(short)
        dep=leg.get('departure')
        active=pass_state is not None and dep is not None and pass_state['expires'] is not None and dep<=pass_state['expires']
        if cls=='express-unverified':
            outcomes[position]=('reason',f'CTtransit route {short} is in the 900 express series but is not a verified express route in current official material; fare not priced.')
            pass_state=None;pass_broken=True;continue
        if cls=='express':
            zones=(express_zones or {}).get(position)
            if not zones:
                outcomes[position]=('reason',f'CTtransit express route {short} needs a zone count.')
                pass_state=None;pass_broken=True;continue
            fare=cttransit_express_fare(zones[0], zones[1])
            if fare['status']!='supported':
                outcomes[position]=('reason',fare['reason'])
                pass_state=None;pass_broken=True;continue
            amount=Decimal(fare['amount']);count=fare['zones_traveled']
            if pass_broken:
                entry=dict(fare);entry['note']=fare['note']+' Priced as a new purchase: an earlier unpriced CTtransit leg may have provided 2-Hour Pass coverage.'
                outcomes[position]=('entry',entry)
                pass_state={'expires':dep+TRANSFER_WINDOW_SECONDS if dep is not None else None,'kind':'express','value':amount,'zones':count}
                pass_broken=False;continue
            if active:
                if pass_state['kind']=='express' and count<=pass_state['zones']:
                    entry=dict(fare);entry['amount']='0.00';entry['covered']=True
                    entry['note']='Covered by the CTtransit Express 2-Hour Pass purchased earlier in this itinerary: the pass provides unlimited local and express rides for the number of zones paid.'
                    outcomes[position]=('entry',entry);continue
                topup=amount-pass_state['value']
                entry=dict(fare);entry['amount']=f'{topup:.2f}'
                entry['note']='Additional payment inside the CTtransit 2-Hour Pass window: the pass retains the full value of the fare already paid, and travel at a higher zone fare requires the difference.'
                outcomes[position]=('entry',entry)
                pass_state={'expires':pass_state['expires'],'kind':'express','value':amount,'zones':count}
                continue
            outcomes[position]=('entry',fare)
            pass_state={'expires':dep+TRANSFER_WINDOW_SECONDS if dep is not None else None,'kind':'express','value':amount,'zones':count}
            continue
        # Local leg (CTfastrak prices as local service).
        if pass_broken:
            entry=_local_fare_entry()
            entry['note']='Priced as a new purchase: an earlier unpriced CTtransit leg may have provided 2-Hour Pass coverage. '+entry['note']
            outcomes[position]=('entry',entry)
            pass_state={'expires':dep+TRANSFER_WINDOW_SECONDS if dep is not None else None,'kind':'local','value':Decimal('1.75'),'zones':None}
            pass_broken=False;continue
        if active:
            entry=_local_fare_entry();entry['amount']='0.00';entry['covered']=True
            entry['note']='Covered by the CTtransit 2-Hour Pass purchased earlier in this itinerary; no additional fare.'
            outcomes[position]=('entry',entry);continue
        outcomes[position]=('entry',_local_fare_entry())
        pass_state={'expires':dep+TRANSFER_WINDOW_SECONDS if dep is not None else None,'kind':'local','value':Decimal('1.75'),'zones':None}
    return outcomes, False


# ---------------------------------------------------------------------------
# PVTA — currently fare-free.
# MassDOT's FY27 Regional Transit Authorities operating assistance
# (mass.gov, June 10, 2026) funds a "fare free grant program that supports
# RTAs in providing systemwide, year-round fare free services"; PVTA's
# MassDOT contract 134462 runs July 1, 2026 - June 30, 2027, and PVTA's
# FY2025 financial statements record that fixed-route and paratransit
# services are free to all passengers and that "fares are only collected
# in the B79 Amherst to Worcester Route". Retrieved 2026-11-15. The
# pre-program fares still shown on PVTA's fares page ($1.50 adult etc.)
# are historical context only and are deliberately NOT modelled; the B79
# table on that same page is current and is modelled below.
PVTA_FARE_FREE_SOURCE = 'https://www.mass.gov/doc/fy27-rtas-state-operating-assistance-presented-to-the-finance-audit-committee-on-june-10-2026/download'
PVTA_FARE_FREE_THROUGH = '2027-06-30'
PVTA_FARES_PAGE = 'https://www.pvta.com/bus_service/fares.php'
B79_TOWNS = ('amherst', 'belchertown', 'ware', 'west brookfield', 'brookfield', 'east brookfield', 'spencer', 'leicester', 'worcester')
# Adult one-way fares from the published B79 fare table on PVTA's fares
# page. None = the table marks the pair "X" (no fare published for that
# pair), which is reported as an explicit unknown, never interpolated.
B79_ONE_WAY = {
 ('amherst','belchertown'): Decimal('1.50'), ('amherst','ware'): Decimal('1.50'), ('amherst','west brookfield'): Decimal('3.50'), ('amherst','brookfield'): Decimal('6.00'), ('amherst','east brookfield'): Decimal('6.00'), ('amherst','spencer'): Decimal('6.00'), ('amherst','leicester'): Decimal('6.00'), ('amherst','worcester'): Decimal('9.00'),
 ('belchertown','ware'): Decimal('1.50'), ('belchertown','west brookfield'): Decimal('3.50'), ('belchertown','brookfield'): Decimal('6.00'), ('belchertown','east brookfield'): Decimal('6.00'), ('belchertown','spencer'): Decimal('6.00'), ('belchertown','leicester'): Decimal('6.00'), ('belchertown','worcester'): Decimal('9.00'),
 ('ware','west brookfield'): Decimal('3.50'), ('ware','brookfield'): Decimal('6.00'), ('ware','east brookfield'): Decimal('6.00'), ('ware','spencer'): Decimal('6.00'), ('ware','leicester'): Decimal('6.00'), ('ware','worcester'): Decimal('9.00'),
 ('west brookfield','brookfield'): Decimal('3.50'), ('west brookfield','east brookfield'): Decimal('3.50'), ('west brookfield','spencer'): Decimal('3.50'), ('west brookfield','leicester'): Decimal('3.50'), ('west brookfield','worcester'): Decimal('6.00'),
 ('brookfield','east brookfield'): Decimal('3.50'), ('brookfield','spencer'): Decimal('3.50'), ('brookfield','leicester'): Decimal('3.50'), ('brookfield','worcester'): Decimal('6.00'),
 ('east brookfield','spencer'): None, ('east brookfield','leicester'): None, ('east brookfield','worcester'): None,
 ('spencer','leicester'): None, ('spencer','worcester'): None,
 ('leicester','worcester'): None,
}


def pvta_fare_free():
    return {'status':'supported','amount':'0.00','currency':'USD','product':'PVTA fixed-route — currently fare-free','basis':'flat (fare-free program)','as_of':RETRIEVED,'estimate':'rough','source_url':PVTA_FARE_FREE_SOURCE,'note':f'Rough estimate: PVTA fixed-route service is fare-free under the Massachusetts fare-free RTA program as of {RETRIEVED}; state funding runs through {PVTA_FARE_FREE_THROUGH}. The B79 Amherst-Worcester route is excluded from the program and is priced from its published fare table.'}


def b79_town_key(name):
    value=' '.join(str(name).lower().replace('-', ' ').split())
    for town in ('west brookfield', 'east brookfield', 'belchertown', 'amherst', 'ware', 'brookfield', 'spencer', 'leicester', 'worcester'):
        if town in value:return town
    return None


def pvta_b79_fare(from_name, to_name):
    origin,destination=b79_town_key(from_name),b79_town_key(to_name)
    if not origin or not destination or origin==destination:
        return {'status':'unknown','reason':'Both stops must be in distinct towns named in the published PVTA B79 fare table.'}
    pair=tuple(sorted((origin,destination),key=B79_TOWNS.index))
    amount=B79_ONE_WAY.get(pair)
    if amount is None:
        return {'status':'unknown','reason':'The official PVTA B79 fare table publishes no fare for this pair (marked X in the table).'}
    return {'status':'supported','amount':str(amount),'currency':'USD','product':'Adult PVTA B79 one-way','basis':'station pair (town)','as_of':RETRIEVED,'estimate':'rough','source_url':PVTA_FARES_PAGE,'note':'Rough estimate from the official PVTA B79 fare table; the B79 is the one PVTA route still collecting fares.'}


def for_plan(result, stop_names, route_info=None, express_zones=None):
    if not result.get('found'):
        return {'status':'unknown','reason':'No itinerary to price.'}
    legs=result.get('legs',[])
    ct_positions=[i for i, leg in enumerate(legs) if leg.get('kind')=='transit' and str(leg.get('route','')).startswith('cttransit:')]
    ct_outcomes={};legacy_local=False
    if ct_positions:
        ct_outcomes,legacy_local=_price_cttransit([(i, legs[i]) for i in ct_positions], route_info, express_zones)
    supported=[];unknown=[];new_style=False
    for i, leg in enumerate(legs):
        if leg.get('kind')!='transit':continue
        route=leg.get('route','')
        if i in ct_outcomes:
            kind,payload=ct_outcomes[i]
            if kind=='entry':
                supported.append(payload)
                if 'as_of' in payload or payload.get('covered'):new_style=True
            elif kind=='reason':
                unknown.append(payload)
            continue
        if route=='hartford:HART':
            fare=hartford_line_fare(stop_names.get(leg['from_stop'],''),stop_names.get(leg['to_stop'],''))
            if fare['status']=='supported':supported.append(fare)
            else:unknown.append(fare['reason'])
        elif route=='hartford:SLE':
            new_style=True
            fare=shore_line_east_fare(stop_names.get(leg['from_stop'],''),stop_names.get(leg['to_stop'],''))
            if fare['status']=='supported':supported.append(fare)
            else:unknown.append(fare['reason'])
        elif route.startswith('pvta:'):
            new_style=True
            if route.split(':',1)[1]=='B79':
                fare=pvta_b79_fare(stop_names.get(leg['from_stop'],''),stop_names.get(leg['to_stop'],''))
                if fare['status']=='supported':supported.append(fare)
                else:unknown.append(fare['reason'])
            else:
                supported.append(pvta_fare_free())
        else:unknown.append(f'No fare table is loaded for {route}.')
    if legacy_local:
        supported.append(_local_fare_entry())
    if unknown:return {'status':'partial' if supported else 'unknown','supported_legs':supported,'unknown_reasons':unknown,'note':'Fare is not a guarantee of ticket validity, discounts, transfers or availability.'}
    if not supported:return {'status':'unknown','reason':'This itinerary has no supported fare-bearing rail leg.'}
    total=sum((Decimal(x['amount']) for x in supported),Decimal('0'))
    products={x['product'] for x in supported}
    product=products.pop() if len(products)==1 else 'Adult one-way fares (rough estimate)'
    out={'status':'supported','amount':f'{total:.2f}','currency':'USD','product':product,'legs':supported,'note':'Walking is not charged. This does not price discounts, passes or unsupported agencies.'}
    if new_style:
        out['estimate']='rough';out['as_of']=RETRIEVED
    return out
