from django.contrib import admin

from .models import Author, Book, BookInstance, Genre, Language


class AuthorInline(admin.TabularInline):
    model = Book


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    """Поле "list_display" будет отображаться снаружи,
    Home › Catalog › Authors ."""
    list_display = (
        'last_name',
        'first_name',
        'date_of_birth',
        'date_of_death'
    )
    """Поле "fields" будет отображаться внутри, после нажатия "add author".
    Home › Catalog › Authors › Add author """
    fields = ['first_name', 'last_name', ('date_of_birth', 'date_of_death')]
    inlines = [AuthorInline]


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name',)


class BooksInstanceInline(admin.TabularInline):
    model = BookInstance


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'display_genre')
    inlines = [BooksInstanceInline]


@admin.register(BookInstance)
class BookInstanceAdmin(admin.ModelAdmin):
    list_display = ('book', 'status', 'borrower', 'due_back', 'id')
    list_filter = ('status', 'due_back')

    fieldsets = (
        (None, {
            'fields': ('book', 'imprint', 'id')
        }),
        ('Availability', {
            'fields': ('status', 'due_back', 'borrower')
        }),
    )

# admin.site.register(Book)
# admin.site.register(BookInstance)
# admin.site.register(Author, AuthorAdmin)
# admin.site.register(Genre)


# Genre.objects.create(name="Fantasy")
# Genre.objects.all()
# from catalog.models import Author
