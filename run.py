from app import create_app, db  

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        from app.models import Staff, Student
        db.create_all()  # Create tables
    
    app.run(debug=True)