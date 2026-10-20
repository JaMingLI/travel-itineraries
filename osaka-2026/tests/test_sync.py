import sys
import json
import unittest
from pathlib import Path
from bs4 import BeautifulSoup, Comment

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from build import generate
from sync import extract_facts

class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preserved = generate(preserve_content=True)
        cls.files = generate()
        cls.page = BeautifulSoup(cls.files['index.html'], 'html.parser')
        cls.facts = json.loads(cls.files['assets/data/itinerary.json'])

    def test_extraction_preserves_dom_and_cascade(self):
        baseline = ROOT.parents[1] / 'work/before-full-refactor.html'
        if not baseline.exists(): self.skipTest('Original extraction audit fixture is local only')
        old = BeautifulSoup(baseline.read_text(), 'html.parser')
        new = BeautifulSoup(self.preserved['index.html'], 'html.parser')
        def rules(soup):
            return [str(n.string) if n.name == 'style' else self.preserved[n['href'].removeprefix('./')] if 'assets/css/' in n['href'] else n['href'] for n in soup.select('style,link[rel=stylesheet]')]
        self.assertEqual(rules(old), rules(new))
        # After intentional itinerary edits, extraction must preserve current source DOM.
        from build import expand_includes, SOURCE
        old = BeautifulSoup(expand_includes((SOURCE / 'document.html').read_text()), 'html.parser')
        for soup in (old,new):
            for n in soup.select('script,style,link[rel=stylesheet]'): n.decompose()
            for n in soup.find_all(string=lambda n:isinstance(n,Comment)): n.extract()
        self.assertEqual(str(old), str(new))

    def test_daily_fragments_untouched(self):
        for day in range(1,9):
            original = (ROOT / f'src/days/day-{day:02}.html').read_text().rstrip('\n')
            self.assertIn(original, self.files['index.html'])

    def test_budget_and_dinners(self):
        self.assertEqual(self.facts['totals'], {'交通':16500,'餐飲':98000,'門票':28800,'total':143300})
        for day,row in zip(self.facts['days'], self.page.select('#summary tbody tr')):
            for dinner in [m for m in day['meals'] if m['label'].startswith('晚餐')]:
                self.assertIn(dinner['start']+'–'+dinner['end'], row.text)
        self.assertNotIn('慢早餐', self.page.select_one('#view-overview').text)
        self.assertEqual(len(self.page.select('.agenda-notes')),sum(len(d['steps']) for d in self.facts['days']))
        self.assertFalse(self.page.select('.agenda-notes[open]'))

    def test_map_and_checklist(self):
        from sync import synchronize
        from build import json_source
        _,data,checklist,_ = synchronize(self.preserved['index.html'],json_source('map.json'),json_source('checklist.json'))
        self.assertTrue(any('一笑' in p['name'] for p in data['tripDays']['6']['points']))
        for day in self.facts['days']:
            self.assertEqual(data['routes'][str(day['day'])], day['routes'][0]['url'])
        task = next(t for t in checklist['tasks'] if t['id']=='booking-10')
        self.assertIn('18:30–20:30',task['note'])
        self.assertNotIn('須以實際訂位統一',task['note'])
        self.assertEqual(len(checklist['tasks']),61)

    def test_build_reproducible_and_links_present(self):
        self.assertEqual(self.files,generate())
        for node in self.page.select('script[src],link[rel=stylesheet]'):
            name=node.get('src',node.get('href')).removeprefix('./')
            self.assertTrue(name in self.files or (ROOT/name).exists(),name)
        self.assertLess(self.files['index.html'].index('assets/js/checklist-state.js'),self.files['index.html'].index('assets/js/checklist.js'))

    def test_day2_user_selected_restaurant(self):
        day = self.page.select_one('#day-card-2')
        self.assertNotIn('春駒', day.text)
        self.assertNotIn('11:00起營業', day.text)
        self.assertNotIn('週二及每月另兩個週三休', day.text)
        self.assertIn('天満産直市場', day.text)
        dinner = next(m for m in self.facts['days'][1]['meals'] if m['label'].startswith('晚餐'))
        self.assertEqual((dinner['start'], dinner['end'], dinner['budget']), ('18:15','19:30',6000))
        for n in self.page.select('#view-overview,#view-map'):
            self.assertNotIn('春駒', n.text)
        self.assertIn('11:30–22:30', day.text)
        self.assertIn('22:00關門', day.text)

    def test_day3_primary_and_sold_out_alternative(self):
        import re
        day = self.facts['days'][2]
        dinner = next(m for m in day['meals'] if m['label'].startswith('晚餐'))
        self.assertEqual((dinner['start'],dinner['end'],dinner['budget']),('16:30','17:10',6000))
        self.assertIn('一寸法師',dinner['label'])
        rendered = self.page.select_one('#day-card-3')
        self.assertNotIn('豬一',rendered.text)
        self.assertNotIn('22:15',rendered.text)
        primary_return = next(n for n in day['steps'] if n['title'].startswith('還衣、'))
        self.assertEqual((primary_return['start'],primary_return['end']),('17:20','17:50'))
        alternative = day['alternatives'][0]['steps']
        self.assertEqual((alternative[1]['start'],alternative[1]['end']),('16:45','17:15'))
        self.assertEqual((alternative[3]['start'],alternative[3]['end']),('17:25','18:10'))
        minutes=lambda value:int(value[:2])*60+int(value[3:])
        for a,b in zip(day['steps'],day['steps'][1:]): self.assertEqual(a['end'],b['start'])
        for a,b in zip(alternative,alternative[1:]): self.assertEqual(a['end'],b['start'])
        for n in alternative:
            self.assertGreaterEqual(minutes(n['end'])-minutes(n['start']),n['baseMinutes']*1.2)
        for n in rendered.select('.agenda-item'):
            m=re.search(r'基準\s*(\d+)\s*分',n.select_one('.agenda-math').text)
            if m:self.assertGreaterEqual(minutes(n.select_one('.time-end').text)-minutes(n.select_one('.time-start').text),int(m[1])*1.2)
        self.assertEqual(len([m for m in day['meals'] if m['label'].startswith('晚餐')]),1)
        self.assertFalse(rendered.select('[data-alternative-plan][open]'))

    def test_confirmed_kimono_booking_and_cost(self):
        booking = self.page.select_one('#kyoto')
        self.assertEqual(booking['data-booking-status'], 'confirmed')
        self.assertEqual(booking['data-booking-time'], '09:30')
        self.assertEqual(booking['data-extra-jpy'], '12056')
        self.assertIn('清水店', booking.text)
        self.assertIn('付款狀態尚未確認', booking.text)
        self.assertIn('237-1-1', booking.text)
        self.assertEqual(self.facts['extrasTotal'], 12056)
        self.assertEqual(self.facts['knownTotal'], 155356)
        self.assertIn('155,356', self.page.select_one('#view-budget').text)
        self.assertEqual(sum(x['amount'] for d in self.facts['days'] for x in d['extras']),12056)
        self.assertIn('06:00', self.page.select_one('#day-card-3').text)

    def test_day5_wadachi_dinner(self):
        day = self.page.select_one('#day-card-5')
        self.assertNotIn('Tottotto', day.text)
        self.assertNotIn('お初天神', day.text)
        self.assertIn('本町橋7-18', day.text)
        self.assertIn('中央線直達堺筋本町', day.text)
        self.assertIn('堺筋線直達天下茶屋', day.text)
        dinner = next(m for m in self.facts['days'][4]['meals'] if m['label'].startswith('晚餐'))
        self.assertEqual((dinner['start'],dinner['end'],dinner['budget']),('18:30','20:30',10000))
        self.assertIn('わだち',dinner['label'])

    def test_day_edit_propagates(self):
        from sync import synchronize
        from build import json_source
        source=self.preserved['index.html']
        source=source.replace('梅田購物，A5 和牛收尾','TEST梅田購物')
        rendered,data,_,facts=synchronize(source,json_source('map.json'),json_source('checklist.json'))
        parsed=BeautifulSoup(rendered,'html.parser')
        self.assertEqual(data['tripDays']['6']['title'],'TEST梅田購物')
        self.assertEqual(parsed.select_one('.overview-day[data-trip-day="6"] strong').text,'TEST梅田購物')
        self.assertIn('TEST梅田購物',parsed.select('#summary tbody tr')[5].text)

if __name__=='__main__': unittest.main()
