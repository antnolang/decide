from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from django.test.client import RequestFactory
from django.urls import reverse
from django.contrib.auth.models import AnonymousUser

# from django.contrib.auth.models import User
from .models import CustomUser
from rest_framework.authtoken.models import Token

from base import mods


class AuthTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()
        mods.mock_query(self.client)
        u = CustomUser(username='voter1')
        u.set_password('123')
        u.save()

        u2 = CustomUser(username='admin')
        u2.set_password('admin')
        u2.is_superuser = True
        u2.save()

    def tearDown(self):
        self.client = None

    def test_login(self):
        data = {'username': 'voter1', 'password': '123'}
        response = self.client.post(
            '/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)

        token = response.json()
        self.assertTrue(token.get('token'))

    def test_login_fail(self):
        data = {'username': 'voter1', 'password': '321'}
        response = self.client.post(
            '/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 400)

    def test_getuser(self):
        data = {'username': 'voter1', 'password': '123'}
        response = self.client.post(
            '/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        token = response.json()

        response = self.client.post(
            '/authentication/getuser/', token, format='json')
        self.assertEqual(response.status_code, 200)

        user = response.json()
        self.assertEqual(user['id'], 1)
        self.assertEqual(user['username'], 'voter1')

    def test_getuser_invented_token(self):
        token = {'token': 'invented'}
        response = self.client.post(
            '/authentication/getuser/', token, format='json')
        self.assertEqual(response.status_code, 404)

    def test_getuser_invalid_token(self):
        data = {'username': 'voter1', 'password': '123'}
        response = self.client.post(
            '/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Token.objects.filter(
            user__username='voter1').count(), 1)

        token = response.json()
        self.assertTrue(token.get('token'))

        response = self.client.post(
            '/authentication/logout/', token, format='json')
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            '/authentication/getuser/', token, format='json')
        self.assertEqual(response.status_code, 404)

    def test_logout(self):
        data = {'username': 'voter1', 'password': '123'}
        response = self.client.post(
            '/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Token.objects.filter(
            user__username='voter1').count(), 1)

        token = response.json()
        self.assertTrue(token.get('token'))

        response = self.client.post(
            '/authentication/logout/', token, format='json')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Token.objects.filter(
            user__username='voter1').count(), 0)

    def test_register_bad_permissions(self):
        data = {'username': 'voter1', 'password': '123'}
        response = self.client.post(
            '/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        token = response.json()

        token.update({'username': 'user1'})
        response = self.client.post(
            '/authentication/register/', token, format='json')
        self.assertEqual(response.status_code, 401)

    def test_register_bad_request(self):
        data = {'username': 'admin', 'password': 'admin'}
        response = self.client.post(
            '/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        token = response.json()

        token.update({'username': 'user1'})
        response = self.client.post(
            '/authentication/register/', token, format='json')
        self.assertEqual(response.status_code, 400)

    def test_register_user_already_exist(self):
        data = {'username': 'admin', 'password': 'admin'}
        response = self.client.post(
            '/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        token = response.json()

        token.update(data)
        response = self.client.post(
            '/authentication/register/', token, format='json')
        self.assertEqual(response.status_code, 400)

    def test_register(self):
        data = {'username': 'admin', 'password': 'admin'}
        response = self.client.post(
            '/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        token = response.json()

        token.update({'username': 'user1', 'password': 'pwd1'})
        response = self.client.post(
            '/authentication/register/', token, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            sorted(list(response.json().keys())),
            ['token', 'user_pk']
        )

    def test_signup(self):

        request = RequestFactory().post(reverse('account_signup'),
                                        {'username': 'voter10',
                                         'email': 'email@gmail.com',
                                         'password1': '1234ABCD.*',
                                         'password2': '1234ABCD.*',
                                         'email': 'email@gmail.com',
                                         'email1': 'email.github@gmail.com',
                                         'email2': 'email.facebook@gmail.com'})

        #
        # response = self.client.post('/authentication/accounts/signup/',
        #                             data, format='json')
        # self.assertEqual(response.status_code, 200)
        from django.contrib.messages.middleware import MessageMiddleware
        from django.contrib.sessions.middleware import SessionMiddleware
        SessionMiddleware().process_request(request)
        MessageMiddleware().process_request(request)
        request.user = AnonymousUser()
        from .views import signup
        signup(request)

        data = {'username': 'voter10', 'password': '1234ABCD.*'}
        response = self.client.post('/authentication/login/', data,
                                    format='json')
        self.assertEqual(response.status_code, 200)
        token = response.json()

        response = self.client.post('/authentication/getuser/', token,
                                    format='json')
        self.assertEqual(response.status_code, 200)

        user = response.json()
        self.assertEqual(user['username'], 'voter10')

    def test_signup_user_already_exist(self):
        # create user
        request = RequestFactory().post(reverse('account_signup'),
                                        {'username': 'voter10',
                                         'email': 'email@gmail.com',
                                         'password1': '1234ABCD.*',
                                         'password2': '1234ABCD.*',
                                         'email': 'email@gmail.com',
                                         'email1': 'email.github@gmail.com',
                                         'email2': 'email.facebook@gmail.com'})

        from django.contrib.messages.middleware import MessageMiddleware
        from django.contrib.sessions.middleware import SessionMiddleware
        SessionMiddleware().process_request(request)
        MessageMiddleware().process_request(request)
        request.user = AnonymousUser()
        from .views import signup
        signup(request)

        # create the same user again
        request = RequestFactory().post(reverse('account_signup'),
                                        {'username': 'voter10',
                                         'email': 'email@gmail.com',
                                         'password1': '1234ABCD.*',
                                         'password2': '1234ABCD.*',
                                         'email': 'email@gmail.com',
                                         'email1': 'email.github@gmail.com',
                                         'email2': 'email.facebook@gmail.com'})

        from django.contrib.messages.middleware import MessageMiddleware
        from django.contrib.sessions.middleware import SessionMiddleware
        SessionMiddleware().process_request(request)
        MessageMiddleware().process_request(request)
        request.user = AnonymousUser()
        from .views import signup
        duplicate = False
        try:
            signup(request)
        except Exception as exception:
            print(exception)
            duplicate = True

        print(duplicate)





