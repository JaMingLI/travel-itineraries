"""Derive cross-tab summaries from the eight canonical day fragments.

Only summary panels are rewritten; daily markup is never serialized or changed.
Map coordinates are curated metadata, never inferred from place names.
"""
from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from html import escape
import re
from urllib.parse import parse_qs, urlparse
from bs4 import BeautifulSoup

FX = Decimal('0.22')


def text(node):
    return node.get_text(' ', strip=True) if node else ''


def yen(value):
    found = re.search(r'¥([\d,]+)', value)
    if not found:
        raise ValueError('Missing JPY amount: ' + value)
    return int(found[1].replace(',', ''))


def currency(amount):
    twd = int((Decimal(amount) * FX).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    return f'¥{amount:,} <span class="twd">約 NT${twd:,}</span>'


def fill(node, markup):
    node.clear()
    node.extend(BeautifulSoup(markup, 'html.parser').contents)


def place_key(url):
    return parse_qs(urlparse(url).query).get('query', [url])[0].strip()


def extract_facts(document):
    soup = BeautifulSoup(document, 'html.parser')
    days = []
    for number, day in enumerate(soup.select('.case-card'), 1):
        if day['id'] != f'day-card-{number}':
            raise ValueError('Expected ordered Day 1–8')
        budget = {text(n.dt): yen(text(n.dd)) for n in day.select('.case-money dl > div')}
        budget['total'] = sum(budget.values())
        if budget['total'] != yen(text(day.select_one('.case-money-total'))):
            raise ValueError(f'Day {number}: budget categories disagree with total')
        steps, meals = [], []
        for node in day.select('.agenda-item'):
            step = {'start': text(node.select_one('.time-start')), 'end': text(node.select_one('.time-end')),
                    'title': text(node.select_one('h4')), 'kind': text(node.select_one('.agenda-kind'))}
            steps.append(step)
            kind = node.select_one('.timeline-meal-type')
            if kind:
                meals.append({**step, 'label': text(kind), 'budget': yen(text(node.select_one('.timeline-meal-price')))})
        days.append({'day': number, 'date': text(day.select_one('.case-day > span:last-child')),
                     'title': text(day.select_one('.disclosure-title')), 'summary': text(day.select_one('.case-itinerary')),
                     'budget': budget, 'steps': steps, 'meals': meals,
                     'extras': [{'label': n['data-extra-label'], 'amount': int(n['data-extra-jpy']), 'bookingTime': n.get('data-booking-time'), 'status': n.get('data-booking-status')} for n in day.select('[data-extra-jpy]')],
                     'alternatives': [{'id': plan['data-alternative-plan'], 'steps': [{'start': n['data-start'], 'end': n['data-end'], 'baseMinutes': int(n['data-base']), 'title': text(n).split('｜',1)[-1]} for n in plan.select('.alternative-item')]} for plan in day.select('[data-alternative-plan]')],
                     'routes': [{'label': text(a), 'url': a['href']} for a in day.select('.case-route')],
                     'places': [{'name': text(a).removeprefix('📍 ').removeprefix('🎂 ').removesuffix(' ↗'), 'url': a['href']} for a in day.select('.case-places a')]})
    if len(days) != 8:
        raise ValueError('Exactly eight daily cards required')
    extras_total = sum(e['amount'] for d in days for e in d['extras'])
    return {'schema': 1, 'extrasTotal': extras_total, 'knownTotal': sum(d['budget']['total'] for d in days) + extras_total, 'source': 'src/days/day-01.html … day-08.html', 'exchangeRate': str(FX), 'days': days,
            'totals': {key: sum(d['budget'][key] for d in days) for key in ('交通', '餐飲', '門票', 'total')}}


def synchronize(document, map_data, checklist):
    facts = extract_facts(document)
    soup = BeautifulSoup(document, 'html.parser')
    map_data, checklist = deepcopy(map_data), deepcopy(checklist)
    old_totals = [yen(text(n)) for n in soup.select('#cost-overview .cost-main')]
    original_panels = {key: str(soup.select_one('#view-' + key)) for key in ('overview', 'map', 'budget', 'prepare')}
    for day in facts['days']:
        number, key = day['day'], str(day['day'])
        overview = soup.select_one(f'.overview-day[data-trip-day="{key}"]')
        overview.select_one('small').string = f'DAY {number:02d} · {day["date"]}'
        overview.select_one('strong').string = day['title']
        overview.select_one('p').string = day['summary']
        row = soup.select('#summary tbody tr')[number - 1]
        row.select_one('[data-label="主題"] .phone-cell-value').string = day['title']
        row.select_one('[data-label="主要景點"] .phone-cell-value').string = day['summary']
        dinners = [m for m in day['meals'] if m['label'].startswith('晚餐')]
        fill(row.select_one('[data-label="指定餐點"] .phone-cell-value'), '<br/>'.join(escape(f'{m["start"]}–{m["end"]} {m["label"]}') for m in dinners))
        map_data['tripDays'][key]['date'] = re.match(r'\d+/\d+', day['date'])[0]
        map_data['tripDays'][key]['title'] = day['title']
        map_data['routes'][key] = day['routes'][0]['url']
        map_data['tripDays'][key]['routeLabel'] = day['routes'][0]['label']
        card = soup.select_one(f'[data-real-card="{key}"]')
        card.select_one('.map-day-title').string = f'Day {number} · {day["title"]}'
        links = card.select('a')
        # Each button says which leg it actually opens; no misleading all-day transit claim.
        links[-1]['href'] = day['routes'][0]['url']
        links[-1].string = '🧭 ' + day['routes'][0]['label']
        canonical = {place_key(p['url']): p for p in day['places']}
        for point in map_data['tripDays'][key]['points']:
            if place_key(point['url']) in canonical:
                point.update(canonical[place_key(point['url'])])
        budget_row = soup.select('#cost-overview tbody tr')[number - 1]
        for label, field in [('交通', '交通'), ('食物', '餐飲'), ('門票', '門票'), ('三類小計', 'total')]:
            fill(budget_row.select_one(f'[data-label="{label}"] .phone-cell-value'), currency(day['budget'][field]))
        extra_summary = soup.select_one(f'#day-card-{key} [data-sync-day-known-cost]')
        # Daily fragments remain canonical; cost note is already rendered there.
        food_row = soup.select('#view-budget table')[1].select('tbody tr')[number - 1]
        fill(food_row.select_one('[data-label="全天雙人"] .phone-cell-value'), currency(day['budget']['餐飲']))
        for label, prefix in [('午餐','午餐'), ('點心與飲料','點心'), ('晚餐','晚餐')]:
            matching = [m for m in day['meals'] if m['label'].startswith(prefix)]
            # Day 8 has a shared envelope: never count its two meals twice.
            if matching and number != 8:
                markup = currency(matching[0]['budget'])
                cake = [m for m in day['meals'] if '生日蛋糕' in m['label']]
                if label == '點心與飲料' and cake:
                    markup += '<br/>另生日蛋糕與配件 ' + currency(cake[0]['budget'])
                fill(food_row.select_one(f'[data-label="{label}"] .phone-cell-value'), markup)
    # Verified coordinate from the existing Google Maps audit; dinner was missing from Day 6 map.
    issho = next(p for p in facts['days'][5]['places'] if '一笑' in p['name'])
    points = map_data['tripDays']['6']['points']
    if not any('一笑' in p['name'] for p in points):
        points.append({**issho, 'lat': 34.7068525, 'lng': 135.4971689})
    totals = facts['totals']
    for node, field in zip(soup.select('#cost-overview .cost-main'), ('交通','餐飲','門票','total')):
        fill(node, currency(totals[field]))
    # Remove a legacy duplicate conversion in the overview hero.
    for node in soup.select('#view-overview .chip'):
        if '餐費' in text(node):
            fill(node, f'🍽 雙人餐費上限 {currency(totals["餐飲"])}')
    overview_text = str(soup.select_one('#view-overview'))
    overview_text = overview_text.replace('19:00 從 KIX 起飛，保留慢早餐與補貨安排；先確認退房後行李寄放方式，再依航空公司報到要求與當日列車時間決定離開住宿的時間。', '19:00 從 KIX 起飛；10:00退房，寄放確認後10:40–11:50難波隨吃，12:30取行李、13:15離開住宿，15:15前到出境航廈。寄放未確認就取消難波往返。')
    overview_text = overview_text.replace('2026/10/18交通複核：', '2026/10/19交通複核：').replace('USJ改06:20由新今宮出發。', 'USJ維持06:20離開住宿、步行至JR新今宮；京都河原町至和服店以步行為主，207公車僅作雨天備案。')
    soup.select_one('#view-overview').replace_with(BeautifulSoup(overview_text, 'html.parser'))
    budget = soup.select_one('#view-budget')
    for node in budget.find_all(string=True):
        if '京都市巴士普通均一運賃目前為' in node:
            node.replace_with(str(node).replace('京都市巴士普通均一運賃目前為', '京都市巴士僅作雨天備案，普通均一運賃原估為'))
    prepare = soup.select_one('#view-prepare')
    for node in list(prepare.find_all(string=True)):
        value = str(node)
        value = value.replace('暫以 13:15 領行李並離開住宿', '12:30取行李，13:15離開住宿')
        value = value.replace('離園前查看返回住宿的轉乘與末班車；原則不搭計程車，疲累時提早離園。', '18:00離園，經西九條轉阪神難波線至大阪難波；19:25–19:45到Alcyon法善寺本店取蛋糕，再搭四橋線難波→花園町回住宿。出發前確認實際班次與店家取貨時間。')
        value = value.replace('2026/10/17 補充｜', '依每日行程同步至2026/10/19｜')
        if value != str(node):
            node.replace_with(value)
    # Defaults migrate only fields still matching old defaults, preserving custom edits/checks.
    updates = {
        'booking-2': {'title': '11/15 天満産直市場：確認18:15雙人訂位', 'note': '天神橋5-6-7的2樓；17:30到附近、18:00報到、18:15–19:30晚餐，尚未訂位。雙人含飲料及お通し上限¥6,000；官網お通し列每人¥333。官網週日22:30關門、Google顯示22:00，預約時核對11/15營業、最晚點餐、費用及取消規則。'},
        'booking-3': {'title': '11/16 一寸法師與Maruto：確認售完與備案', 'note': '15:50–16:20先到璃光清水本店還衣，16:20–16:30步行至一寸法師。16:30主選一寸法師，售完或候位過久則16:30–16:45到Maruto，16:45–17:30晚餐；兩家擇一共用雙人¥6,000。已換回便服，候位不再影響17:30歸還期限。'},
        'booking-6': {'note': '17:00–18:00在SAIDO彩道吃晚餐，18:00離園銜接19:25–19:45 Alcyon蛋糕取貨；確認當日營業、最後點餐及優先入座規則。尚未訂位，園內餐廳可能提早關門。'},
        'booking-10': {'title': '11/18 炭や わだち 別邸：確認18:30雙人訂位與店址', 'note': '時間軸18:00到店附近、18:15報到、18:30–20:30晚餐；建議訂位18:30，尚未訂位。2人單點上限¥10,000；確認本町橋7-18的別邸、週三營業、席費及取消規則。'},
    }
    updates['booking-1'] = {'title': '11/16 璃光清水本店09:30已預約：確認現場方案與舊預約取消', 'note': '女性1人＋男性1人，預訂ID 261116-24393；到店選方案與付款，訂金¥0，租借總價待確認，原岡本¥12,056不再計入。06:00出門、09:15報到；地址桝屋町351-16。15:50–16:20先還衣，官方最晚17:30原店歸還，再16:30一寸法師，售完改Maruto。確認原岡本訂單是否已取消、新店取消期限及現場加購費用。', 'due': '已預約／出發前複核'}
    dinner5 = next(m for m in facts['days'][4]['meals'] if m['label'].startswith('晚餐'))
    updates['booking-10']['title'] = f"11/18 炭や わだち 別邸：確認{dinner5['start']}雙人訂位與店址"
    updates['booking-10']['note'] = f"時間軸18:00到店附近、18:15報到、{dinner5['start']}–{dinner5['end']}晚餐；建議訂位{dinner5['start']}，尚未訂位。2人單點上限¥{dinner5['budget']:,}；確認本町橋7-18的別邸、週三營業、席費及取消規則。"
    previous = {}
    for task in checklist['tasks']:
        if task['id'] in updates:
            previous[task['id']] = {field: task[field] for field in updates[task['id']]}
            task.update(updates[task['id']])
    checklist['previousDefaults'] = previous
    checklist['revision'] = '2026-10-20-riko-kiyomizu-booking'
    # Keep aggregate prose, hero links and food envelope in sync as daily amounts change.
    replacements = {}
    for old, field in zip(old_totals, ('交通','餐飲','門票','total')):
        new = totals[field]
        replacements[f'¥{old:,}'] = f'¥{new:,}'
        replacements[f'NT${int(Decimal(old)*FX):,}'] = f'NT${int(Decimal(new)*FX):,}'
    pattern = re.compile('|'.join(re.escape(k) for k in replacements))
    for key in original_panels:
        for node in list(soup.select_one('#view-' + key).find_all(string=True)):
            if node.parent.name not in ('script', 'style'):
                value = pattern.sub(lambda m: replacements[m[0]], str(node))
                if value != str(node): node.replace_with(value)
    extra_total = facts['extrasTotal']
    known_total = facts['knownTotal']
    if extra_total:
        shortcut = soup.select_one('.overview-action[data-view-target="budget"]')
        shortcut.select_one('strong').string = f'¥{known_total:,}'
        shortcut.select_one('small').string = '交通・餐飲・門票・已預約和服 →'
        kpi = soup.select('#cost-overview .cost-kpi')[-1]
        kpi.select_one('.cost-label').string = '已知費用合計（含和服）'
        fill(kpi.select_one('.cost-main'), currency(known_total))
        kpi.select_one('.cost-sub').string = f'三類¥{totals["total"]:,}＋和服¥{extra_total:,}；機票、住宿、購物等另計'
        for row in soup.select('#view-budget table')[2].select('tbody tr'):
            if '和服租借' in text(row.select_one('[data-label="項目"]')):
                fill(row.select_one('[data-label="目前資料"] .phone-cell-value'), f'已預約雙人 {currency(extra_total)}')
                row.select_one('[data-label="計算方式"] .phone-cell-value').string = '清水店11/16 09:30；含DECO與髮型加購，付款狀態待確認'
        for n in soup.select('[data-sync-known-trip-cost]'):
            fill(n, f'交通／餐飲／門票三類小計 {currency(totals["total"])}；另加已預約和服 {currency(extra_total)}。已知項目合計 <strong>{currency(known_total)}</strong>，機票、住宿、購物、上網、保險等尚未包含。和服預約完成不代表已付款，避免再次加計同一筆租借費。')
    elif soup.select_one('#kyoto[data-extra-pending]'):
        shortcut = soup.select_one('.overview-action[data-view-target="budget"]')
        shortcut.select_one('strong').string = f'¥{known_total:,}＋'
        shortcut.select_one('small').string = '交通・餐飲・門票；和服費待確認 →'
        kpi = soup.select('#cost-overview .cost-kpi')[-1]
        kpi.select_one('.cost-label').string = '已知費用小計（不含和服）'
        fill(kpi.select_one('.cost-main'), currency(known_total))
        kpi.select_one('.cost-sub').string = '璃光到店選方案、現場付款；和服總價待確認，另計'
        for row in soup.select('#view-budget table')[2].select('tbody tr'):
            if '和服租借' in text(row.select_one('[data-label="項目"]')):
                row.select_one('[data-label="目前資料"] .phone-cell-value').string = '璃光已預約；總價待確認（訂金¥0）'
                row.select_one('[data-label="計算方式"] .phone-cell-value').string = '11/16 09:30清水本店；到店選方案與付款，原岡本費用已移除'
        for n in soup.select('[data-sync-known-trip-cost]'):
            fill(n, f'交通／餐飲／門票已知小計 <strong>{currency(known_total)}</strong>；璃光和服到店選方案、費用待確認。機票、住宿、購物、上網、保險等另計；訂金¥0不是免費租借。')
    # Replace only edited panels in the original document to preserve daily fragments verbatim.
    for key, old in original_panels.items():
        original = BeautifulSoup(document, 'html.parser').select_one('#view-' + key)
        # Locate exact source boundaries without reserializing the eight daily cards.
        # Existing source panels are already BeautifulSoup-normalized by the previous version.
        needle = str(original)
        replacement = str(soup.select_one('#view-' + key))
        if needle in document:
            document = document.replace(needle, replacement, 1)
        else:
            # Whitespace/attribute order may differ in hand-authored templates.
            # Parse only this panel's outer range using balanced div tags.
            start = re.search(r'<div\b[^>]*\bid="view-' + key + r'"[^>]*>', document).start()
            depth = 0
            for tag in re.finditer(r'</?div\b[^>]*>', document[start:]):
                depth += -1 if tag[0].startswith('</') else 1
                if depth == 0:
                    end = start + tag.end()
                    document = document[:start] + replacement + document[end:]
                    break
            else:
                raise ValueError('Unbalanced panel ' + key)
    return document, map_data, checklist, facts
