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
  @TODO: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
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

    