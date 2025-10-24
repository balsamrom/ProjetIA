from django import forms
from .models import Destination

class DestinationForm(forms.ModelForm):
    class Meta:
        model = Destination
        fields = '__all__'
        widgets = {
            'destination': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'cultural_significance': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'cost_of_living': forms.TextInput(attrs={'class': 'form-control'}),
        }