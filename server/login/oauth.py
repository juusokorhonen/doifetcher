# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)

from flask import current_app, url_for, redirect, request
from rauth import OAuth1Service, OAuth2Service
import json, requests 

class OAuthSignIn(object):
    """
    This is an abstraction layer for RAuth authentication. Sample code adapted
    with gratitude from tutorials by Miguel Grinberg.
    """
    providers = None

    def __init__(self, provider_name):
        self.provider_name = provider_name
        credentials = current_app.config['OAUTH_CREDENTIALS'][provider_name]
        self.consumer_id = credentials['id']
        self.consumer_secret = credentials['secret']

    def authorize(self):
        pass

    def callback(self):
        pass

    def get_callback_url(self):
        if current_app.debug:
            print("get_callback_url() called. Provider: {}".format(self.provider_name))
        return url_for('login.oauth_callback', provider=self.provider_name, _external=True)

    @classmethod
    def get_provider(self, provider_name):
        if self.providers is None:
            self.providers = {}
            for provider_class in self.__subclasses__():
                provider = provider_class()
                self.providers[provider.provider_name] = provider
        return self.providers[provider_name]

class GoogleSignIn(OAuthSignIn):
    _name = 'google'
    def __init__(self):
        super(GoogleSignIn, self).__init__('google')
        # DEFAULT URLs FROM CONFIG:
        authorize_url = current_app.config['OAUTH_CREDENTIALS'][self._name]['authorize_url']
        base_url = current_app.config['OAUTH_CREDENTIALS'][self._name]['base_url']
        access_token_url = current_app.config['OAUTH_CREDENTIALS'][self._name]['access_token_url']

        if (current_app.config['OAUTH_CREDENTIALS'][self._name]['configuration_url'] is not None) and not current_app.config['OAUTH_CREDENTIALS'][self._name]['always_use_defaults']:
            # Try to fetch correct urls from Google 
            try:
                response = requests.get(current_app.config['OAUTH_CREDENTIALS'][self._name]['configuration_url'])
                if response.status_code != 200:
                    raise Exception("Response {}".format(response.status_code))
                google_params = response.json()
                authorize_url = google_params.get('authorization_endpoint')
                base_url = google_params.get('userinfo_endpoint')
                access_token_url = google_params.get('token_endpoint')
            except Exception as e:
                # Failed to fetch google urls so fall back to defaults (last checked 16.4.2015)
                if current_app.debug:
                    print("Failed to fetch OAUTH urls from Google. Falling back to defaults.")
                    print(str(e))

        # Create an OAuth2Service instance
        self.service = OAuth2Service(
                name = self._name,
                client_id = self.consumer_id,
                client_secret = self.consumer_secret,
                authorize_url = authorize_url,
                base_url = base_url,
                access_token_url = access_token_url
                )

    def authorize(self):
        return redirect(self.service.get_authorize_url(
            scope = 'openid email profile',
            response_type = 'code',
            redirect_uri = self.get_callback_url())
            )

    def callback(self):
        if 'code' not in request.args:
            return {'authenticated': False} 

        oauth_session = self.service.get_auth_session(
                data = {'code': request.args['code'],
                    'grant_type': 'authorization_code',
                    'redirect_uri': self.get_callback_url()
                    },
                decoder = json.loads
                )

        # DEBUG INFORMATION:
        if current_app.debug:
            print("Callback information from Google : ")
            for k,v in oauth_session.get('').json().items():
                print("{} : {}".format(k, v))

        authuser = oauth_session.get('').json()
        oauth_id = str(authuser.get('sub'))
        email = authuser.get('email')
        nickname = email.split('@')[0]
        name = authuser.get('name')
        verified = (authuser.get('email_verified') or authuser.get('email_verified') == 'True')

        return {
                'authenticated': True,
                'verified': verified,
                'provider': self._name,
                'id': oauth_id,
                'nickname': nickname, 
                'email': email,
                'name': name
            }

