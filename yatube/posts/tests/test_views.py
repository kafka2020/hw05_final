import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTests(TestCase):

    # Количество записей в БД
    COUNT_OF_REC = 15

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_without_post = User.objects.create_user(
            username='auth_without_post'
        )
        cls.group_1 = Group.objects.create(
            title='Тестовая группа № 1',
            slug='test_slug_1',
            description='Тестовое описание № 1',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа № 2',
            slug='test_slug_2',
            description='Тестовое описание № 2',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image_gif = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.new_image_gif = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif',
        )
        cls.new_user = User.objects.create_user(username='auth_1')
        # список объектов Post для БД
        objs = list()
        for post_number in range(1, cls.COUNT_OF_REC + 1):
            objs.append(
                Post(
                    author=cls.user,
                    text=f'Тестовый пост и содержит номер: {post_number}',
                    group=cls.group_1,
                    image=cls.image_gif,
                )
            )
        Post.objects.bulk_create(objs)
        cls.post = Post.objects.filter(author=cls.user).latest('pub_date')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_without_post = Client()
        self.authorized_client_without_post.force_login(self.new_user)
        cache.clear()

    def test_pages_uses_correct_templates(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group_1.slug}): 'posts/group_list.html',
            reverse('posts:profile', kwargs={
                    'username': self.user.username}): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={
                    'post_id': self.post.id}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={
                    'post_id': self.post.id}): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """
        Шаблон index сформирован с правильным контекстом.
        Передается список постов.
        """
        response = self.authorized_client.get(reverse('posts:index'))
        last_object = response.context['page_obj'][0]
        expected_post = self.post
        last_object_expected_post_fields = {
            last_object.text: expected_post.text,
            last_object.pub_date: expected_post.pub_date,
            last_object.group: expected_post.group,
            last_object.image: expected_post.image,
        }
        for last_object_field, expected_post_field in (
            last_object_expected_post_fields.items()
        ):
            with self.subTest(last_object=last_object):
                self.assertEqual(
                    last_object_field,
                    expected_post_field,
                    'Ошибка передачи контекста в index'
                )

    def test_group_list_page_show_correct_context(self):
        """
        Шаблон group_list сформирован с правильным контекстом.
        Передается список постов группы.
        """
        group_1 = self.group_1
        slug = group_1.slug
        expected_post = group_1.posts.latest('pub_date')
        response = (
            self.
            authorized_client.
            get(reverse('posts:group_list', kwargs={'slug': slug}))
        )
        last_object = response.context['page_obj'][0]
        last_object_expected_post_fields = {
            last_object.text: expected_post.text,
            last_object.pub_date: expected_post.pub_date,
            last_object.author: expected_post.author,
            last_object.image: expected_post.image
        }
        for last_object_field, expected_post_field in (
            last_object_expected_post_fields.items()
        ):
            with self.subTest(last_object=last_object):
                self.assertEqual(
                    last_object_field,
                    expected_post_field,
                    'Ошибка передачи контекста в group_list'
                )

    def test_profile_page_show_correct_context(self):
        """
        Шаблон profile сформирован с правильным контекстом.
        Передается список постов группы.
        """
        user = self.user
        response = (
            self.
            authorized_client.
            get(reverse('posts:profile', kwargs={'username': user.username}))
        )
        last_object = response.context['page_obj'][0]
        expected_post = user.posts.latest('pub_date')
        last_object_expected_post_fields = {
            last_object.text: expected_post.text,
            last_object.pub_date: expected_post.pub_date,
            last_object.image: expected_post.image,
        }
        for last_object_field, expected_post_field in (
            last_object_expected_post_fields.items()
        ):
            with self.subTest(last_object=last_object):
                self.assertEqual(
                    last_object_field,
                    expected_post_field,
                    'Ошибка передачи контекста в profile'
                )

    def test_not_group_page_show_correct(self):
        """Пост не попал в группу, для которой не был предназначен."""
        user = self.user
        group_2 = self.group_2
        slug = group_2.slug
        response = (
            self.
            authorized_client.
            get(reverse('posts:group_list', kwargs={'slug': slug}))
        )
        objects_group_2 = response.context['page_obj']
        self.assertNotIn(
            user.posts.latest('pub_date'),
            objects_group_2,
            'Новый пост появляется не в той группе'
        )

    def test_post_detail_page_show_correct_context(self):
        """
        Шаблон post_detail сформирован с правильным контекстом.
        Передается пост c заданным id.
        """
        user = self.user
        post_id = self.post.id
        response = (
            self.
            authorized_client.
            get(reverse('posts:post_detail', kwargs={'post_id': post_id}))
        )
        last_object = response.context['post']
        expected_post = user.posts.get(id=post_id)
        last_object_expected_post_fields = {
            last_object.text: expected_post.text,
            last_object.image: expected_post.image,
        }
        for last_object_field, expected_post_field in (
            last_object_expected_post_fields.items()
        ):
            with self.subTest(last_object=last_object):
                self.assertEqual(
                    last_object_field,
                    expected_post_field,
                    'Ошибка передачи контекста в post_detail'
                )

    def test_create_post_page_show_correct_context(self):
        """
        Шаблон create_post сформирован с правильным контекстом.
        Передается форма с text и списком group.
        """
        response = (
            self.
            authorized_client.
            get(reverse('posts:post_create'))
        )
        post_id = self.post.id
        response_edit = (
            self.
            authorized_client.
            get(reverse('posts:post_edit', kwargs={'post_id': post_id}))
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(
                    form_field,
                    expected,
                    'Ошибка передачи контекста в create_post'
                )
                form_field = (
                    response_edit.
                    context.get('form').
                    fields.get(value)
                )
                self.assertIsInstance(
                    form_field,
                    expected,
                    (
                        'Ошибка передачи контекста в create_post'
                        'при редактировании'
                    )
                )

    def test_pages_contains_required_counts_records(self):
        """На страницах 1 и 2 выводится необходимое количество постов"""
        posts_on_first_page = settings.POSTS_ON_PAGE
        posts_on_second_page = (self.COUNT_OF_REC
                                - settings.POSTS_ON_PAGE)
        slug = self.group_1.slug
        username = self.user.username
        numbers = {
            posts_on_first_page: [
                reverse('posts:index'),
                reverse('posts:profile', kwargs={'username': username}),
                reverse('posts:group_list', kwargs={'slug': slug}),
            ],
            posts_on_second_page: [
                reverse('posts:index') + '?page=2',
                reverse(
                    'posts:profile', kwargs={'username': username}
                ) + '?page=2',
                reverse(
                    'posts:group_list', kwargs={'slug': slug}
                ) + '?page=2',
            ]
        }
        for number, urls in numbers.items():
            for url in urls:
                with self.subTest(url=url):
                    response = self.authorized_client.get(url)
                    self.assertEqual(
                        len(response.context['page_obj']),
                        number,
                        (
                            f'На странице {url}'
                            ' выводится неправильное количество постов'
                        )
                    )

    def test_edit_post(self):
        """Редактирование поста пользователем."""
        url_post_edit = reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.id}
        )
        response = self.authorized_client.get(url_post_edit)
        form_data = response.context['form'].initial
        changed_text = 'Изменение'
        form_data['text'] = changed_text
        form_data['image'] = self.new_image_gif
        response = self.authorized_client.post(
            url_post_edit,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id}
        ))
        changed_post = Post.objects.get(id=self.post.id)
        self.assertEqual(changed_post.text, changed_text)

    def test_cache_index_page(self):
        """Работа кеша на главной странице"""
        response_0 = self.authorized_client.get('/')
        Post.objects.latest('pub_date').delete()
        response_1 = self.authorized_client.get('/')
        cache.clear()
        response_2 = self.authorized_client.get('/')
        self.assertEqual(
            response_0.content,
            response_1.content,
            'Кеширование на главной странице не осуществляется'
        )
        self.assertNotEqual(
            response_1.content,
            response_2.content,
            'После обновления кеша главная страница не обновляется'
        )

    def test_add_comment_authorized_client(self):
        """
        Комментировать посты может только авторизованный пользователь
        и комментарий создаётся
        """
        comment_id = 1
        form_data = {'text': 'Мой комментарий'}
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data
        )
        self.assertEqual(
            Comment.objects.get(id=comment_id).text,
            'Мой комментарий',
            'Комментарий не создается')
        self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(
            self.post.comments.get(id=comment_id).text,
            'Мой комментарий',
            'Авторизованный пользователь не может создать комментарий'
        )

    def test_add_comment_guest_client(self):
        """
        Неавторизованный пользователь не может комментировать посты
        и комментарий не создаётся
        """
        comment_id = 1
        form_data = {'text': 'Тестовый комментарий'}
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data
        )
        with self.assertRaisesMessage(
            ObjectDoesNotExist,
            'Comment matching query does not exist'
        ):
            Comment.objects.get(id=comment_id)
