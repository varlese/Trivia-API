import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy
from flaskr import create_app, QUESTIONS_PER_PAGE
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgres://{}/{}".format('localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
    
    def tearDown(self):
        """Executed after reach test"""
        pass

    def test_im_learning_testing(self):
        self.assertTrue(True)

    def test_should_return_all_categories(self):
        res = self.client().get('/categories')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])

        categories = Category.query.all()
        self.assertEqual(len(data['categories']), len(categories))

    def test_get_categories_dont_accept_post_request(self):
        res = self.client().post('/categories')
        self.assertEqual(res.status_code, 405)

    def test_should_get_first_page_questions(self):
        res = self.client().get('/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        # Makes sure the request is properly paginated.
        self.assertEqual(len(data['questions']), QUESTIONS_PER_PAGE)

        questions = Question.query.all()
        # Asserting that pagination worked.
        self.assertEqual(data['total_questions'], len(questions))

    def test_should_allow_second_page_questions(self):
        res = self.client().get('/questions/2')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])

        questions = Question.query.all()
        # Asserting that pagination worked.
        self.assertEqual(data['total_questions'], len(questions))

        # Makes sure the request is properly paginated.
        self.assertEqual(len(data['questions']), len(questions) - QUESTIONS_PER_PAGE)

    def test_should_not_allow_third_page_questions(self):
        res = self.client().get('/questions/3')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['error'], 404)
        self.assertFalse(data['success'])

    def test_should_filter_questions_by_sports_category(self):
        res = self.client().get('/categories/6/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])

        sports_questions = Question.query.filter_by(category=6).all()
        self.assertEqual(data['total_questions'], len(sports_questions))

    def test_should_not_return_second_page_of_sports_questions(self):
        res = self.client().get('/categories/6/questions/2')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['error'], 404)
        self.assertFalse(data['success'])


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()