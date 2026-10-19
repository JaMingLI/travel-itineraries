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
        self.assertEqual(len(self.page.select('.agenda-notes')),110)
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
