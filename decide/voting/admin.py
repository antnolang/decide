from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils import timezone
from xlrd import XLRDError

from .forms import ImportSenateCandidates

from .models import QuestionOption
from .models import Question
from .models import Voting

from .filters import StartedFilter
from store.models import Vote


def start(modeladmin, request, queryset):
    for v in queryset.all():
        v.create_pubkey()
        v.start_date = timezone.now()
        v.save()


def stop(ModelAdmin, request, queryset):
    for v in queryset.all():
        v.end_date = timezone.now()
        v.save()


def tally(ModelAdmin, request, queryset):
    for v in queryset.filter(end_date__lt=timezone.now()):
        token = request.session.get('auth-token', '')
        v.tally_votes(token)


def deleteAll(ModelAdmin, request, queryset):
    for v in queryset:
       
        votes = Vote.objects.all()

        for i in votes:
            if i.voting_id == v.id:
                i.delete()
                v.delete()


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    fields = ['question', 'option', 'gender']


class QuestionAdmin(admin.ModelAdmin):
    inlines = [QuestionOptionInline]


class VotingAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date')
    readonly_fields = ('start_date', 'end_date', 'pub_key',
                       'tally', 'postproc')
    date_hierarchy = 'start_date'
    list_filter = (StartedFilter,)
    search_fields = ('name', )

    actions = [start, stop, tally, deleteAll]

    def add_view(self, request, form_url='', extra_context=None):
        if request.method == 'POST':
            form = ImportSenateCandidates(request.POST, request.FILES)
            if form.is_valid():
                try:
                    form.save()
                    messages.success(request, 'All votings created correctly')
                    return HttpResponseRedirect('/admin/voting/voting')
                except AssertionError as msg_error:
                    messages.error(request, msg_error)
                    return HttpResponseRedirect('')
                except XLRDError:
                    messages.error(request, 'Unsupported format or corrupt '
                                            'file. The file must be a valid '
                                            'excel')
                except Exception:
                    messages.error(request, 'Could not commit the operation. '
                                            'Please, try again or contact with'
                                            ' an administrator')
                    return HttpResponseRedirect('')
            else:
                messages.error(request, 'Please, select a file')

        context = dict(title='Import votings')
        context.update(extra_context or {})

        return render(request, 'voting/import_form.html', context)

    def delete_model(self, request, obj):
        votes = Vote.objects.all()

        for i in votes:
            if i.voting_id == obj.id:
                i.delete()

        super(VotingAdmin, self).delete_model(request, obj)


admin.site.register(Voting, VotingAdmin)
admin.site.register(Question, QuestionAdmin)
