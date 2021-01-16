import os, sys
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

'''
Create and setup flask app and init db
'''
def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  CORS(app)

  # CORS Headers 
  @app.after_request
  def after_request(response):
      response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
      response.headers.add('Access-Control-Allow-Methods', 'GET,PATCH,POST,DELETE,OPTIONS')
      return response

  '''
  Endpoint to handle GET requests for all available categories.
  '''
  @app.route('/categories', methods=['GET'])
  def get_all_categories():
    #take all categories from DB and format them
    categories=[category.format() for category in Category.query.all()]
    return jsonify({
      'success':True,
      'categories':categories,
      'total_categories':len(categories)
    })

  '''
  Endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 
  '''
  @app.route('/questions',methods=['GET'])
  def get_questions():
    '''
    Get all questions
    '''
    # paginate questions, and store the current page questions in a list
    page = request.args.get('page', 1, type=int)
    selection = Question.query.order_by(Question.id).paginate(page, QUESTIONS_PER_PAGE, True)
    total_questions = selection.total
    
    if total_questions == 0:
        # no questions are found, abort with a 404 error.
        abort(404)
    
    current_questions = [question.format() for question in selection.items]
    # load all categories from db
    categories=[category.format() for category in Category.query.all()]
    
    return jsonify({
        'success': True,
        'questions': current_questions,
        'total_questions': total_questions,
        'categories': categories
    })


  '''
  Create an endpoint to DELETE question using a question ID. 
  '''
  @app.route('/questions/<question_id>', methods=['Delete'])
  def delete_question(question_id):
    '''Delete a question from the database'''
    try:
        question = Question.query.filter(Question.id == question_id).one_or_none()
        # return 404 if question is not available
        if question is None:
            abort(404)
        
        question.delete()
        
        return jsonify({
            'success': True,
            'deleted': question_id
        })
    except:
        # rollback and close the connection
        db.session.rollback()
        abort(422)

  '''
  Endpoint to POST a new question, 
  which will require the question and answer text, category, and difficulty score.
  '''
  @app.route('/questions', methods=['POST'])
  def create_questions():
    try:
      request_body = request.get_json()
      # needs to have a body 
      if not request_body:
        abort(400)
      # extract data from body for question
      new_question = Question(
          request_body['question'],
          request_body['answer'],
          request_body['category'],
          request_body['difficulty']
      )
      # QA check on difficulty
      if not 1 <= int(request_body['difficulty']) < 6:
        abort(400)
      # validating that the quesiton and answer must be present
      if request_body['question'] == '' or request_body['answer'] == '':
        raise TypeError
      # insert the new question
      new_question.insert()

      return jsonify({
          'success': True
      }), 201

    except TypeError:
        abort(422)

    except:
        abort(500)


  '''
  Endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 
  '''
  @app.route('/questions/search', methods={'POST'})
  def search_questions():
    request_body = request.get_json()
    search_term = request_body.get('search_term')
    current_category = request_body.get('current_category') 
    
    if not request_body:
      # body should have valid json
      abort(400)

    if search_term: 
      #query db for the paginated results
      page = request.args.get('page', 1, type=int)
      results = Question.query.filter(
            Question.question.ilike(f'%{search_term}%')).paginate(page, QUESTIONS_PER_PAGE, True)
      total_questions = results.total
      
      if total_questions == 0:
        # no questions returned from db
        abort(404)
      
      current_questions = [question.format() for question in results.items]
      
      return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': total_questions,
            'search_term': search_term
        }), 200
    else: 
      # if no search term no search
      abort(400)


  ''' 
  Endpoint to get questions based on category. 
  '''
  @app.route('/categories/<category_id>/questions', methods=['GET'])
  def search_questions_by_category(category_id):
    '''Get all questions in a category'''
    category = Category.query.filter(Category.id == category_id).one_or_none()
    if category is None:
      # abort is category is none
      abort(404)
    # paginate questions, and store the current page questions in a list
    page = request.args.get('page', 1, type=int)
    results = Question.query.filter(Question.category == category.id).order_by(Question.id).paginate(page, QUESTIONS_PER_PAGE, True)

    total_questions = results.total
    current_questions = [question.format() for question in results.items]

    return jsonify(
      {
        'success':True,
        'questions':current_questions,
        'total_questions': total_questions,
        'current_category': category.type
      }
    ), 200


  '''
  Endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 
  '''
  @app.route('/quizzes')
  def play_quiz():
    '''take a quiz in the trivia game'''
    try:
      request_body = rquest.body.json()
      if request_body:
        # must use valid json
        abort(400)
      if 'previous_questions' not in request_body \
              or 'quiz_category' not in request_body \
              or 'id' not in request_body['quiz_category']:
              # response must have all of these
          raise TypeError
      
      previous_questions = request_body['previous_questions']
      category_id = request_body['quiz_category']['id']
      # find questions that have not been seen already
      questions_query = Question.query.with_entities(Question.id) \
        .filter(Question.id.notin(previous_questions))
      # as long as category is valid 
      if category_id != 0:
        questions = questions_query.filter(Question.category == str(category_id))
      
      questions = questions.order_by(Quesiton.id).all()
      question_ids = [q.id for q in questions_query]
      # what to return if there are no questions
      if len(question_ids) == 0:
        return jsonify(
          {
            'question':None
          }
        ), 200
      # randomly pick a new question
      random_question = random.choice(question_ids)
      next_question = Question.query.get(random_question_id).format()
      # return next question
      return jsonify(
        {
          'question': next_question
        }, 200
      )
 
    except TypeError:
      abort(400)

    except:
      aabort(500)



  '''
  Error handlers for all expected errors 
  '''
  @app.errorhandler(400)
  @app.errorhandler(404)
  @app.errorhandler(405)
  @app.errorhandler(422)
  @app.errorhandler(500)
  def error_handler(error):
      return jsonify({
          'success': False,
          'error': error.code,
          'message': error.description
      }), error.code
  
  return app

    