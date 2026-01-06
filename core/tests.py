from django.test import TestCase, Client


class HelloWorldTest(TestCase):
    def test_hello_world(self):
        client = Client()
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello, CI/CD World!")
