import unittest
from email_extractor import clean_email_addresses, should_skip_email, extract_body
from unittest.mock import MagicMock

class TestEmailExtractor(unittest.TestCase):
    def test_clean_email_addresses(self):
        # Test to ensure email addresses are removed
        text = "Contact us at example@example.com for more info."
        expected_text = "Contact us at  for more info."
        self.assertEqual(clean_email_addresses(text), expected_text)

        # Test to ensure multiple email addresses are removed
        text_multiple = "Emails: first@test.com, second@test.com"
        expected_text_multiple = "Emails: , "
        self.assertEqual(clean_email_addresses(text_multiple), expected_text_multiple)

    def test_should_skip_email(self):
        # Test to skip email based on subject containing 're:'
        self.assertTrue(should_skip_email("Re: Inquiry"))
        # Test to skip email based on subject containing delivery failure notice
        self.assertTrue(should_skip_email("delivery status notification (failure)"))
        # Test not to skip email with unrelated subject
        self.assertFalse(should_skip_email("Welcome to our newsletter"))

    def test_extract_body(self):
        # Create a mock message object for multipart email
        message = MagicMock()
        message.is_multipart.return_value = True
        part = MagicMock()
        part.get_content_type.return_value = 'text/plain'
        part.get_payload.return_value = b'Hello, this is the body of the email.'
        message.walk.return_value = [part]

        # Test extraction of body from multipart email
        self.assertEqual(extract_body(message), 'Hello, this is the body of the email.')

        # Create a mock message object for non-multipart email
        message_non_multipart = MagicMock()
        message_non_multipart.is_multipart.return_value = False
        message_non_multipart.get_payload.return_value = b'Simple body content'
        # Test extraction of body from non-multipart email
        self.assertEqual(extract_body(message_non_multipart), 'Simple body content')

if __name__ == '__main__':
    unittest.main()