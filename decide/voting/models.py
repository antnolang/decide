from django.db import models
from django.contrib.postgres.fields import JSONField
from base import mods
from base.models import Auth, Key

import pandas as pd


class Question(models.Model):
    desc = models.TextField()

    def __str__(self):
        return self.desc


class QuestionOption(models.Model):
    question = models.ForeignKey(Question, related_name='options',
     on_delete=models.CASCADE)
    number = models.PositiveIntegerField(blank=True, null=True)
    option = models.TextField()
    GENDER_CHOICES = (
        ('H', 'Hombre'),
        ('M', 'Mujer'),
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)

    def save(self):
        if not self.number:
            self.number = self.question.options.count() + 2
        return super().save()

    def __str__(self):
        return '{} ({})'.format(self.option, self.number)

    class Meta:
        unique_together = ('question', 'number')


class Voting(models.Model):
    name = models.CharField(max_length=200)
    desc = models.TextField(blank=True, null=True)
    question = models.ForeignKey(Question, related_name='voting',
     on_delete=models.CASCADE)

    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)

    pub_key = models.OneToOneField(Key, related_name='voting', blank=True,
     null=True, on_delete=models.SET_NULL)
    auths = models.ManyToManyField(Auth, related_name='votings')

    tally = JSONField(blank=True, null=True)
    postproc = JSONField(blank=True, null=True)

    def create_pubkey(self):
        if self.pub_key or not self.auths.count():
            return

        auth = self.auths.first()
        data = {
            "voting": self.id,
            "auths": [{"name": a.name, "url": a.url}
            for a in self.auths.all()],
        }
        key = mods.post('mixnet', baseurl=auth.url, json=data)
        pk = Key(p=key["p"], g=key["g"], y=key["y"])
        pk.save()
        self.pub_key = pk
        self.save()

    def get_votes(self, token=''):
        # gettings votes from store
        votes = mods.get('store', params={'voting_id': self.id},
        HTTP_AUTHORIZATION='Token ' + token)

        # anon votes
        return [[i['a'], i['b']] for i in votes]

    def tally_votes(self, token=''):
        '''
        The tally is a shuffle and then a decrypt
        '''

        votes = self.get_votes(token)

        auth = self.auths.first()
        shuffle_url = "/shuffle/{}/".format(self.id)
        decrypt_url = "/decrypt/{}/".format(self.id)
        auths = [{"name": a.name, "url": a.url} for a in self.auths.all()]

        # first, we do the shuffle
        data = {"msgs": votes}
        response = mods.post('mixnet', entry_point=shuffle_url,
         baseurl=auth.url, json=data, response=True)
        if response.status_code != 200:
            # TODO: manage error
            pass

        # then, we can decrypt that
        data = {"msgs": response.json()}
        response = mods.post('mixnet', entry_point=decrypt_url,
         baseurl=auth.url, json=data, response=True)

        if response.status_code != 200:
            # TODO: manage error
            pass

        self.tally = response.json()
        self.save()

        self.do_postproc()

    def do_postproc(self):
        tally = self.tally
        options = self.question.options.all()

        opts = []
        for opt in options:
            if isinstance(tally, list):
                votes = tally.count(opt.number)
            else:
                votes = 0
            opts.append({
                'option': opt.option,
                'number': opt.number,
                'votes': votes
            })

        data = {'type': 'IDENTITY', 'options': opts}
        postp = mods.post('postproc', json=data)

        self.postproc = postp
        self.save()

    def __str__(self):
        return self.name

    def checkInputFile(filePath):
        file = pd.read_excel(filePath,sheet_name = 'Hoja1')
        df = pd.DataFrame(file)
        columns_names = ['Nombre', 'Apellidos', 'Sexo', 'Provincia',
                         'Partido Político', 'Proceso Primarias']

        # Comprobación número columnas
        if len(file.columns) != 6:
            raise AssertionError(
        'El número de columnas del archivo no concuerda con el esperado')
        # Comprobación nombres de columnas
        if (columns_names != file.columns).all():
            raise AssertionError(
        'Los nombres de las columnas deben ser ' + str(columns_names))
        # Comprobación provincias
        if len(df["Provincia"].unique()) != 52:
            raise AssertionError('Faltan provincias con candidatos')
        for row in df.iterrows():
            # Comprobación proceso primarias
            if str(row[1][5]) != "Sí":
                raise AssertionError(
            'El candidato con nombre ' + str(row[1][0]) + ' ' 
            + str(row[1][1]) + ' perteneciente a la provincia ' + str(
                row[1][3]) + ' del partido ' + str(row[1][4]) +
            ' no ha pasado por un proceso de primarias.')
        # Comprobación 6 candidatos/provincia/partido político
        df2 = df.groupby(['Provincia', 'Partido Político'])
        for key, item in df2:
            if len(item) != 6 :
                raise AssertionError('Las siguientes candidaturas no cumplen '
                                     'con los 6 candidatos obligatorios:\n' +
                                     str(df2.get_group(key)))
        # Comprobación relación 1/2
        df3 = df.groupby(['Provincia', 'Partido Político', 'Sexo'])
        for key, item in df3:
            if len(df3.get_group(key)) != 3:
                raise AssertionError(
            'Las siguientes candidaturas no cumplen con la relación 1/2' +
             'entre hombres y mujeres:\n' + str(df3.get_group(key)))

        return df
