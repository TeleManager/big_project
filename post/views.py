from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect, get_list_or_404
from .models import Post, Comment
from .forms import PostForm, CommentForm
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages

def index(request):
    posts = Post.objects.all()
    return render(request, 'post/post_list.html', {'posts': posts})


def post_list(request):
    posts = Post.objects.all()
    search_key = request.GET.get("keyword")
    
    if search_key:
        posts = posts.filter(Q(title__icontains=search_key))
        
    return render(request, 'post/post_list.html', {'posts': posts, 'q': search_key})
 
def index(request):
    posts = Post.objects.all()
    search_key = request.GET.get("keyword", "")
    print(search_key)
    if search_key:
        print(search_key)
        posts = Post.objects.filter(title__icontains=search_key)
       
    return render(request, 'post/post_list.html', {'posts':posts, 'q':search_key})


    # posts = Post.objects.all()
    # return render(request, 'post/post_list.html', {'posts': posts})
 
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comments = post.comment_set.all()  # 댓글을 가져오는 부분을 수정
    return render(request, 'post/post_detail.html', {'post': post, 'comments': comments})


@login_required
def post_new(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.created = timezone.now()
            post.save()
            return redirect('post:post_list')
    else:
        form = PostForm()
    return render(request, 'post/post_form.html', {'form': form})
 
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        post.delete()
        return redirect('post:post_list')
    return render(request, 'post/post_delete.html', {'post': post})
 
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
   
    if request.method == 'GET':
        form = PostForm(instance=post)
       
    elif request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save()
            return redirect('post:post_detail', pk=pk)
       
    return render(request, 'post/post_edit.html', {
        'form': form,
    })

def Comment2(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comments = CommentForm(request.POST)
    if comments.is_valid():
        comments = comments.save(commit=False)
        comments.post = get_object_or_404(Post, pk=pk)
        comments.user = request.user
        comments.save()
    return redirect('post:post_detail', pk=pk)
    

def comment_delete(request, pk, comment_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, pk=pk)
        
        # Comment 모델의 쿼리셋을 사용하여 댓글을 가져옴
        comment = get_object_or_404(Comment, pk=comment_id, post=post)

        # Check if the logged-in user has the permission to delete the comment
        if request.user.is_authenticated and request.user == comment.user:
            comment.delete()
            messages.success(request, 'Comment deleted successfully.')
        else:
            messages.error(request, 'You do not have permission to delete this comment.')

        return redirect('post:post_detail', pk=pk)
    else:
        # Handle cases where 'GET' request is received (e.g., direct URL access)
        messages.error(request, 'Invalid request method.')
        return redirect('post:post_detail', pk=pk)
    
    # post = get_object_or_404(Post, id=pk)
    # comment = get_object_or_404(Comment, id=comment_id)
    # comment.delete()   
    # return redirect('post:post_detail', pk=pk)



