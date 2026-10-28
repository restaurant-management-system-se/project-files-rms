from django.test import TestCase
from .models import MenuItem
class MenuBrowseTests(TestCase):
    def test_grouping_only_available_fresh_and_empty(self):
        r=self.client.get('/api/menu'); self.assertEqual(r.status_code,200); self.assertEqual(len(r.json()['categories']),4)
        item=MenuItem.objects.create(name='<script>alert(1)</script>',description='Test',category='Starters',price='2.50')
        MenuItem.objects.create(name='Sold out',category='Desserts',price='3',available=False)
        data=self.client.get('/api/menu').json(); self.assertEqual(data['categories'][0]['items'][0]['id'],item.pk); self.assertEqual(data['categories'][2]['items'],[])
        item.available=False; item.save(); self.assertEqual(self.client.get('/api/menu').json()['categories'][0]['items'],[])
        self.assertIn('no-store',self.client.get('/api/menu')['Cache-Control'])
    def test_public_read_cannot_write_and_responsive_template(self):
        self.assertEqual(self.client.post('/api/menu',{}).status_code,405)
        r=self.client.get('/menu/'); self.assertContains(r,'width=device-width'); self.assertContains(r,'textContent'); self.assertNotContains(r,'innerHTML')
