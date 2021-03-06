from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from yatube.settings import COUNT_POST_FOR_PAGE

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post


def include_paginator(request, db_object):
    paginator = Paginator(db_object, COUNT_POST_FOR_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


def index(request):
    post_list = Post.objects.all()
    page_obj = include_paginator(request, post_list)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = include_paginator(request, post_list)

    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    count_posts = author.posts.all().count()
    posts = author.posts.all()
    page_obj = include_paginator(request, posts)

    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user).filter(author=author).exists()

    context = {
        'author': author,
        'count_posts': count_posts,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    author = post.author
    count_posts = author.posts.all().count()
    comments = Comment.objects.filter(post_id=post_id)
    form = CommentForm(request.POST or None)

    context = {
        'count_posts': count_posts,
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@ login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user)
    return render(request, 'posts/create_post.html', {'form': form})


@ login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post.id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:post_detail', post.id)

    context = {
        'is_edit': True,
        'post': post,
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@ login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@ login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = include_paginator(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@ login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author == request.user:
        return redirect('posts:profile', username=username)
    Follow.objects.get_or_create(
        user=request.user,
        author=author
    )
    return redirect('posts:profile', username=username)


@ login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user).filter(author=author).delete()
    return redirect('posts:profile', username=username)
