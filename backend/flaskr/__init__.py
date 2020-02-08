import os
from flask import Flask, request, abort, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import *

# Set up a function to paginate trivia questions with 10 results per page.
# Returns the list of 10 questions. 
QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection, page):
  if not page:
    page = request.args.get('page', 1, type=int)
  start = (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions = [question.format() for question in selection]
  questions_displayed = questions[start:end]

  return questions_displayed

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)

  # CORS app
  cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

  # CORS Headers 
  @app.after_request
  def after_request(response):
      response.headers.add(
        'Access-Control-Allow-Headers',
        'Content-Type,Authorization,true'
      )
      response.headers.add(
        'Access-Control-Allow-Methods',
        'GET,PATCH,POST,DELETE,OPTIONS'
      )
      return response

  # Endpoint to handle GET requests for all available categories.
  @app.route('/categories', methods=['GET'])
  def get_categories():
      categories = Category.query.all()
      return jsonify({
        'success': True,
        'categories': [category.format() for category in categories],
      }), 200

  # Endpoint to handle GET requests for questions, paginated by QUESTIONS_PER_PAGE, showing all questions.
  @app.route('/questions', methods=['GET'], strict_slashes=False)
  @app.route('/questions/<int:page>', methods=['GET'], strict_slashes=False)
  def get_questions(page=False):
    # Get categories for JSON return for frontend
    categories = Category.query.all()
    # Get all questions
    questions = Question.query.all()
    questions_displayed = paginate_questions(request, questions, page=page)
    if not questions_displayed:
      abort(404)

    return jsonify({
      'questions': questions_displayed,
      'categories': [category.format() for category in categories],
      'success': True,
      'total_questions': len(questions),
      'next_url': url_for('get_questions', page=page+1)
      }), 200

  # Endpoint to handle GET request for questions, paginated by QUESTIONS_PER_PAGE and filtered by category.
  # Uses paginate_questions for the pagination.
  @app.route('/categories/<category>/questions', methods=['GET'], strict_slashes=False)
  @app.route('/categories/<category>/questions/<int:page>', methods=['GET'], strict_slashes=False)
  def get_questions_by_category(category, page=False):
    questions = Question.query.filter_by(category=category).all()
    questions_displayed = paginate_questions(request, questions, page=page)
    if not questions_displayed:
      abort(404)

    return jsonify({
      'questions': questions_displayed,
      'success': True,
      'total_questions': len(questions),
      'next_url': url_for('get_questions_by_category', category=category, page=page+1)
      }), 200

  '''
  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''

  @app.route('/delete/<int:quest_id>', methods=['DELETE'])
  def delete_questions(quest_id):
    question_to_delete = Question.query.filter_by(id = quest_id)
    question_to_delete.delete()
    db.session.commit()
    return 'OK'

  '''
  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''

  @app.route('/add', methods=['POST'])
  def add_questions():
    new_question = Question(
      question = request.args.get('question'),
      answer = request.args.get('answer'),
      category = request.args.get('category'),
      difficulty = request.args.get('difficulty')
    )
    db.session.add(new_question)
    # question_id = new_question.id
    db.session.commit()
    
    return 'OK'

  '''
  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''

  @app.route('/search/<term>', methods=['POST'])
  def find_questions(term):
    search_term = request.args.get('term')
    print(search_term)
    # search_data = Question.query.filter(Question.question.ilike('%' + search_term + '%')).all()
    return 'OK'

    # if not search_data:
    #   abort(404)

    # return jsonify({
    #   'questions': search_data,
    #   'categories': [category.format() for category in categories],
    #   'success': True,
    #   'total_questions': len(questions)
    #   }), 200

  '''
  @TODO: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''

  '''
  @TODO: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''

  '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
  
  return app

    