from django import forms


class RegistrationForm(forms.Form):
    name = forms.CharField(max_length=60)
    email = forms.EmailField(max_length=254)
    phone = forms.CharField(max_length=16, required=False, help_text="Optional: 7–15 digits, with an optional leading +.")
    password = forms.CharField(widget=forms.PasswordInput, min_length=8, max_length=128, strip=False)


class LoginForm(forms.Form):
    identifier = forms.CharField(label="Email or phone", max_length=254)
    password = forms.CharField(widget=forms.PasswordInput, max_length=128, strip=False)
