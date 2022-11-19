import datetime

from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.views import View, generic
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from .forms import RenewBookForm, RenewBookModelForm
from .models import Author, Book, BookInstance, Genre


class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """
    Generic class-based view listing books on loan to current user.
    """
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(
            borrower=self.request.user).filter(status__exact='o').order_by('due_back')


class AllLoanedBooks(ListView):
    permission_required = ('catalog.can_mark_returned',
                           'catalog.view_bookinstance')
    template_name = 'catalog/bookinstance_list_borrowed_librarians.html'
    model = BookInstance


# def get_queryset(request):
#     #     return BookInstance.objects.filter(
#     #         borrower='librarian').filter(status__exact='o').order_by('due_back')

#     template_name = 'catalog/bookinstance_list_borrowed_librarians.html'
#     bor_filt = BookInstance.objects.all()

#     context = {'bor_filt': bor_filt}

#     return render(request, template_name, context)


def index(request):
    """
    Функция отображения для домашней страницы сайта.
    """
    # Генерация "количеств" некоторых главных объектов
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()
    # Доступные книги (статус = 'a')
    num_instances_available = BookInstance.objects.filter(
        status__exact='a').count()
    # Метод 'all()' применён по умолчанию.
    num_authors = Author.objects.count()  # The 'all()' is implied by default.

    # Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits+1

    # Render the HTML template index.html with the data in the context variable.
    return render(
        request,
        'index.html',
        context={'num_books': num_books, 'num_instances': num_instances, 'num_instances_available': num_instances_available, 'num_authors': num_authors,
                 'num_visits': num_visits},  # num_visits appended
    )


# def book_detail_view(request, pk):
#     try:
#         book_id = Book.objects.get(pk=pk)
#     except Book.DoesNotExist:
#         raise get_object_or_404("Book does not exist")

#     #book_id=get_object_or_404(Book, pk=pk)

#     return render(
#         request,
#         'catalog/book_detail.html',
#         context={'book': book_id, }
#     )


# def author_detail_view(request, pk):
#     author_id = get_object_or_404(Author, pk=pk)

#     #book_id=get_object_or_404(Book, pk=pk)

#     return render(
#         request,
#         'catalog/author_detail.html',
#         context={'author': author_id, }
#     )

# class BookListView(generic.ListView):
#     model = Book
#     # ваше собственное имя переменной контекста в шаблоне
#     context_object_name = 'my_book_list'
#     # Получение 5 книг, содержащих слово 'war' в заголовке
#     queryset = Book.objects.filter(title__icontains='war')[:5]
#     # Определение имени вашего шаблона и его расположения
#     template_name = 'books/my_arbitrary_template_name_list.html'


class BookListView(generic.ListView):
    model = Book
    paginate_by = 10

    def get_context_data(self, **kwargs):
        # В первую очередь получаем базовую реализацию контекста
        context = super(BookListView, self).get_context_data(**kwargs)
        # Добавляем новую переменную к контексту и инициализируем её некоторым значением
        context['some_data'] = 'This is just some data'
        return context


class BookDetailView(generic.DetailView):
    model = Book


class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 10

    def get_context_data(self, **kwargs):
        # В первую очередь получаем базовую реализацию контекста
        context = super(AuthorListView, self).get_context_data(**kwargs)
        # Добавляем новую переменную к контексту и инициализируем её некоторым значением
        context['some_data'] = 'This is just some data'
        return context


class AuthorDetailView(generic.DetailView):
    model = Author


@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
    """
    View function for renewing a specific BookInstance by librarian
    """
    book_inst = get_object_or_404(BookInstance, pk=pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = RenewBookForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            book_inst.due_back = request.POST['renewal_date']
            book_inst.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('total-borrowed'))

    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookModelForm(
            initial={'renewal_date': proposed_renewal_date, })

    return render(request, 'catalog/book_renew_librarian.html', {'form': form, 'bookinst': book_inst})


class AuthorCreate(CreateView):
    model = Author
    fields = '__all__'
    initial = {'date_of_death': '12/10/2016', }


class AuthorUpdate(UpdateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']


class AuthorDelete(DeleteView):
    model = Author
    success_url = reverse_lazy('authors')


class BookCreate(CreateView):
    model = Book
    fields = '__all__'
    initial = {'genre': 'Fantasy', }


class BookUpdate(UpdateView):
    model = Book
    fields = ['title', 'author', 'summary', 'genre']


class BookDelete(DeleteView):
    model = Book
    success_url = reverse_lazy('authors')
