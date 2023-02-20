import shutil
import tempfile

from http import HTTPStatus
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
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

        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_form(self):
        """Валидная форма create создает запись в Post."""
        form_data = {
            'text': 'Текст поста из формы',
            'group': self.group.pk,
            'image': self.uploaded,
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
            (post.group.id, form_data['group']),
            (post.image, 'posts/small.gif'),
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

    def test_add_comment(self):
        """Валидная форма создает комментарий к посту."""
        post = Post.objects.create(
            author=self.user,
            text='Тестовая запись',
        )
        form_data = {
            'text': 'Тестовый комментарий',
            'post': post.pk
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment', kwargs={'post_id': post.pk}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), 1)
        self.assertTrue(
            Comment.objects.filter(
                text='Тестовый комментарий',
                post=post,
            ).exists()
        )
