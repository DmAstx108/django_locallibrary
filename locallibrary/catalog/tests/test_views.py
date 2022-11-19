from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Permission
from django.views import generic
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from catalog.forms import RenewBookForm
from catalog.models import BookInstance, Book, Genre, Language, Author


class AuthorListViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create 13 authors for pagination tests
        number_of_authors = 13
        for author_num in range(number_of_authors):
            Author.objects.create(first_name='Christian %s' %
                                  author_num, last_name='Surname %s' % author_num,)

    def test_view_url_exists_at_desired_location(self):
        resp = self.client.get('/catalog/authors/')
        self.assertEqual(resp.status_code, 200)

    def test_view_url_accessible_by_name(self):
        resp = self.client.get(reverse('authors'))
        self.assertEqual(resp.status_code, 200)

    def test_view_uses_correct_template(self):
        resp = self.client.get(reverse('authors'))
        self.assertEqual(resp.status_code, 200)

        self.assertTemplateUsed(resp, 'catalog/author_list.html')

    def test_pagination_is_ten(self):
        resp = self.client.get(reverse('authors'))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('is_paginated' in resp.context)
        self.assertTrue(resp.context['is_paginated'] == True)
        self.assertTrue(len(resp.context['author_list']) == 10)

    def test_lists_all_authors(self):
        # Get second page and confirm it has (exactly) remaining 3 items
        resp = self.client.get(reverse('authors')+'?page=2')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('is_paginated' in resp.context)
        self.assertTrue(resp.context['is_paginated'] == True)
        self.assertTrue(len(resp.context['author_list']) == 3)


class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """
    Обобщённый класс отображения списка взятых книг текущим пользователем
    """
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')


class LoanedBookInstancesByUserListViewTest(TestCase):

    def setUp(self):
        # Создание двух пользователей
        test_user1 = User.objects.create_user(
            username='testuser1', password='12345')
        test_user1.save()
        test_user2 = User.objects.create_user(
            username='testuser2', password='12345')
        test_user2.save()

        # Создание книги
        test_author = Author.objects.create(
            first_name='John', last_name='Smith')
        test_genre = Genre.objects.create(name='Fantasy')
        test_language = Language.objects.create(name='English')
        test_book = Book.objects.create(
            title='Book Title', summary='My book summary', isbn='ABCDEFG', author=test_author, language=test_language)
        # Create genre as a post-step
        genre_objects_for_book = Genre.objects.all()
        # Присвоение типов many-to-many напрямую недопустимо
        test_book.genre.set(genre_objects_for_book)
        test_book.save()

        # Создание 30 объектов BookInstance
        number_of_book_copies = 30
        for book_copy in range(number_of_book_copies):
            return_date = timezone.now() + datetime.timedelta(days=book_copy % 5)
            if book_copy % 2:
                the_borrower = test_user1
            else:
                the_borrower = test_user2
            status = 'm'
            BookInstance.objects.create(book=test_book, imprint='Unlikely Imprint, 2016',
                                        due_back=return_date, borrower=the_borrower, status=status)

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('my-borrowed'))
        self.assertRedirects(resp, '/accounts/login/?next=/catalog/mybooks/')

    def test_logged_in_uses_correct_template(self):
        login = self.client.login(username='testuser1', password='12345')
        resp = self.client.get(reverse('my-borrowed'))

        # Проверка что пользователь залогинился
        self.assertEqual(str(resp.context['user']), 'testuser1')
        # Проверка ответа на запрос
        self.assertEqual(resp.status_code, 200)

        # Проверка того, что мы используем правильный шаблон
        self.assertTemplateUsed(
            resp, 'catalog/bookinstance_list_borrowed_user.html')


# Если пользователь не залогирован то, чтобы убедиться в том что отображение перейдёт на страницу входа(логирования), мы используем метод assertRedirects, что продемонстрировано в методе test_redirect_if_not_logged_in(). Затем мы осуществляем вход для пользователя и проверяем что полученный статус status_code равен 200 (успешно).

# Остальные тесты проверяют, соответственно, что наше отображение показывает только те книги которые взяты текущим пользователем. Скопируйте код, показанный ниже, в нижнюю часть предыдущего класса.

    def test_only_borrowed_books_in_list(self):
        login = self.client.login(username='testuser1', password='12345')
        resp = self.client.get(reverse('my-borrowed'))

        # Проверка, что пользователь залогинился
        self.assertEqual(str(resp.context['user']), 'testuser1')
        # Check that we got a response "success"
        self.assertEqual(resp.status_code, 200)

        # Проверка, что изначально у нас нет книг в списке
        self.assertTrue('bookinstance_list' in resp.context)
        self.assertEqual(len(resp.context['bookinstance_list']), 0)

        # Теперь все книги "взяты на прокат"
        get_ten_books = BookInstance.objects.all()[:10]

        for copy in get_ten_books:
            copy.status = 'o'
            copy.save()

        # Проверка, что все забронированные книги в списке
        resp = self.client.get(reverse('my-borrowed'))
        # Проверка, что пользователь залогинился
        self.assertEqual(str(resp.context['user']), 'testuser1')
        # Проверка успешности ответа
        self.assertEqual(resp.status_code, 200)

        self.assertTrue('bookinstance_list' in resp.context)

        # Подтверждение, что все книги принадлежат testuser1 и взяты "на прокат"
        for bookitem in resp.context['bookinstance_list']:
            self.assertEqual(resp.context['user'], bookitem.borrower)
            self.assertEqual('o', bookitem.status)

    def test_pages_ordered_by_due_date(self):

        # Изменение статуса на "в прокате"
        for copy in BookInstance.objects.all():
            copy.status = 'o'
            copy.save()

        login = self.client.login(username='testuser1', password='12345')
        resp = self.client.get(reverse('my-borrowed'))

        # Пользователь залогинился
        self.assertEqual(str(resp.context['user']), 'testuser1')
        # Check that we got a response "success"
        self.assertEqual(resp.status_code, 200)

        # Подтверждение, что из всего списка показывается только 10 экземпляров
        self.assertEqual(len(resp.context['bookinstance_list']), 10)

        last_date = 0
        for copy in resp.context['bookinstance_list']:
            if last_date == 0:
                last_date = copy.due_back
            else:
                self.assertTrue(last_date <= copy.due_back)


def test_only_borrowed_books_in_list(self):
    login = self.client.login(username='testuser1', password='12345')
    resp = self.client.get(reverse('my-borrowed'))

    # Проверка, что пользователь залогинился
    self.assertEqual(str(resp.context['user']), 'testuser1')
    # Check that we got a response "success"
    self.assertEqual(resp.status_code, 200)

    # Проверка, что изначально у нас нет книг в списке
    self.assertTrue('bookinstance_list' in resp.context)
    self.assertEqual(len(resp.context['bookinstance_list']), 0)

    # Теперь все книги "взяты на прокат"
    get_ten_books = BookInstance.objects.all()[:10]

    for copy in get_ten_books:
        copy.status = 'o'
        copy.save()

    # Проверка, что все забронированные книги в списке
    resp = self.client.get(reverse('my-borrowed'))
    # Проверка, что пользователь залогинился
    self.assertEqual(str(resp.context['user']), 'testuser1')
    # Проверка успешности ответа
    self.assertEqual(resp.status_code, 200)

    self.assertTrue('bookinstance_list' in resp.context)

    # Подтверждение, что все книги принадлежат testuser1 и взяты "на прокат"
    for bookitem in resp.context['bookinstance_list']:
        self.assertEqual(resp.context['user'], bookitem.borrower)
        self.assertEqual('o', bookitem.status)


def test_pages_ordered_by_due_date(self):

    # Изменение статуса на "в прокате"
    for copy in BookInstance.objects.all():
        copy.status = 'o'
        copy.save()

    login = self.client.login(username='testuser1', password='12345')
    resp = self.client.get(reverse('my-borrowed'))

    # Пользователь залогинился
    self.assertEqual(str(resp.context['user']), 'testuser1')
    # Check that we got a response "success"
    self.assertEqual(resp.status_code, 200)

    # Подтверждение, что из всего списка показывается только 10 экземпляров
    self.assertEqual(len(resp.context['bookinstance_list']), 10)

    last_date = 0
    for copy in resp.context['bookinstance_list']:
        if last_date == 0:
            last_date = copy.due_back
        else:
            self.assertTrue(last_date <= copy.due_back)


@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
    """
    Функция отображения обновления экземпляра BookInstance библиотекарем
    """
    book_inst = get_object_or_404(BookInstance, pk=pk)

    # Если это POST-запрос, тогда обработать данные формы
    if request.method == 'POST':

        # Создать объект формы и заполнить её данными из запроса (связывание/биндинг):
        form = RenewBookForm(request.POST)

        # Проверка валидности формы:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            book_inst.due_back = form.cleaned_data['renewal_date']
            book_inst.save()

            # переход по URL-адресу:
            return HttpResponseRedirect(reverse('all-borrowed'))

    # Если это GET-запрос (или что-то ещё), то создаём форму по умолчанию
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date, })

    return render(request, 'catalog/book_renew_librarian.html', {'form': form, 'bookinst': book_inst})


class RenewBookInstancesViewTest(TestCase):

    def setUp(self):
        # Создание пользователя
        test_user1 = User.objects.create_user(
            username='testuser1', password='12345')
        test_user1.save()

        test_user2 = User.objects.create_user(
            username='testuser2', password='12345')
        test_user2.save()
        permission = Permission.objects.get(name='Set book as returned')
        test_user2.user_permissions.add(permission)
        test_user2.save()

        # Создание книги
        test_author = Author.objects.create(
            first_name='John', last_name='Smith')
        test_genre = Genre.objects.create(name='Fantasy')
        test_language = Language.objects.create(name='English')
        test_book = Book.objects.create(title='Book Title', summary='My book summary',
                                        isbn='ABCDEFG', author=test_author, language=test_language,)
        # Создание жанра Create genre as a post-step
        genre_objects_for_book = Genre.objects.all()
        test_book.genre = genre_objects_for_book
        test_book.save()

        # Создание объекта BookInstance для для пользователя test_user1
        return_date = datetime.date.today() + datetime.timedelta(days=5)
        self.test_bookinstance1 = BookInstance.objects.create(
            book=test_book, imprint='Unlikely Imprint, 2016', due_back=return_date, borrower=test_user1, status='o')

        # Создание объекта BookInstance для для пользователя test_user2
        return_date = datetime.date.today() + datetime.timedelta(days=5)
        self.test_bookinstance2 = BookInstance.objects.create(
            book=test_book, imprint='Unlikely Imprint, 2016', due_back=return_date, borrower=test_user2, status='o')
