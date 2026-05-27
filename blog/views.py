from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import CommentForm, CustomUserCreationForm, PostForm, UserProfileForm
from .models import Category, Comment, Post

User = get_user_model()

POSTS_PER_PAGE = 10


def get_filtered_posts(posts=None):
    if posts is None:
        posts = Post.objects.all()
    return (
        posts.select_related("category", "location", "author")
        .annotate(comment_count=Count("comments"))
        .filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True,
        )
    )


class PostListView(ListView):
    model = Post
    template_name = "blog/index.html"
    context_object_name = "page_obj"
    paginate_by = POSTS_PER_PAGE

    def get_queryset(self):
        return get_filtered_posts().order_by("-pub_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_obj"] = context["page_obj"]
        return context


class PostDetailView(DetailView):
    model = Post
    template_name = "blog/detail.html"
    pk_url_kwarg = "post_id"
    context_object_name = "post"

    def get_object(self, queryset=None):
        post = super().get_object(queryset)
        if (
            post.pub_date > timezone.now()
            or not post.is_published
            or not post.category.is_published
        ) and post.author != self.request.user:
            raise Http404()
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = CommentForm()
        context["comments"] = self.object.comments.select_related("author")
        return context


class CategoryPostsView(ListView):
    template_name = "blog/category.html"
    context_object_name = "page_obj"
    paginate_by = POSTS_PER_PAGE

    def get_queryset(self):
        self.category = get_object_or_404(
            Category, slug=self.kwargs["slug"], is_published=True
        )
        return get_filtered_posts().filter(category=self.category).order_by("-pub_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = self.category
        return context


class UserProfileView(ListView):
    template_name = "blog/profile.html"
    context_object_name = "page_obj"
    paginate_by = POSTS_PER_PAGE

    def get_queryset(self):
        self.profile = get_object_or_404(User, username=self.kwargs["username"])
        posts = (
            Post.objects.select_related("category", "location", "author")
            .annotate(comment_count=Count("comments"))
            .filter(author=self.profile)
        )
        if self.request.user != self.profile:
            posts = posts.filter(
                pub_date__lte=timezone.now(),
                is_published=True,
                category__is_published=True,
            )
        return posts.order_by("-pub_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile"] = self.profile
        return context


class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = "blog/user.html"

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse("blog:profile", kwargs={"username": self.request.user.username})


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = "blog/create.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("blog:profile", kwargs={"username": self.request.user.username})


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = "blog/create.html"
    pk_url_kwarg = "post_id"

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return redirect("blog:post_detail", post_id=post.id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("blog:post_detail", kwargs={"post_id": self.object.id})


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = "blog/create.html"
    pk_url_kwarg = "post_id"

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return redirect("blog:post_detail", post_id=post.id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("blog:profile", kwargs={"username": self.request.user.username})


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, pk=self.kwargs["post_id"])
        return super().form_valid(form)

    def get_success_url(self):
        return (
            reverse("blog:post_detail", kwargs={"post_id": self.kwargs["post_id"]})
            + f"#comment_{self.object.id}"
        )


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = "blog/comment.html"
    pk_url_kwarg = "comment_id"

    def dispatch(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user:
            return redirect("blog:post_detail", post_id=comment.post.id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return (
            reverse("blog:post_detail", kwargs={"post_id": self.object.post.id})
            + f"#comment_{self.object.id}"
        )


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = "blog/comment.html"
    pk_url_kwarg = "comment_id"

    def dispatch(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user:
            return redirect("blog:post_detail", post_id=comment.post.id)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comment"] = self.object
        return context

    def get_success_url(self):
        return reverse("blog:post_detail", kwargs={"post_id": self.object.post.id})


class UserRegistrationView(CreateView):
    form_class = CustomUserCreationForm
    template_name = "registration/registration_form.html"
    success_url = reverse_lazy("login")


# Старые view-функции для обратной совместимости
def index(request):
    post_list = get_filtered_posts().order_by("-pub_date")
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {"page_obj": page_obj}
    return render(request, "blog/index.html", context)


def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related("category", "location", "author"),
        pk=post_id,
    )
    if (
        post.pub_date > timezone.now()
        or not post.is_published
        or not post.category.is_published
    ) and post.author != request.user:
        raise Http404()
    form = CommentForm()
    comments = post.comments.select_related("author")
    context = {"post": post, "form": form, "comments": comments}
    return render(request, "blog/detail.html", context)


def category_posts(request, slug):
    category = get_object_or_404(Category, slug=slug, is_published=True)
    post_list = (
        Post.objects.select_related("category", "location", "author")
        .annotate(comment_count=Count("comments"))
        .filter(
            category=category,
            pub_date__lte=timezone.now(),
            is_published=True,
        )
        .order_by("-pub_date")
    )
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "category": category,
        "page_obj": page_obj,
    }
    return render(request, "blog/category.html", context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect("blog:post_detail", post_id=post_id)
    return redirect("blog:post_detail", post_id=post_id)
