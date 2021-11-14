import os, sys
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
db_drop_and_create_all()

def get_drinks(format):
    drinks = Drink.query.order_by(Drink.id).all()
    if format == "short":
        formatted_drinks = [drink.short() for drink in drinks]
    elif format == "long":
        formatted_drinks = [drink.long() for drink in drinks]
    else:
        abort(400)
    
    if len(formatted_drinks) == 0:
        abort(404)

    return formatted_drinks

def get_name_and_recipe_from_body(body):
    name = None
    recipe = None

    if "title" in body:
        name = body["title"]
    
    if "recipe" in body:
        recipe = body["recipe"] or None
        recipe = json.dumps(recipe)

    return name, recipe

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks' , methods=['GET'])
def get_short_drinks():
    drinks = get_drinks(format="short")
    return jsonify(
        {
            "success": True,
            "drinks": drinks
        }
    )

'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks-detail' , methods=['GET'])
@requires_auth('get:drinks-detail')
def get_long_drinks(jwt):
    drinks = get_drinks(format="long")

    return jsonify(
        {
            "success": True,
            "drinks": drinks
        }
    )

'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks' , methods=['POST'])
@requires_auth('post:drinks')
def post_drink(jwt):
    body = request.get_json()
    # print(body)
    #{'id': -1, 'title': 'Test', 'recipe': [{'name': 'A', 'color': 'red', 'parts': 1}, {'name': 'B', 'color': 'blue', 'parts': 1}, {'name': '', 'color': 'white', 'parts': 1}]}
    # print("""{}""".format(body['recipe']))

    name, recipe = get_name_and_recipe_from_body(body)
    
    if (not name) or (not recipe):
        abort(400)
    
    try:
        new_drink = Drink(title = name, recipe = recipe)
        new_drink.insert()
        return jsonify(
          {
            'success': True,
            'drink': new_drink.long()
          }
        )
    except:
        print(sys.exc_info())
        abort(422)

'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>' , methods=['PATCH'])
@requires_auth('patch:drinks')
def patch_drink(jwt, id):
    body = request.get_json()

    updated_name, updated_recipe = get_name_and_recipe_from_body(body)

    if (updated_name is None) and (updated_recipe is None):
        abort(400)

    try:
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        if updated_name:
            drink.title = updated_name
        if updated_recipe:
            drink.recipe = updated_recipe
        drink.update()
        return jsonify(
            {
                'success': True,
                'drinks': [drink.long()]
            }
        )
    except:
        print(sys.exc_info())
        abort(422)

'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>' , methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(jwt, id):
    if id is None:
        abort(422)
    
    try:
        drink = Drink.query.filter(Drink.id == id).one_or_none()

        if drink is None:
            abort(404)

        drink.delete()

        return jsonify(
            {
                'success': True,
                'delete': id
            }
        )
    except:
        abort(422)

# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''
@app.errorhandler(400)
def bad_request(error):
    return jsonify({
                    "success": False, 
                    "error": 400,
                    "message": "bad request"
                    }), 400

'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''
@app.errorhandler(404)
def ressource_not_found(error):
    return jsonify({
                    "success": False, 
                    "error": 404,
                    "message": "resource not found"
                    }), 404

# @app.errorhandler(401)
# def permission_not_found(error):
#     return jsonify({
#                     "success": False, 
#                     "error": 401,
#                     "message": "permission not found"
#                     }), 401

# @app.errorhandler(403)
# def unauthorized(error):
#     return jsonify({
#                     "success": False, 
#                     "error": 403,
#                     "message": "unauthorized"
#                     }), 403

'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''
@app.errorhandler(AuthError)
def authentification_failed(AuthError):
    # print(AuthError.status_code)
    # print(AuthError.error)
    return jsonify({
                    "success": False, 
                    "error": AuthError.status_code,
                    "message":  AuthError.error
                    }), AuthError.status_code