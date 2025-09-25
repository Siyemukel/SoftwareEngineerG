from app import create_app,socketio
from app.extensions import db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    #app.run(debug=True)

socketio.run(app, host="0.0.0.0", port=5000, debug=True)