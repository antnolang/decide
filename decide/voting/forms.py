from django import forms
from django.conf import settings
from django.db import transaction

from base.models import Auth
from voting.models import Question, QuestionOption, Voting


class ImportSenateCandidates(forms.Form):

    candidate_file = forms.FileField()

    @transaction.atomic
    def save(self):
        candidate_file = self.cleaned_data.get('candidate_file', None)
        df = Voting.checkInputFile(candidate_file)
        auth = Auth.objects.get_or_create(url=settings.BASEURL, name='Sys')[0]

        for name, group in df.groupby(['Provincia']):
            count = 2

            quest = Question(desc='Elige un máximo de 2 personas para las '
                                  'listas al senado por ' + name)
            quest.save()

            voting_name = 'Votación Senado ' + name
            voting_desc = 'Listas al Senado por ' + name
            voting = Voting(name=voting_name, desc=voting_desc, question=quest)
            voting.save()
            voting.auths.add(auth)

            for row in group.iterrows():
                count += 1
                desc_option = row[1][4] + ': ' + row[1][1] + ', ' + row[1][0]
                gender = row[1][2]

                quest_option = QuestionOption(number=count, option=desc_option,
                                              gender=gender)
                quest_option.question = quest
                quest_option.save()
