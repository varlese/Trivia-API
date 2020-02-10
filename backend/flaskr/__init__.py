import os, random, sys, traceback
from flask import Flask, request, abort, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

from models import *

# ----------------------------------------------------------------------
# Utils
# ----------------------------------------------------------------------

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

# Set up function to validate if difficulty level is valid.

def is_valid_difficulty(difficulty):
  difficulty = int(difficulty)
  if difficulty >= 1 or difficulty <= 5:
    return True
  else:
    return False

# ----------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  app.url_map.strict_slashes = False
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

# ----------------------------------------------------------------------
# Endpoints
# ----------------------------------------------------------------------

  # Endpoint to handle GET requests for all available categories.
  @app.route('/categories', methods=['GET'])
  def get_categories():
      categories = Category.query.all()
      return jsonify({
        'success': True,
        'categories': [category.format() for category in categories],
      }), 200

  # Endpoint to handle GET requests for questions, paginated by QUESTIONS_PER_PAGE, showing all questions.
  @app.route('/questions', methods=['GET'])
  @app.route('/questions/<int:page>', methods=['GET'])
  def get_questions(page=False):
    # Get categories for JSON return for frontend.
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

  # Endpoint to handle GET request for questions, paginated by QUESTIONS_PER_PAGE and filtered by category ID.
  # Uses paginate_questions for the pagination.
  @app.route('/categories/<category>/questions', methods=['GET'])
  @app.route('/categories/<category>/questions/<int:page>', methods=['GET'])
  def get_questions_by_category(category, page=False):
    category_data = False

    # Checks for valid category ID.
    if category.isnumeric():
      category_data = Category.query.get(category)
      category_id = category

    # Checks for category type and converts to ID if found.
    if not category_data:
      category_data = Category.query.filter_by(type=category).first()
      category_id = category_data.id

    # If category is not found, returns error message.
    if not category_data:
      abort(422)

    questions = Question.query.filter_by(category=category_id).all()
    questions_displayed = paginate_questions(request, questions, page=page)

    # If page number doesn't exist, returns 404.
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

  # Endpoint to handle DELETE requests using question ID.
  @app.route('/delete/<int:quest_id>', methods=['DELETE'])
  def delete_questions(quest_id):
    # Checks that question ID is not 0.
    if not quest_id:
      abort(422)

    question_to_delete = Question.query.get(quest_id)
    # Checks if question ID exists.
    if not question_to_delete:
      abort(404)

    try:
      question_to_delete.delete()
      db.session.commit()

    except:
      db.session.rollback()
      exc_type, exc_value, exc_traceback = sys.exc_info()

      print("*** print_exception:")
      traceback.print_exception(exc_type, exc_value, exc_traceback, limit = 2, file = sys.stdout)
      abort(418)

    return jsonify({
      'id': quest_id,
      'success': True
      }), 200

  '''
  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''

  # Endpoint to add new questions to the database.
  @app.route('/add', methods=['POST'])
  def add_questions():
    question = request.args.get('question'),
    answer = request.args.get('answer'),
    category = request.args.get('category'),
    difficulty = request.args.get('difficulty')

    # Checks for values for each required field, otherwise throws a 422.
    if not question:
      abort(422)
    if not answer:
      abort(422)
    if not category:
      abort(422)
    if not difficulty:
      abort(422)

    # Values are returned as a tuple - ensures we're only comparing the first value.
    category = category[0]
    category_data = False
    # Checks for valid category ID.
    if category.isnumeric():
      category_data = Category.query.get(category)
      category_id = category

    # Checks for category type and converts to ID if found.
    if not category_data:
      category_data = Category.query.filter_by(type=category).first()
      category_id = category_data.id

    # If category is not found, returns error message.
    if not category_data:
      abort(422)

    if not is_valid_difficulty(difficulty):
      abort(422)

    new_question = Question(
      question = question,
      answer = answer,
      category = category_id,
      difficulty = difficulty
    )

    try:
      db.session.add(new_question)
      db.session.commit()
      data = {
        'id': new_question.id,
        'question': new_question.question,
        'answer': new_question.answer,
        'category': new_question.category,
        'difficulty': new_question.difficulty
      }

    except:
      db.session.rollback()
      exc_type, exc_value, exc_traceback = sys.exc_info()

      print("*** print_exception:")
      traceback.print_exception(exc_type, exc_value, exc_traceback, limit = 2, file = sys.stdout)
      abort(418)

    return jsonify({
      'question': data,
      'success': True
      }), 200

  '''
  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''

  # Endpoint to handle search requests.
  @app.route('/search/<search_term>', methods=['POST'])
  @app.route('/search/<search_term>/<int:page>', methods=['POST'])
  def find_questions(search_term, page=False):
    search_data = Question.query.filter(Question.question.ilike('%' + search_term + '%')).all()
    displayed_results = paginate_questions(request, search_data, page=page)

    if not displayed_results:
      abort(404)

    return jsonify({
      'results': displayed_results,
      'success': True,
      'total_questions': len(search_data),
      'next_url': url_for('find_questions', search_term=search_term, page=page+1)
    }), 200


  '''
  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''

  # Endpoint to play quiz that filters by category and previous questions that have been answered. 
  @app.route('/quizzes', methods=['POST'])
  def play_quiz():
    body = request.get_json()
    category = int(body['category'])
    previous_questions = body['previous_questions']

    quiz_category = Category.query.get(category)
    if not quiz_category:
      abort(404)

    # Breaking up questions query to make the code cleaner. 
    questions = Question.query.filter_by(category=category)
    if previous_questions:
      questions = questions.filter(Question.id.notin_(previous_questions))
    questions = questions.all()
    print(questions)
    if not questions:
      abort(404)

    return jsonify({
      'category': category,
      'previous_questions': previous_questions,
      'question': random.choice(questions).format(),
      'success': True
    }), 200


  '''
  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''

  #Error handler for objects that cannot be found in the database.
  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      "success": False, 
      "error": 404,
      "message": "Item not found."
      }), 404

  #Error handler for total fails. 
  @app.errorhandler(418)
  def teapot(error):
    return jsonify({
      "success": False, 
      "error": 418,
      "message": "Server refuses to brew coffee because it's a teapot"
      }), 418

  #Error handler for requests that cannot be processed.
  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      "success": False, 
      "error": 422,
      "message": "Request could not be processed."
      }), 422

  
  return app

    