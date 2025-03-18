# accounts/forms.py
from django.forms import (ModelForm, ModelChoiceField, DateInput,
                          DateTimeInput, HiddenInput, CharField, TextInput)
from django.urls import reverse_lazy
from .models import Trip, Destination


class UIDateInput(DateInput):
    input_type = "date"


class UIDateTimeInput(DateTimeInput):
    input_type = "datetime-local"


class TripForm(ModelForm):
    class Meta:
        model = Trip
        fields = ("title", "start_date", "end_date", "scheduled", "notes")
        widgets = {
            "start_date": UIDateInput(),
            "end_date": UIDateInput(),
        }


class DestinationForm(ModelForm):
    trip = ModelChoiceField(queryset=Trip.objects, required=False,
                            empty_label="--- (Create a new trip for this destination) ---")

    location = CharField(required=False,
                         template_name="trips/location_search_field_snippet.html",
                         widget=TextInput(attrs={
                             "placeholder": "(Search for a new location)",
                             "hx-post": reverse_lazy("trips:search-loc"),
                             "hx-params": "location",
                             "hx-target": "next #id_location_results",
                             "hx-swap": "outerHTML",
                             "hx-trigger": "input delay:250ms",
                         }))

    class Meta:
        model = Destination
        fields = ("trip", "name", "location",
                  "mapbox_id", "start_time", "end_time")
        widgets = {
            "mapbox_id": HiddenInput(),
            "start_time": UIDateTimeInput(),
            "end_time": UIDateTimeInput(),
        }

    def __init__(self, *args, **kwargs):
        only_trip = kwargs.pop("only_trip", None)
        self.user = kwargs.pop("user", None)
        if not (only_trip or self.user):
            raise Exception(
                "DestinationForm requires either a user or a specific trip")
        super().__init__(*args, **kwargs)

        if only_trip:
            self.fields['trip'].queryset = Trip.objects.filter(pk=only_trip.pk)
            self.fields['trip'].initial = only_trip
            self.fields['trip'].disabled = True
        else:
            self.fields['trip'].queryset = Trip.objects.filter(owner=self.user)

    def clean_trip(self):
        if self.cleaned_data['trip']:
            return self.cleaned_data['trip']
        if self.user and self.data.get('name'):
            return Trip.objects.create(owner=self.user, title=self.data.get('name'))
