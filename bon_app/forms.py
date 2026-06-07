from django import forms
from django.contrib.auth.models import User

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'password','required':'required'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'confirm password','required':'required'}))

    class Meta:
        model = User
        fields = ['username','email']
        widgets = {
            'username':forms.TextInput(attrs={'placeholder':'username','required':'required'}),
            'email':forms.EmailInput(attrs={'placeholder':'email','required':'required'})
        }
        
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('user already exists with that username!')
        return username
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')    
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password','re-enter password')
         
        
    def save(self,commit=True):
        user = super().save(commit= False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

class logged_in(forms.Form):
    username = forms.CharField(max_length=140) 
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'password','required':'required'}))

class OrderForm(forms.Form):
    name    = forms.CharField(label="Your Name", max_length=100)
    email   = forms.EmailField(label="Email")
    address = forms.CharField(label="Shipping Address", widget=forms.Textarea)
    