from .models import ArticlePost
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import ArticlePostForm
from django.contrib.auth.models import User
import markdown
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from comment.models import Comment

def article_list(request):
    search = request.GET.get('search')
    order = request.GET.get('order')
    if search:
        if order == 'total_views':
            article_list = ArticlePost.objects.filter(
            Q(title__icontains = search)|
            Q(body__icontains = search)
            ).order_by('-total_views')
        else:
            article_list = ArticlePost.objects.filter(
            Q(title__icontains = search)|
            Q(body__icontains = search)
            )
    else:
        seach = ''
        if order == 'total_views':
            article_list = ArticlePost.objects.all().order_by('-total_views')
        else:
            article_list = ArticlePost.objects.all()

    paginator = Paginator(article_list, 6)
    page = request.GET.get('page')
    articles = paginator.get_page(page)

    context = {'articles':articles, 'order': order, 'search': search}

    return render(request, 'article/list.html', context)

def article_detail(request, id):
    article = ArticlePost.objects.get(id = id)
    comments = Comment.objects.filter(article = id)
    article.total_views += 1
    article.save(update_fields = ['total_views'])
    md = markdown.Markdown(
    extensions = [
    'markdown.extensions.extra',
    'markdown.extensions.codehilite',
    # directory
    'markdown.extensions.toc',
    ])

    article.body = md.convert(article.body)
    context = {'article': article, 'toc': md.toc, 'comments': comments}
    return render(request, 'article/detail.html', context)

def article_create(request):
    if request.method == "POST":
        article_post_form = ArticlePostForm(data = request.POST)
        if article_post_form.is_valid():
            new_article = article_post_form.save(commit = False)
            if not request.user.id:
                return HttpResponse("please log in first")
            new_article.author = User.objects.get(id = request.user.id)
            new_article.save()
            return redirect("article:article_list")
        else:
            return HttpResponse("illegal post request, please write again")
    else:
        article_post_form = ArticlePostForm()
        context = {'article_post_form':article_post_form}
        return render(request, 'article/create.html', context)

@login_required(login_url='/userprofile/login/')
def article_safe_delete(request, id):
    if request.method == 'POST':
        article = ArticlePost.objects.get(id = id)
        if request.user != article.author:
            return HttpResponse("You are not authorized to edit this article")
        article.delete()
        return redirect("article:article_list")
    else:
        return HttpResponse("only post request allowed")

@login_required(login_url='/userprofile/login/')
def article_update(request, id):
    article = ArticlePost.objects.get(id = id)
    if request.user != article.author:
        return HttpResponse("You are not authorized to edit this article")
    if request.method == "POST":
        article_post_form = ArticlePostForm(data = request.POST)
        if article_post_form.is_valid():
            article.title = request.POST['title']
            article.body = request.POST['body']
            article.save()
            return redirect("article:article_detail",id = id)
        else:
            return HttpResponse("illegal post request, please write again")
    # if GET
    else:
        article_post_form = ArticlePostForm()
        context = {'article':article, 'article_post_form': article_post_form}
        return render(request, 'article/update.html', context)
