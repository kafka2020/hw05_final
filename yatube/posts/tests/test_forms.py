from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_form(self):
        """Валидная форма create создает запись в Post."""
        form_data = {
            'text': 'Текст поста из формы',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        post = Post.objects.last()
        check_post_fields = (
            (post.author, self.user),
            (post.text, form_data['text']),
            (post.group.id, form_data['group'])
        )
        for new_post, expected in check_post_fields:
            with self.subTest(new_post=new_post):
                self.assertEqual(new_post, expected)
        self.assertEqual(Post.objects.count(), 1)

    def test_edit_form(self):
        """Валидная форма edit редактирует запись в Post."""
        new_group = Group.objects.create(
            title='Новая группа',
            slug='new-slug',
            description='Новое описание группы',
        )
        post = Post.objects.create(
            author=self.user,
            text='Тестовая запись',
            group=self.group,
        )
        form_data = {
            'text': 'Редактированный текст',
            'group': new_group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=(post.id,)),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.last()
        check_edited_post_fields = (
            (post.author, self.user),
            (post.text, 'Редактированный текст'),
            (post.group, new_group),
        )
        for new_post, expected in check_edited_post_fields:
            with self.subTest(new_post=new_post):
                self.assertEqual(new_post, expected)
        self.assertEqual(self.group.posts.count(), 0)
