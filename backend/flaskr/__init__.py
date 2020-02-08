import os, random, sys, traceback
from flask import Flask, request, abort, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

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
      return 404

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
      return 422

    questions = Question.query.filter_by(category=category_id).all()
    questions_displayed = paginate_questions(request, questions, page=page)

    # If page number doesn't exist, returns 404.
    if not questions_displayed:
      return 404

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
      return 422

    question_to_delete = Question.query.get(quest_id)
    # Checks if question ID exists.
    if not question_to_delete:
      return 404

    try:
      question_to_delete.delete()
      db.session.commit()

    except:
      db.session.rollback()
      exc_type, exc_value, exc_traceback = sys.exc_info()

      print("*** print_exception:")
      traceback.print_exception(exc_type, exc_value, exc_traceback, limit = 2, file = sys.stdout)
      return 418

    return jsonify({
      'id': quest_id,
      'success': True
      }), 200

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

    