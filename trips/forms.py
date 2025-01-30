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
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields['trip'].queryset = Trip.objects.filter(owner=self.user)

    def clean_trip(self):
        return (self.cleaned_data['trip']
                or Trip.objects.create(owner=self.user, title=self.data.get('name')))
