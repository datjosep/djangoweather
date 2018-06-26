from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class data_form(forms.Form):
    site = forms.CharField(max_length=4, required=True)
    start_time = forms.DateTimeField(input_formats=['%Y,%m,%d,%H,%M'], required=True)
    end_time = forms.DateTimeField(input_formats=['%Y,%m,%d,%H,%M'], required=True)

    def __init__(self, *args, **kwargs):
        super(data_form, self).__init__(*args, **kwargs)
        self.fields['site'].label = "Name of radar site, should be 4 letter all caps."
        self.fields['start_time'].label = "Input date should resemble this format: (2013, 5, 31, 17, 0). Year, Month, Day, Hr, minute."
        self.fields['end_time'].label = "Input date should resemble this format: (2013, 5, 31, 17, 0). Year, Month, Day, Hr, minute."


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', )