from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase


from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    """TestCase для urls."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_without_post = User.objects.create_user(
            username='auth_without_post'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост в котором больше, чем 15 символов',
            group=cls.group
        )
        # список url доступных всем
        cls.urls = [
            '/',
            f'/group/{cls.group.slug}/',
            f'/profile/{cls.user.username}/',
            f'/posts/{cls.post.id}/',
        ]
        cls.url_templates_names = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user.username}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{cls.post.id}/edit/': 'posts/create_post.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_url_is_for_guests(self):
        """Доступность страниц любому пользователю."""
        urls = PostURLTests.urls
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f'Страница {url} недоступна любому пользователю.'
                )

    def test_url_is_for_user(self):
        """Доступность страницы 'create/' зарегистрированным пользователям."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(
            response.status_code,
            HTTPStatus.OK,
            'Страница create/ не доступна зарегистрированным пользователям.'
        )

    def test_url_is_for_author(self):
        """Доступность cтраницы 'posts/<int:post_id>/edit/' автору поста."""
        post_id = PostURLTests.post.id
        response = self.authorized_client.get(f'/posts/{post_id}/edit/')
        self.assertEqual(
            response.status_code,
            HTTPStatus.OK,
            'Страница posts/<int:post_id>/edit/ не доступна автору поста.'
        )

    def test_non_existent_url(self):
        """Запрос к несуществующей странице."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(
            response.status_code,
            HTTPStatus.NOT_FOUND,
            'Запрос к несуществующей странице не возвращает ошибку 404.'
        )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_templates_names = PostURLTests.url_templates_names
        for address, template in url_templates_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(
                    response,
                    template,
                    f'URL-адрес: {address} использует неправильный шаблон'
                )

    def test_posts_urls_redirection_for_guest_client(self):
        """Редирект неавторизованного пользователя"""
        urls = {
            '/create/': '/auth/login/?next=/create/',
            '/posts/1/edit/': '/auth/login/?next=/posts/1/edit/'
        }
        for route, redirect_page in urls.items():
            with self.subTest(redirect_page=redirect_page):
                response = self.guest_client.get(route, follow=True)
                self.assertRedirects(response, redirect_page)
