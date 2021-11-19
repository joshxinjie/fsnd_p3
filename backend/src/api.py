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

db_drop_and_create_all()

def get_drinks(format):
    """
    Retrieve either the drink.short() or drink.long() data representation
    of the drinks.

    Parameters
    ----------
    format: str
      Indicates either the drink.short() or drink.long() data representation
    
    Returns
    -------
    formatted_drinks: 
      The drink.short() or drink.long() data representation of the drinks
    """
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
    """
    Retrieves the title and recipe of the request body

    Parameters
    ----------
    body:
      The request body
    
    Returns
    -------
    name: str
      The name of the drink
    recipe: json str
      The drink's recipe
    """
    name = None
    recipe = None

    if "title" in body:
        name = body["title"]
    
    if "recipe" in body:
        recipe = body["recipe"] or None
        recipe = json.dumps(recipe)

    return name, recipe

# ROUTES
@app.route('/drinks' , methods=['GET'])
def get_short_drinks():
    """
    Endpoint
    GET /drinks
    - a public endpoint
    - contain only the drink.short() data representation
    
    Returns status code 200 and json {"success": True, "drinks": drinks} 
    where drinks is the list of drinks or appropriate status code 
    indicating reason for failure.

    Parameters
    ----------
    None
    
    Returns
    -------
    json object with the keys:
    
    success:
      Whether the request is successful
    drinks:
      The drink.short() data representation of the drinks
    """
    drinks = get_drinks(format="short")
    return jsonify(
        {
            "success": True,
            "drinks": drinks
        }
    )

@app.route('/drinks-detail' , methods=['GET'])
@requires_auth('get:drinks-detail')
def get_long_drinks(jwt):
    """
    Endpoint
    GET /drinks-detail
    - require the 'get:drinks-detail' permission
    - contain the drink.long() data representation
    
    Returns status code 200 and json {"success": True, "drinks": drinks} 
    where drinks is the list of drinks or appropriate status code 
    indicating reason for failure.

    Parameters
    ----------
    jwt:
      JSON Web token
    
    Returns
    -------
    json object with the keys:
    
    success:
      Whether the request is successful
    drinks
      The drink.long() data representation of the drinks
    """
    drinks = get_drinks(format="long")

    return jsonify(
        {
            "success": True,
            "drinks": drinks
        }
    )

@app.route('/drinks' , methods=['POST'])
@requires_auth('post:drinks')
def post_drink(jwt):
    """
    Endpoint
    POST /drinks
    - create a new row in the drinks table
    - require the 'post:drinks' permission
    - contain the drink.long() data representation
    
    Returns status code 200 and json {"success": True, "drinks": drink} 
    where drink an array containing only the newly created drink
    or appropriate status code indicating reason for failure.

    Parameters
    ----------
    jwt:
      JSON Web token
    
    Returns
    -------
    json object with the keys:
    
    success:
      Whether the request is successful
    drink:
      The drink.long() data representation of the new drink
    """
    body = request.get_json()

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

@app.route('/drinks/<int:id>' , methods=['PATCH'])
@requires_auth('patch:drinks')
def patch_drink(jwt, id):
    """
    Endpoint
    PATCH /drinks/<id>
    - where <id> is the existing model id
    - respond with a 404 error if <id> is not found
    - update the corresponding row for <id>
    - require the 'patch:drinks' permission
    - contain the drink.long() data representation
    
    Returns status code 200 and json {"success": True, "drinks": drink} 
    where drink an array containing only the updated drink or 
    appropriate status code indicating reason for failure.

    Parameters
    ----------
    jwt:
      JSON Web token
    id:
      The drink id
    
    Returns
    -------
    json object with the keys
    
    success:
      Whether the request is successful
    drinks:
      The drink.long() data representation of the updated drink
    """
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

@app.route('/drinks/<int:id>' , methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(jwt, id):
    """
    Endpoint
    DELETE /drinks/<id>
    - <id> is the existing model id
    - respond with a 404 error if <id> is not found
    - delete the corresponding row for <id>
    - require the 'delete:drinks' permission
    
    Returns status code 200 and json {"success": True, "delete": id} 
    where id is the id of the deleted record or appropriate status 
    code indicating reason for failure.

    Parameters
    ----------
    jwt:
      JSON Web token
    id:
      The drink id
    
    Returns
    -------
    json object with the keys
    
    success:
      Whether the request is successful
    id:
      ID of the drink deleted
    """
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
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
                    "success": False, 
                    "error": 400,
                    "message": "bad request"
                    }), 400

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

@app.errorhandler(AuthError)
def authentification_failed(AuthError):
    return jsonify({
                    "success": False, 
                    "error": AuthError.status_code,
                    "message":  AuthError.error
                    }), AuthError.status_code