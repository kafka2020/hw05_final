from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post, Comment, Follow

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.new_user = User.objects.create_user(username='new_auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост в котором больше, чем 15 символов',
            group=cls.group
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий'
        )
        cls.follower = Follow.objects.create(
            user=cls.user,
            author=cls.new_user,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем корректную работу __str__."""
        expected_object_name = (
            (str(self.group), self.group.title),
            (str(self.post), self.post.text[:settings.STRING_LENGTH]),
            (str(self.comment), self.comment.text[:settings.STRING_LENGTH]),
            (str(self.follower), f'{self.user} подписан на {self.new_user}'),
        )
        for instance, expected in expected_object_name:
            with self.subTest(instance=instance):
                self.assertEqual(instance, expected)

    def test_field_verboses_for_models(self):
        """Проверяем verbose names."""
        post = PostModelTest.post
        comment = PostModelTest.comment
        follower = PostModelTest.follower
        field_verboses_post = {
            'text': 'Текст поста',
            'group': 'Группа',
            'image': 'Картинка',
        }
        field_verboses_comment = {
            'post': 'Комментарий',
            'author': 'Автор комментария',
            'text': 'Содержание комментария',
        }
        field_verboses_follower = {
            'user': 'Подписчик',
            'author': 'Автор',
        }
        for field, expected in field_verboses_post.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected)
        for field, expected in field_verboses_comment.items():
            with self.subTest(field=field):
                self.assertEqual(
                    comment._meta.get_field(field).verbose_name, expected)
        for field, expected in field_verboses_follower.items():
            with self.subTest(field=field):
                self.assertEqual(
                    follower._meta.get_field(field).verbose_name, expected)

    def test_help_texts_for_models(self):
        """Проверяем help_text."""
        post = PostModelTest.post
        comment = PostModelTest.comment
        field_help_texts_post = {
            'group': 'Группа, к которой будет относиться пост',
            'text': 'Текст нового поста',
        }
        field_help_texts_comment = {
            'post': 'Оставьте комментарий',
            'text': 'Введите текст комментария',
        }
        for field, expected in field_help_texts_post.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected)
        for field, expected in field_help_texts_comment.items():
            with self.subTest(field=field):
                self.assertEqual(
                    comment._meta.get_field(field).help_text, expected)
