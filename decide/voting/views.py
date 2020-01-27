import django_filters.rest_framework
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from io import BytesIO as IO

import pandas as pd
import re

from .models import Question, QuestionOption, Voting
from .serializers import SimpleVotingSerializer, VotingSerializer
from base.perms import UserIsStaff
from base.models import Auth


def get_candidates():
    votings = Voting.objects.all()
    data = [['Nombre', 'Apellidos', 'Sexo', 'Provincia', 'Partido Político',
             'Proceso Primarias']]

    for voting in votings:
        quest = voting.question
        question_options = QuestionOption.objects.filter(question=quest)
        for quest_op in question_options:
            regex = re.compile(r'(.+)\: (.+), (.+)').search(quest_op.option)
            first_name = regex.group(3).strip()
            last_name = regex.group(2).strip()
            gender = quest_op.gender
            province = re.compile(r'Votación Senado (.+)').search(
                voting.name).group(1)
            political_party = regex.group(1).strip()
            primary = 'Sí'
            row = [first_name, last_name, gender, province, political_party,
                   primary]
            data.append(row)

    return data


def export_candidates(request):
    output = get_candidates()
    df_output = pd.DataFrame(output)
    excel_file = IO()

    xlwriter = pd.ExcelWriter(excel_file, engine='xlsxwriter')
    df_output.to_excel(excel_writer=xlwriter, sheet_name='Hoja1',
                       index=False, header=False)
    xlwriter.save()
    xlwriter.close()

    excel_file.seek(0)

    response = HttpResponse(excel_file.read(),
                            content_type='application/vnd.openxmlformats-'
                                         'officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; ' \
                                      'filename=Candidatos_Senado.xlsx'

    return response


class VotingView(generics.ListCreateAPIView):
    queryset = Voting.objects.all()
    serializer_class = VotingSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filter_fields = ('id', )

    def get(self, request, *args, **kwargs):
        version = request.version
        if version not in settings.ALLOWED_VERSIONS:
            version = settings.DEFAULT_VERSION
        if version == 'v2':
            self.serializer_class = SimpleVotingSerializer

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.permission_classes = (UserIsStaff,)
        self.check_permissions(request)
        for data in ['name', 'desc', 'question', 'question_opt']:
            if not data in request.data:
                return Response({}, status=status.HTTP_400_BAD_REQUEST)

        question = Question(desc=request.data.get('question'))
        question.save()
        for idx, q_opt in enumerate(request.data.get('question_opt')):
            opt = QuestionOption(question=question, option=q_opt,
             number=idx+1)
            opt.save()
        voting = Voting(name=request.data.get('name'),
         desc=request.data.get('desc'), question=question)
        voting.save()

        auth, _ = Auth.objects.get_or_create(url=settings.BASEURL,
                                          defaults={'me': True,
                                           'name': 'test auth'})
        auth.save()
        voting.auths.add(auth)
        return Response({}, status=status.HTTP_201_CREATED)


class VotingUpdate(generics.RetrieveUpdateDestroyAPIView):
    queryset = Voting.objects.all()
    serializer_class = VotingSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    permission_classes = (UserIsStaff,)

    def put(self, request, voting_id, *args, **kwars):
        action = request.data.get('action')
        if not action:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

        voting = get_object_or_404(Voting, pk=voting_id)
        msg = ''
        st = status.HTTP_200_OK
        if action == 'start':
            if voting.start_date:
                msg = 'Voting already started'
                st = status.HTTP_400_BAD_REQUEST
            else:
                voting.start_date = timezone.now()
                voting.save()
                msg = 'Voting started'
        elif action == 'stop':
            if not voting.start_date:
                msg = 'Voting is not started'
                st = status.HTTP_400_BAD_REQUEST
            elif voting.end_date:
                msg = 'Voting already stopped'
                st = status.HTTP_400_BAD_REQUEST
            else:
                voting.end_date = timezone.now()
                voting.save()
                msg = 'Voting stopped'
        elif action == 'tally':
            if not voting.start_date:
                msg = 'Voting is not started'
                st = status.HTTP_400_BAD_REQUEST
            elif not voting.end_date:
                msg = 'Voting is not stopped'
                st = status.HTTP_400_BAD_REQUEST
            elif voting.tally:
                msg = 'Voting already tallied'
                st = status.HTTP_400_BAD_REQUEST
            else:
                voting.tally_votes(request.auth.key)

                msg = 'Voting tallied'

        else:
            msg = 'Action not found, try with start, stop or tally'
            st = status.HTTP_400_BAD_REQUEST
        return Response(msg, status=st)
