from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.core.exceptions import PermissionDenied
from django import forms 

from .models import Ad, Category


class AdForm(forms.ModelForm):
    class Meta:
        model = Ad
        fields = ['title', 'description', 'price', 'category']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }


def ad_list(request):
    ads = Ad.objects.select_related('category', 'author').all()
    categories = Category.objects.all()

    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()

    if query:
        ads = ads.filter(Q(title__icontains=query) | Q(description__icontains=query))

    if category_id:
        ads = ads.filter(category_id=category_id)

    paginator = Paginator(ads, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
    }
    return render(request, 'ads/ad_list.html', context)


def ad_detail(request, pk):
    ad = get_object_or_404(Ad.objects.select_related('category', 'author'), pk=pk)
    return render(request, 'ads/ad_detail.html', {'ad': ad})


@login_required
def ad_create(request):
    if request.method == 'POST':
        form = AdForm(request.POST)
        if form.is_valid():
            ad = form.save(commit=False)
            ad.author = request.user
            ad.save()
            return redirect('ad_detail', pk=ad.pk)
    else:
        form = AdForm()
    return render(request, 'ads/ad_form.html', {'form': form, 'title': 'Создать объявление'})


@login_required
def ad_edit(request, pk):
    ad = get_object_or_404(Ad, pk=pk)
    if ad.author != request.user:
        raise PermissionDenied("Вы не можете редактировать чужое объявление.")

    if request.method == 'POST':
        form = AdForm(request.POST, instance=ad)
        if form.is_valid():
            form.save()
            return redirect('ad_detail', pk=ad.pk)
    else:
        form = AdForm(instance=ad)
    return render(request, 'ads/ad_form.html', {'form': form, 'title': 'Редактировать объявление'})


@login_required
def ad_delete(request, pk):
    ad = get_object_or_404(Ad, pk=pk)
    if ad.author != request.user:
        raise PermissionDenied("Вы не можете удалить чужое объявление.")

    if request.method == 'POST':
        ad.delete()
        return redirect('ad_list')

    return render(request, 'ads/ad_confirm_delete.html', {'ad': ad})


@login_required
def my_ads(request):
    ads = Ad.objects.filter(author=request.user).select_related('category')
    paginator = Paginator(ads, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'ads/my_ads.html', {'page_obj': page_obj})


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('ad_list')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})