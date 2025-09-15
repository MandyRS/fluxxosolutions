from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Post
from .forms import PostForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.http import HttpResponseForbidden

# Página listar últimos artigos
def blog(request):
    posts = Post.objects.order_by('-data_publicacao')
    return render(request, 'blog.html', {'posts': posts})

# Ver detalhes de um artigo
def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug)
    return render(request, 'post_detail.html', {'post': post})

# Login
def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('blog')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

# Logout
def user_logout(request):
    logout(request)
    return redirect('blog')



# Criar novo post (só pra quem estiver logado)
@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.autor = request.user
            post.save()
            return redirect(post.get_absolute_url())
    else:
        form = PostForm()
    return render(request, 'post_form.html', {'form': form})

# Editar post (só autor pode editar)
@login_required
def post_edit(request, slug):
    post = get_object_or_404(Post, slug=slug)
    if post.autor != request.user:
        return HttpResponseForbidden("Você não tem permissão para editar este post.")
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect(post.get_absolute_url())
    else:
        form = PostForm(instance=post)
    return render(request, 'post_form.html', {'form': form, 'post': post})

# Deletar post
@login_required
def post_delete(request, slug):
    post = get_object_or_404(Post, slug=slug)
    if post.autor != request.user:
        return HttpResponseForbidden("Você não tem permissão para deletar este post.")
    if request.method == 'POST':
        post.delete()
        return redirect('blog')
    return render(request, 'post_confirm_delete.html', {'post': post})
