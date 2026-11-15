"""Source-backed fare calculations for supported scheduled services."""
from decimal import Decimal

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


def for_plan(result, stop_names, route_info=None):
    if not result.get('found'):
        return {'status':'unknown','reason':'No itinerary to price.'}
    supported=[];unknown=[];cttransit_seen=False
    for leg in result.get('legs',[]):
        if leg.get('kind')!='transit':continue
        route=leg.get('route','')
        if route=='hartford:HART':
            fare=hartford_line_fare(stop_names.get(leg['from_stop'],''),stop_names.get(leg['to_stop'],''))
            if fare['status']=='supported':supported.append(fare)
            else:unknown.append(fare['reason'])
        elif route.startswith('cttransit:'):
            info=(route_info or {}).get(route,{})
            short=str(info.get('short',''))
            if short.isdigit() and 901<=int(short)<=971:
                unknown.append(f'CTtransit express route {short} needs a zone count.')
            else:
                cttransit_seen=True
        else:unknown.append(f'No fare table is loaded for {route}.')
    if cttransit_seen:
        supported.append({'status':'supported','amount':'1.75','currency':'USD','product':'Adult CTtransit local 2-hour fare','source_url':CTTRANSIT_SOURCE,'note':'Includes unlimited transfers during the two-hour validity window.'})
    if unknown:return {'status':'partial' if supported else 'unknown','supported_legs':supported,'unknown_reasons':unknown,'note':'Fare is not a guarantee of ticket validity, discounts, transfers or availability.'}
    if not supported:return {'status':'unknown','reason':'This itinerary has no supported fare-bearing rail leg.'}
    total=sum((Decimal(x['amount']) for x in supported),Decimal('0'))
    return {'status':'supported','amount':f'{total:.2f}','currency':'USD','product':'Adult CTrail Hartford Line one-way','legs':supported,'note':'Walking is not charged. This does not price discounts, passes or unsupported agencies.'}
