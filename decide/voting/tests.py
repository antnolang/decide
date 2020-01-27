import random
import itertools
from django.utils import timezone
from django.conf import settings

from django.test import TestCase

from base import mods
from base.tests import BaseTestCase
from census.models import Census
from mixnet.mixcrypt import ElGamal
from mixnet.mixcrypt import MixCrypt
from mixnet.models import Auth
from voting.models import Voting, Question, QuestionOption
from voting import views

from django.contrib.auth import get_user_model
User = get_user_model()

import os


class VotingTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def encrypt_msg(self, msg, v, bits=settings.KEYBITS):
        pk = v.pub_key
        p, g, y = (pk.p, pk.g, pk.y)
        k = MixCrypt(bits=bits)
        k.k = ElGamal.construct((p, g, y))
        return k.encrypt(msg)

    def create_voting(self):
        q = Question(desc='test question')
        q.save()
        for i in range(5):
            opt = QuestionOption(question=q, option='option {}'.format(i+1))
            opt.save()
        v = Voting(name='test voting', question=q)
        v.save()

        a, _ = Auth.objects.get_or_create(url=settings.BASEURL,
                                          defaults={'me': True,
                                           'name': 'test auth'})
        a.save()
        v.auths.add(a)

        return v

    def create_voters(self, v):
        for i in range(100):
            u, _ = User.objects.get_or_create(username='testvoter{}'.format(i))
            u.is_active = True
            u.save()
            c = Census(voter_id=u.id, voting_id=v.id)
            c.save()

    def get_or_create_user(self, pk):
        user, _ = User.objects.get_or_create(pk=pk)
        user.username = 'user{}'.format(pk)
        user.set_password('qwerty')
        user.save()
        return user

    def store_votes(self, v):
        voters = list(Census.objects.filter(voting_id=v.id))
        voter = voters.pop()

        clear = {}
        for opt in v.question.options.all():
            clear[opt.number] = 0
            for i in range(random.randint(0, 5)):
                a, b = self.encrypt_msg(opt.number, v)
                data = {
                    'voting': v.id,
                    'voter': voter.voter_id,
                    'vote': {'a': a, 'b': b},
                }
                clear[opt.number] += 1
                user = self.get_or_create_user(voter.voter_id)
                self.login(user=user.username)
                voter = voters.pop()
                mods.post('store', json=data)
        return clear

    def test_complete_voting(self):
        v = self.create_voting()
        self.create_voters(v)

        v.create_pubkey()
        v.start_date = timezone.now()
        v.save()

        clear = self.store_votes(v)

        self.login()  # set token
        v.tally_votes(self.token)

        tally = v.tally
        tally.sort()
        tally = {k: len(list(x)) for k, x in itertools.groupby(tally)}

        for q in v.question.options.all():
            self.assertEqual(tally.get(q.number, 0), clear.get(q.number, 0))

        for q in v.postproc:
            self.assertEqual(tally.get(q["number"], 0), q["votes"])

    def test_create_voting_from_api(self):
        data = {'name': 'Example'}
        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 401)

        # login with user no admin
        self.login(user='noadmin')
        response = mods.post('voting', params=data, response=True)
        self.assertEqual(response.status_code, 403)

        # login with user admin
        self.login()
        response = mods.post('voting', params=data, response=True)
        self.assertEqual(response.status_code, 400)

        data = {
            'name': 'Example',
            'desc': 'Description example',
            'question': 'I want a ',
            'question_opt': ['cat', 'dog', 'horse']
        }

        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 201)

    def test_delete_voting(self):
        q = Question(desc='test question')
        q.save()
        for i in range(5):
            opt = QuestionOption(question=q, option='option {}'.format(i + 1))
            opt.save()
        v = Voting(name='test voting', question=q)
        v.save()

        a, _ = Auth.objects.get_or_create(url=settings.BASEURL,
                                          defaults={'me': True,
                                                    'name': 'test auth'})
        a.save()
        v.auths.add(a)

        v.delete()

    def test_update_voting(self):
        voting = self.create_voting()

        data = {'action': 'start'}
        # response = self.client.post('/voting/{}/'.format(
        # voting.pk), data, format='json')
        # self.assertEqual(response.status_code, 401)

        # login with user no admin
        self.login(user='noadmin')
        response = self.client.put('/voting/{}/'.format(voting.pk),
         data, format='json')
        self.assertEqual(response.status_code, 403)

        # login with user admin
        self.login()
        data = {'action': 'bad'}
        response = self.client.put('/voting/{}/'.format(voting.pk),
         data, format='json')
        self.assertEqual(response.status_code, 400)

        # STATUS VOTING: not started
        for action in ['stop', 'tally']:
            data = {'action': action}
            response = self.client.put('/voting/{}/'.format(voting.pk),
             data, format='json')
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json(), 'Voting is not started')

        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk),
         data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Voting started')

        # STATUS VOTING: started
        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk),
         data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already started')

        data = {'action': 'tally'}
        response = self.client.put('/voting/{}/'.format(voting.pk),
         data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting is not stopped')

        data = {'action': 'stop'}
        response = self.client.put('/voting/{}/'.format(voting.pk),
         data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Voting stopped')

        # STATUS VOTING: stopped
        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk),
         data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already started')

        data = {'action': 'stop'}
        response = self.client.put('/voting/{}/'.format(voting.pk),
         data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already stopped')

        data = {'action': 'tally'}
        response = self.client.put('/voting/{}/'.format(voting.pk),
         data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Voting tallied')

        # STATUS VOTING: tallied
        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk),
         data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already started')

        data = {'action': 'stop'}
        response = self.client.put('/voting/{}/'.format(voting.pk),
         data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already stopped')

        data = {'action': 'tally'}
        response = self.client.put('/voting/{}/'.format(voting.pk),
         data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already tallied')

    def test_check_inputFile(self):
        THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
        filePath = THIS_FOLDER + '/docs/CandidatesFiles/Candidatos_Senado.xlsx'
        # my_file = os.path.join(THIS_FOLDER + '/docs/CandidatesFiles/',
        #  'Candidatos_Senado.xlsx')
        
        # Test positivo
        Voting.checkInputFile(filePath)

        # Test negativo. Un candidato no ha pasado por el proceso de primarias
        filePath = THIS_FOLDER + '/docs/CandidatesFiles/Candidatos_Senado2' \
                                 '.xlsx'
        try:
            Voting.checkInputFile(filePath)
        except:
            print('Test negativo de proceso de primarias correcto')
        
        # Test negativo. Faltan provincias con candidatos
        filePath = THIS_FOLDER + '/docs/CandidatesFiles/Candidatos_Senado3' \
                                 '.xlsx'
        try:
            Voting.checkInputFile(filePath)
        except:
            print('Test negativo de provincias correcto')
        
        # Test negativo. No hay 6 candidatos/provincia/partido político 
        # ni relación 1/2 entre hombres y mujeres
        filePath = THIS_FOLDER + '/docs/CandidatesFiles/Candidatos_Senado4' \
                                 '.xlsx'
        try:
            Voting.checkInputFile(filePath)
        except:
            print('Test negativo de 6 candidatos/provincia/partido político' +
            'yrelación 1/2 correcto')


class VotingViewTestCase(TestCase):

    def setUp(self):
        q1 = Question(desc='Elige un máximo de 2 personas para las listas del '
                           'senado por Ávila')
        q1.save()
        opt11 = QuestionOption(question=q1, option='PSOE: García Mata, Jaime',
                               gender='H')
        opt11.save()
        opt12 = QuestionOption(question=q1, option='PP: López Ugarte, Mohamed',
                               gender='H')
        opt12.save()
        opt13 = QuestionOption(question=q1, option='PP: Samaniego Nolé, María',
                               gender='M')
        opt13.save()
        opt14 = QuestionOption(question=q1, option='PP: Llanos  Plana, Josefa',
                               gender='M')
        opt14.save()
        opt15 = QuestionOption(question=q1, option='PP: Encinas Cuervo, Gonzo',
                               gender='H')
        opt15.save()

        q2 = Question(desc='Elige un máximo de 2 personas para las listas del '
                           'senado por Sevilla')
        q2.save()
        opt21 = QuestionOption(question=q2, option='PSOE: García Mata, Mohamed',
                               gender='H')
        opt21.save()
        opt22 = QuestionOption(question=q2, option='PP: López Ugarte, Mohamed',
                               gender='H')
        opt22.save()
        opt23 = QuestionOption(question=q2, option='PP: Anguita Ruiz, María',
                               gender='M')
        opt23.save()
        opt24 = QuestionOption(question=q2, option='PP: Girón Plana, Jaime',
                               gender='H')
        opt24.save()
        opt25 = QuestionOption(question=q2, option='PP: Encinas Cuevas, Gonzo',
                               gender='H')
        opt25.save()

        v1 = Voting(name='Votación Senado Ávila', question=q1,
                    desc='Listas al Senado por Ávila')
        v1.save()

        v2 = Voting(name='Votación Senado Sevilla', question=q2,
                    desc='Listas al Senado por Sevilla')
        v2.save()

        a, _ = Auth.objects.get_or_create(url=settings.BASEURL,
                                          defaults={'me': True,
                                                    'name': 'test auth'})
        a.save()
        v1.auths.add(a)
        v2.auths.add(a)
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_get_candidates(self):
        data = views.get_candidates()
        self.assertEqual(type(data), list().__class__)
        self.assertEqual(len(data), 11)
        for d in data:
            self.assertEqual(type(d), list().__class__)
            self.assertEqual(len(d), 6)
