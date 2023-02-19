from http import HTTPStatus

from django.test import Client, TestCase


class ViewTestClass(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_error_page(self):
        self.guest_client = Client()
        response = self.guest_client.get('/none/')
        self.assertEqual(
            response.status_code,
            HTTPStatus.NOT_FOUND,
            'Запрос к несуществующей странице не возвращает ошибку 404.',
        )
        template = 'core/404.html'
        self.assertTemplateUsed(
            response,
            template,
            msg_prefix='Страница с ошибкой 404 содержит неправильный шаблон',
        )
