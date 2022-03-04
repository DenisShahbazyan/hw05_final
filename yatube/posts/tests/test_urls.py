from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = User.objects.create_user(username='TestUser_1')
        cls.user_2 = User.objects.create_user(username='TestUser_2')

        cls.post_1 = Post.objects.create(
            author=cls.user_1,
            text='Тестовый текст 1',
        )

        cls.post_2 = Post.objects.create(
            author=cls.user_2,
            text='Тестовый текст 2',
        )

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client_1 = Client()
        self.authorized_client_1.force_login(self.user_1)

        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user_2)

    # Проверка доступности страниц
    def test_url_exists_at_desired_location_anonymous(self):
        """Страницы доступны не авторизованному пользователю."""
        urls = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user_1.username}/',
            f'/posts/{self.post_1.id}/',
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_exists_at_desired_location_authorized(self):
        """Страницы доступны авторизованному пользователю."""
        urls = [
            '/create/',
            '/follow/',
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client_1.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_exists_at_desired_location_author(self):
        """Страница доступна только автору."""
        response = self.authorized_client_1.get(
            f'/posts/{self.post_1.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_no_exists_at_desired_location_no_author(self):
        """Страница доступна автору."""
        response = self.authorized_client_2.get(
            f'/posts/{self.post_1.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_url_no_exists(self):
        """Несуществующая страница должна вернуть код 404"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    # Проверяем редиректы для неавторизованного пользователя
    def test_url_redirect_anonymous_on_user_login(self):
        """Страница перенаправит анонимного пользователя
        на страницу логина.
        """
        urls = [
            '/create/',
            f'/posts/{self.post_1.id}/edit/',
            '/follow/',
            f'/profile/{self.user_1}/follow/',
            f'/profile/{self.user_1}/unfollow/',
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, f'/auth/login/?next={url}')

    # Проверка вызываемых шаблонов для каждого адреса
    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user_1.username}/': 'posts/profile.html',
            f'/posts/{self.post_1.id}/': 'posts/post_detail.html',
            f'/posts/{self.post_1.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client_1.get(url)
                self.assertTemplateUsed(response, template)
