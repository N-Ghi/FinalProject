from flask import request, jsonify, current_app as app, render_template, redirect, url_for, flash, Blueprint, session
from app.db_models import db, User, WasteCollection, RecyclingEffort, Locations, WasteType, WasteCollectionSchedule, Notification, Credentials
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message


mail = Mail(app)
api = Blueprint('api', __name__)

def register_routes(app):
    #Route for homepage
    @app.route('/')
    def index():
        return render_template('index.html')
    
    #Route for dashboard
    @app.route('/api/dashboard')
    def dashboard():
        if 'user_id' in session:
         return render_template('dashboard.html')
        else:
            flash('You need to log in first.', 'error')
            return redirect(url_for('login'))
   
    # API Routes for User
    @app.route('/api/users', methods=['POST', 'GET'])
    def create_user():
        if request.method == 'POST':
            if request.is_json:
                data = request.json
                username = data.get('username')
                email = data.get('email')
                password = data.get('password')
                role = data.get('role') 
            else:
                username = request.form.get('username')
                email = request.form.get('email')
                password = request.form.get('password')
                role = request.form.get('role')

            # Check if username exists
            user = User.query.filter_by(username=username).first()
            if user:                       
                if request.is_json:
                    flash('Username already exists.', 'error')
                return redirect(url_for('create_user'))

            # Hash the password
            hashed_password = generate_password_hash(password)

            # Create new user in database
            new_user = User(username=username,  email=email, password=hashed_password, role=role)
            try:
                db.session.add(new_user)
                db.session.commit()
                if request.is_json:
                    flash(f'User created successfully. User ID: {new_user.id}', 'success')
                    flash('Please login to continue', 'info')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                if request.is_json:
                    flash('Failed to create user', 'error')
                return redirect(url_for('create_user'))
        return render_template('index.html')

    @app.route('/api/all-users', methods=['GET', 'POST'])
    def get_all_users():
        users = User.query.all()
        return jsonify([user.__dict__ for user in users]), 200

    @app.route('/api/get-users', methods=['GET', 'POST'])
    def get_user(user_id):
        user = User.query.get(user_id)
        if user:
            return jsonify(user.__dict__), 200
        else:
            return jsonify({'message': 'User not found'}), 404

    
    @app.route('/api/update-user', methods=['PUT'])
    def update_user(user_id):
        data = request.json
        user = User.query.get(user_id)
        if user:
            user.username = data.get('username', user.username)
            user.role = data.get('role', user.role)
            user.email = data.get('email', user.email)
            user.password = data.get('password', user.password)
            
            try:
                db.session.commit()
                return jsonify({'message': 'User updated successfully'}), 200
            except Exception as e:
                db.session.rollback()
                return jsonify({'message': 'Failed to update user', 'error': str(e)}), 500
        else:
            return jsonify({'message': 'User not found'}), 404

    @app.route('/api/delete-user', methods=['DELETE'])
    def delete_user(user_id):
        user = User.query.get(user_id)
        if user:
            try:
                db.session.delete(user)
                db.session.commit()
                return jsonify({'message': 'User deleted successfully'}), 200
            except Exception as e:
                db.session.rollback()
                return jsonify({'message': 'Failed to delete user', 'error': str(e)}), 500
        else:
            return jsonify({'message': 'User not found'}), 404

    @app.route('/api/users/login', methods=['POST', 'GET'])
    def login():
        if request.method == 'POST':    
            if request.is_json:
                data = request.json
                id = data.get('id')
                password = data.get('password')
            else:
                id = request.form.get('id')
                password = request.form.get('password')

           
            try:
                user = Credentials.query.filter_by(id=id).first()

                if user and check_password_hash(user.password, password):
                    session['user_id'] = user.id
                    session['username'] = user.username
                    flash('Login successful!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid email or password.', 'error')

                if not id or not password:
                    flash('ID and password are required.', 'error')
                return redirect(url_for('login'))

            except Exception as e:
                flash(f"An error occurred: {str(e)}", 'error')
                return redirect(url_for('login'))

            finally:
                if db:
                    db.session.close()
        return render_template('index.html')

    @app.route('/api/users/logout', methods=['GET', 'POST'])
    def logout():
        session.pop('user_id', None)
        session.pop('username', None)
        return redirect(url_for('login'))



    # API Routes for Waste Collection

    @app.route('/api/wastecollection', methods=['POST', 'GET'])
    def create_waste_collection():
        data = request.json
        new_collection = WasteCollection(
            user_id=data['user_id'],
            date=data['date'],
            status=data['status'],
            waste_type=data['waste_type'],
            location=data['location']
        )
        
        try:
            db.session.add(new_collection)
            db.session.commit()
            return jsonify({'message': 'Waste collection created successfully'}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': 'Failed to create waste collection', 'error': str(e)}), 500

    @app.route('/api/all-wastecollection', methods=['GET', 'POST'])
    def get_all_collections():
        w_collections = WasteCollection.query.all()
        return jsonify([w_collection.__dict__ for w_collection in w_collections]), 200

    @app.route('/api/id-wastecollection', methods=['GET', 'POST'])
    def get_collection(id):
        w_collection = WasteCollection.query.get(id)
        if w_collection:
            return jsonify(w_collection.__dict__), 200
        else:
            return jsonify({'message': 'Collection not found'}), 404

    @app.route('/api/update-wastecollection', methods=['PUT'])
    def update_collection(id):
        data = request.json
        w_collection = WasteCollection.query.get(id)
        if w_collection:
            w_collection.date = data.get('date', w_collection.date)
            w_collection.status = data.get('status', w_collection.status)
            w_collection.waste_type = data.get('waste_type', w_collection.waste_type)
            w_collection.location = data.get('location', w_collection.location)
            
            try:
                db.session.commit()
                return jsonify({'message': 'Collection updated successfully'}), 200
            except Exception as e:
                db.session.rollback()
                return jsonify({'message': 'Failed to update collection', 'error': str(e)}), 500
        else:
            return jsonify({'message': 'Collection not found'}), 404

    @app.route('/api/delete-wastecollection', methods=['DELETE'])
    def delete_collection(id):
        w_collection = WasteCollection.query.get(id)
        if w_collection:
            try:
                db.session.delete(w_collection)
                db.session.commit()
                return jsonify({'message': 'Collection deleted successfully'}), 200
            except Exception as e:
                db.session.rollback()
                return jsonify({'message': 'Failed to delete collection', 'error': str(e)}), 500
        else:
            return jsonify({'message': 'Collection not found'}), 404
        
    # API Routes for Recycling Effort

    @app.route('/api/create-recyclingeffort', methods=['POST', 'GET'])
    def create_recycling_effort():
        data = request.json
        new_effort = RecyclingEffort(
            user_id=data['user_id'],
            date=data['date'],
            waste_type=data['waste_type']
        )
        
        try:
            db.session.add(new_effort)
            db.session.commit()
            return jsonify({'message': 'Recycling effort created successfully'}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': 'Failed to create recycling effort', 'error': str(e)}), 500

    @app.route('/api/all-recyclingeffort', methods=['GET', 'POST'])
    def get_all_recycling_efforts():
        efforts = RecyclingEffort.query.all()
        return jsonify([effort.__dict__ for effort in efforts]), 200

    @app.route('/api/id-recyclingeffort', methods=['GET', 'POST'])
    def get_recycling_effort(id):
        effort = RecyclingEffort.query.get(id)
        if effort:
            return jsonify(effort.__dict__), 200
        else:
            return jsonify({'message': 'Recycling effort not found'}), 404

    @app.route('/api/update-recyclingeffort', methods=['PUT'])
    def update_recycling_effort(id):
        data = request.json
        effort = RecyclingEffort.query.get(id)
        if effort:
            effort.date = data.get('date', effort.date)
            effort.waste_type = data.get('waste_type', effort.waste_type)

            try:
                db.session.commit()
                return jsonify({'message': 'Recycling effort updated successfully'}), 200
            except Exception as e:
                db.session.rollback()
                return jsonify({'message': 'Failed to update recycling effort', 'error': str(e)}), 500
        else:
            return jsonify({'message': 'Recycling effort not found'}), 404

    @app.route('/api/delete-recyclingeffort', methods=['DELETE'])
    def delete_recycling_effort(id):
        effort = RecyclingEffort.query.get(id)
        if effort:
            try:
                db.session.delete(effort)
                db.session.commit()
                return jsonify({'message': 'Recycling effort deleted successfully'}), 200
            except Exception as e:
                db.session.rollback()
                return jsonify({'message': 'Failed to delete recycling effort', 'error': str(e)}), 500
        else:
            return jsonify({'message': 'Recycling effort not found'}), 404

    # API Routes for Locations

    @app.route('/api/create-locations', methods=['POST', 'GET'])
    def create_location():
        data = request.json
        new_location = Locations(
            locations=data['locations']
        )
        
        try:
            db.session.add(new_location)
            db.session.commit()
            return jsonify({'message': 'Location created successfully'}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': 'Failed to create location', 'error': str(e)}), 500

    @app.route('/api/all-locations', methods=['GET', 'POST'])
    def get_all_locations():
        locations = Locations.query.all()
        return jsonify([location.__dict__ for location in locations]), 200

    @app.route('/api/id-locations', methods=['GET', 'POST'])
    def get_location(id):
        location = Locations.query.get(id)
        if location:
            return jsonify(location.__dict__), 200
        else:
            return jsonify({'message': 'Location not found'}), 404

    @app.route('/api/update-locations', methods=['PUT'])
    def update_location(id):
        data = request.json
        location = Locations.query.get(id)
        if location:
            location.locations = data.get('locations', location.locations)

            try:
                db.session.commit()
                return jsonify({'message': 'Location updated successfully'}), 200
            except Exception as e:
                db.session.rollback()
                return jsonify({'message': 'Failed to update location', 'error': str(e)}), 500
        else:
            return jsonify({'message': 'Location not found'}), 404

    @app.route('/api/delete-locations', methods=['DELETE'])
    def delete_location(id):
        location = Locations.query.get(id)
        if location:
            try:
                db.session.delete(location)
                db.session.commit()
                return jsonify({'message': 'Location deleted successfully'}), 200
            except Exception as e:
                db.session.rollback()
                return jsonify({'message': 'Failed to delete location', 'error': str(e)}), 500
        else:
            return jsonify({'message': 'Location not found'}), 404
        
    #API routes for WasteType
    @app.route('/api/create-wastetype', methods=['POST', 'GET'])
    def create_wastetype():
        data = request.json
        new_wastetype = WasteType(
            name=data['name']
        )
        
        try:
            db.session.add(new_wastetype)
            db.session.commit()
            return jsonify({'message': 'WasteType created successfully'}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': 'Failed to create WasteType', 'error': str(e)}), 500

    @app.route('/api/all-wastetype', methods=['GET', 'POST'])
    def get_all_wastetype():
        wastetypes = WasteType.query.all()
        return jsonify([wastetype.__dict__ for wastetype in wastetypes]), 200

    @app.route('/api/id-wastetype', methods=['GET', 'POST'])
    def get_wastetype(id):
        wastetype = WasteType.query.get(id)
        if wastetype:
            return jsonify(wastetype.__dict__), 200
        else:
            return jsonify({'message': 'WasteType not found'}), 404

    @app.route('/api/update-wastetype', methods=['PUT'])
    def update_wastetype(id):
        data = request.json
        wastetype = WasteType.query.get(id)
        if wastetype:
            wastetype.name = data.get('name', wastetype.name)

            try:
                db.session.commit()
                return jsonify({'message': 'WasteType updated successfully'}), 200
            except Exception as e:
                db.session.rollback()
                return jsonify({'message': 'Failed to update WasteType', 'error': str(e)}), 500
        else:
            return jsonify({'message': 'WasteType not found'}), 404

    @app.route('/api/delete-wastetype', methods=['DELETE'])
    def delete_wastetype(id):
        wastetype = WasteType.query.get(id)
        if wastetype:
            try:
                db.session.delete(wastetype)
                db.session.commit()
                return jsonify({'message': 'WasteType deleted successfully'}), 200
            except Exception as e:
                db.session.rollback()
                return jsonify({'message': 'Failed to delete WasteType', 'error': str(e)}), 500
        else:
            return jsonify({'message': 'WasteType not found'})
   
    #API routes for WasteCollectionSchedule
    @api.route('/api/create-schedule', methods=['GET', 'POST'])
    def schedule_collection():
        if request.method == 'POST':
            user_id = request.form['user_id']
            collection_date = datetime.strptime(request.form['collection_date'], '%Y-%m-%dT%H:%M')
            waste_type = request.form['waste_type']
            new_schedule = WasteCollectionSchedule(user_id=user_id, collection_date=collection_date, waste_type=waste_type, status='scheduled')
            db.session.add(new_schedule)
            db.session.commit()
            send_notification(user_id, 'Collection scheduled successfully!', 'confirmation')
            return redirect(url_for('api.schedule_collection'))
        return render_template('schedule.html')

    @app.route('/api/update_schedule', methods=['GET', 'POST'])
    def update_schedule():
        if request.method == 'POST':
            data = request.get_json() or request.form
            
            schedule_id = data.get('schedule_id')
            collection_date = datetime.strptime(data.get('collection_date'), '%Y-%m-%d')
            waste_type = data.get('waste_type')
            
            # Retrieve the schedule by ID
            schedule = WasteCollectionSchedule.query.get(schedule_id)
            
            # If schedule exists, update it
            if schedule:
                schedule.collection_date = collection_date
                schedule.waste_type = waste_type
                db.session.commit()
                # Assuming you have a function to send notifications
                send_notification(schedule.user_id, 'Collection updated successfully!', 'update')
                return jsonify({'message': 'Schedule updated successfully!'}), 200
            else:
                # If schedule does not exist, return 404
                return jsonify({'message': 'Schedule not found'}), 404

        # Render the update schedule form for GET requests
        return render_template('update_schedule.html')

    #API routes for Notification
    @app.route('/api/notifications', methods=['GET', 'POST'])
    def send_notification(user_id, message, notif_type):
        notification = Notification(user_id=user_id, message=message, type=notif_type)
        db.session.add(notification)
        db.session.commit()

        user = User.query.get(user_id)
        print(f"Notification sent to {user.email}: {message}")

    @app.route('/api/get-notifications', methods=['GET', 'POST'])
    def view_notifications():   
        user_id = request.args.get('user_id')
        notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.date.desc()).all()
        return render_template('notifications.html', notifications=notifications)
if __name__ == '__main__':
    app.run(debug=True)
