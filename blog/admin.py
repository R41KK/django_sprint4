from django.contrib import admin

from .models import Category, Comment, Location, Post


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "is_published", "created_at")
    list_filter = ("is_published",)
    search_fields = ("title",)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "is_published", "created_at")
    list_filter = ("is_published",)
    search_fields = ("name",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "category",
        "location",
        "pub_date",
        "is_published",
        "created_at",
    )
    list_filter = ("is_published", "category", "location")
    search_fields = ("title", "text")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("short_text", "author", "post", "created_at")
    list_filter = ("created_at",)
    search_fields = ("text", "author__username")

    @admin.display(description="Текст комментария")
    def short_text(self, obj):
        return obj.text[:50]
