from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic.base import TemplateView
from .forms import UserUpdateForm, ProfileUpdateForm
from .models import CustomUser as User
from base64 import urlsafe_b64decode, urlsafe_b64encode
from django.contrib import auth
from colorama import reinit
from django.shortcuts import redirect, render
from django.views import View
import json
from django.http import JsonResponse
from matplotlib.cbook import silent_list
from validate_email import validate_email 
from django.contrib import messages
from django.core.mail import EmailMessage
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site
from .utils import token_generator


class RegistrationView(View):
    def get(self,request):
        return render(request,'users/register.html')

    def post(self,request):
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        context = {
            'fieldValues' : request.POST
        }
        if not User.objects.filter(username=username).exists():
            if not User.objects.filter(email=email).exists():
                if password == password2:
                    user = User.objects.create_user(username=username,email=email)
                    user.set_password(password)
                    user.is_active = False
                    user.save()
                    
                    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                    domain = get_current_site(request).domain
                    link = reverse('users:activate',kwargs={'uidb64':uidb64,'token':token_generator.make_token(user)})
                    active_url = 'http://'+domain+link     
                    email_subject = 'Active your account'
                    email_body = f'Hi {user.username}. Please use this link to verify your account\n'+active_url
                    email = EmailMessage(
                        email_subject,
                        email_body,
                        'from@example.com',
                        [email],
                    )

                    email.send(fail_silently=True)     
                    return redirect('users:registration_under_approval_url')
        return render(request,'users/register.html',context)

class VerificationView(View):
    def get(self,request,uidb64,token):
        try:
            id = force_str(urlsafe_base64_decode)
            user = User.objects.get(pk=id)

            if not token_generator.check_token(user, token):
                return redirect('login'+'?message='+'User already activate')
            if user.is_active:
                return redirect('users:registration_under_approval_url')
            user.is_active = True
            user.save()
            return redirect('users:registration_under_approval_url')
        except:
            pass
        return redirect('login')

class RegistrationUnderApproval(TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Do something here!
        return context


@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST,
                                   request.FILES,
                                   instance=request.user.profile)
        if u_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect('profile')

    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }

    return render(request, 'users/profile.html', context)
