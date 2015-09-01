from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from rest_framework.test import APILiveServerTestCase

from grd.models import Agent


class BaseTestCase(StaticLiveServerTestCase, APILiveServerTestCase):
    def setUp(self):
        self.username = 'ereuse'
        self.password = 'ereuse'
        
        User = get_user_model()
        user = User.objects.create_superuser(self.username,
                                             'test@localhost',
                                             self.password)
        
        self.agent = Agent.objects.create(name='XSR', user=user)
        
        # authenticate the user
        token = self.get_user_token(self.username, self.password)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
    
    def get_user_token(self, username, password):
        response = self.client.post(
            '/api-token-auth/',
            data={'username': username, 'password': password},
        )
        self.assertEqual(200, response.status_code,
                         "Unable to log in with provided credentials.")
        
        return response.data['token']
    
    def count_listed_objects(self, url):
        response = self.client.get(url)
        return len(response.data)
    
    def get_latest_event(self, events):
        assert len(events) > 0
        last_event = events[0]
        for event in events:
            if event['grdTimestamp'] > last_event['grdTimestamp']:
                last_event = event
        return last_event
    
    def assertEventType(self, event_url, type):
        response = self.client.get(event_url)
        self.assertEqual(200, response.status_code, response.content)
        
        event = response.data
        self.assertEqual(type, event['type'])
        
        response = self.client.get(event['agent'])
        self.assertEqual(200, response.status_code, response.content)
        agent = response.data
        self.assertEqual(self.agent.name, agent['name'])
