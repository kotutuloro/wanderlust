# accounts/forms.py
from django.forms import ModelForm, ModelChoiceField
from .models import Trip, Destination


class TripForm(ModelForm):
    class Meta:
        model = Trip
        fields = ("title", "start_date", "end_date", "scheduled", "notes")


class DestinationForm(ModelForm):
    trip = ModelChoiceField(queryset=Trip.objects, required=False,
                            empty_label="--- (Create a new trip for this destination) ---")

    class Meta:
        model = Destination
        fields = ("trip", "name", "start_time", "end_time")

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
        return (self.cleaned_data['trip']
                or Trip.objects.create(owner=self.user, title=self.data.get('name')))
