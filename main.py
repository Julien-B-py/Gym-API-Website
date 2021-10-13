import os
import random

from flask import Flask, jsonify, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, FileField, SubmitField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename, redirect


API_KEY = os.environ.get('API_KEY')
SECRET_KEY = os.environ.get('SECRET_KEY')
UPLOAD_FOLDER = r'static\uploads'

# Create a Flask instance
app = Flask(__name__)

# Specify the database URI that should be used for the connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gyms.db'
# Disable warnings
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Disable json alphabetical sorting
app.config['JSON_SORT_KEYS'] = False
#
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)

bootstrap = Bootstrap(app)


# Define table name and every column
class Gym(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    monthly_sub_price = db.Column(db.String(250), nullable=False)
    opening_time = db.Column(db.String(250), nullable=True)
    closing_time = db.Column(db.String(250), nullable=True)
    review = db.Column(db.String(250), nullable=True)
    website_url = db.Column(db.String(500), nullable=True)
    image_file = db.Column(db.String(500), nullable=True)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


# Force tables creation and database update
# db.create_all()
# db.session.commit()


class AddGymForm(FlaskForm):
    """A WTForm for configuring gym information"""
    gym_name = StringField('Name', validators=[DataRequired()])
    gym_location = StringField('Location', validators=[DataRequired()])
    monthly_sub_price = StringField('Monthly subscription price')
    opening_time = StringField('Opening time', validators=[DataRequired()])
    closing_time = StringField('Closing time', validators=[DataRequired()])
    review = StringField('Review (0-5)', validators=[DataRequired()])
    website_url = StringField('Website URL')
    image_file = FileField('Image (optional)')
    submit = SubmitField("Add gym")


# Home page
@app.route("/")
def home():
    return render_template("index.html")


# Add
@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddGymForm()

    if form.validate_on_submit():

        image_file = form.image_file.data
        filename = secure_filename(image_file.filename)

        if filename:
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Null
        if not filename:
            filename = None

        new_gym = Gym(
            name=form.gym_name.data,
            location=form.gym_location.data,
            monthly_sub_price=form.monthly_sub_price.data,
            opening_time=form.opening_time.data,
            closing_time=form.closing_time.data,
            review=form.review.data,
            website_url=form.website_url.data,
            image_file=filename,
        )
        db.session.add(new_gym)
        db.session.commit()
        return redirect(url_for("gyms"))

    return render_template("add.html", form=form)


@app.route('/gyms')
def gyms():
    gyms = db.session.query(Gym).all()
    return render_template('gyms.html', gyms=gyms)


# Get a random gym from database
@app.route("/api/gym/random")
def get_random_gym():
    # Read all records from database
    gyms = db.session.query(Gym).all()
    # Pick one randomly from the list
    random_gym = random.choice(gyms)
    # Display data in JSON format
    return jsonify(gym=random_gym.to_dict())


# List all known gyms
@app.route("/api/gym/all")
def get_all_gyms():
    gyms = db.session.query(Gym).all()
    # Turn data into list of dicts and then display it in JSON format
    return jsonify(gyms=[gym.to_dict() for gym in gyms])


# Search for gym
@app.route("/api/gym/search")
def get_gym_at_location():
    # Get the loc value passed by the user in the request
    # Titlecase the string value to avoid portential typo issues
    query_location = request.args.get("loc").title()
    # Read records filtered by user requested location and get the first match
    gym = db.session.query(Gym).filter_by(location=query_location).first()
    # If no matching result return an error message
    if not gym:
        return jsonify(error={"Not Found": "Sorry, no gym at that location."}), 404
    return jsonify(gym=gym.to_dict())


# Add a new gym to database
# Handle POST requests
@app.route("/api/gym/add", methods=["POST"])
def post_new_gym():
    new_gym = Gym(
        name=request.form.get("name"),
        location=request.form.get("loc"),
        monthly_sub_price=request.form.get("price"),
        opening_time=request.form.get("opening"),
        closing_time=request.form.get("closing"),
        review=request.form.get("review"),
        website_url=request.form.get("website"))
    db.session.add(new_gym)
    db.session.commit()
    return jsonify(response={"success": "Successfully added the gym to the database."})


# Update specified gym price information
# Handle PATCH requests (partial modification)
@app.route("/api/gym/update-price/<int:gym_id>", methods=["PATCH"])
def patch_new_price(gym_id):
    new_price = request.args.get("new_price")
    gym = db.session.query(Gym).get(gym_id)
    if not gym:
        return jsonify(error={"Not Found": "Sorry no gym with that id was found in the database."}), 404

    gym.coffee_price = new_price
    db.session.commit()
    return jsonify(response={"success": "Successfully updated the monthly subscription price."}), 200


# Delete all data related to the specified gym
# Handle DELETE requests
@app.route("/api/gym/delete/<int:gym_id>", methods=["DELETE"])
def delete_gym(gym_id):
    # Get the api-key value passed by the user in the request
    api_key = request.args.get("api-key")
    # If not authorized API key:
    if api_key != API_KEY:
        return jsonify(error={"Forbidden": "Access denied. Make sure you are using the correct api_key."}), 403
    # Read a particular record by primary key
    gym = db.session.query(Gym).get(gym_id)
    # If no matching record
    if not gym:
        return jsonify(error={"Not Found": "Sorry no gym with that id was found in the database."}), 404
    # Delete record from database and save if it exists
    db.session.delete(gym)
    db.session.commit()
    return jsonify(response={"success": "Successfully deleted the gym from the database."}), 200


if __name__ == '__main__':
    app.run(debug=True)
