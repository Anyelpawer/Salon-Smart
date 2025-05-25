from app import app, db  # Asegúrate de que 'app' sea el nombre de tu archivo principal

# Inicia el contexto de la aplicación
with app.app_context():
    # Borra todas las tablas
    db.drop_all()

    # Crea todas las tablas de nuevo
    db.create_all()

    print("Las tablas han sido recreadas con éxito.")
