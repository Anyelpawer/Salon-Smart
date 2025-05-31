# ✅ app.py con sistema de login y roles
# Comentado paso a paso para que sepas qué se agregó y qué se modificó

from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, Cliente, Producto, Factura, DetalleFactura, MovimientoProducto, Usuario  # ✅ AÑADIDO: modelo Usuario
from datetime import datetime
import pytz
import re
import os

app = Flask(__name__, static_folder='static')
app.secret_key = 'clave_secreta'

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///salon_smart.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

zona_nicaragua = pytz.timezone('America/Managua')

# ✅ NUEVA RUTA: Registro de usuarios
@app.route('/registrar_usuario', methods=['GET', 'POST'])
def registrar_usuario():
    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        usuario = request.form['usuario'].strip().lower()
        contraseña = request.form['contraseña'].strip()

        if not nombre or not usuario or not contraseña:
            flash('Todos los campos son obligatorios.')
            return redirect(url_for('registrar_usuario'))

        # Validar que no exista el usuario
        existente = Usuario.query.filter_by(usuario=usuario).first()
        if existente:
            flash('El usuario ya existe.')
            return redirect(url_for('registrar_usuario'))

        nuevo_usuario = Usuario(nombre=nombre, usuario=usuario, contraseña=contraseña)
        db.session.add(nuevo_usuario)
        db.session.commit()
        flash('Usuario registrado correctamente.')
        return redirect(url_for('login'))

    return render_template('registrar_usuario.html')


# ✅ NUEVA RUTA: Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario'].strip().lower()
        contraseña = request.form['contraseña'].strip()

        user = Usuario.query.filter_by(usuario=usuario, contraseña=contraseña).first()
        if user:
            session['usuario'] = user.usuario
            session['nombre'] = user.nombre

            if user.usuario == 'raquel':
                return redirect(url_for('dashboard_raquel'))
            else:
                return redirect(url_for('dashboard_usuario'))
        else:
            flash('Usuario o contraseña incorrectos.')
            return redirect(url_for('login'))

    return render_template('login.html')



# ✅ NUEVA RUTA: Dashboard para Raquel
@app.route('/dashboard_raquel')
def dashboard_raquel():
    if 'usuario' not in session or session['usuario'] != 'raquel':
        return redirect(url_for('login'))
    return render_template('dashboard_raquel.html', nombre=session['nombre'])

# ✅ NUEVA RUTA: Dashboard para otros usuarios
@app.route('/dashboard_usuario')
def dashboard_usuario():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard_usuario.html', nombre=session['nombre'])


# ✅ RUTA INICIO: Redirecciona según sesión
@app.route('/')
def index():
    if 'usuario' in session:
        if session['usuario'] == 'raquel':
            return redirect(url_for('dashboard_raquel'))
        else:
            return redirect(url_for('dashboard_usuario'))
    return render_template('index.html')  # PÚBLICA

# ✅ RUTA LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- TU CÓDIGO ORIGINAL ---

# MODULO REGISTRO DE CLIENTES
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        correo = request.form['correo'].strip()
        telefono = request.form['telefono'].strip()

        if not nombre or not correo or not telefono:
            flash('Todos los campos son obligatorios.')
            return redirect(url_for('registro'))

        if not nombre.isalpha():
            flash('El nombre solo puede contener letras.')
            return redirect(url_for('registro'))

        if not telefono.isdigit() or len(telefono) != 8:
            flash('El número de teléfono debe tener exactamente 8 dígitos.')
            return redirect(url_for('registro'))

        patron_correo = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(patron_correo, correo):
            flash('Ingrese un correo electrónico válido.')
            return redirect(url_for('registro'))

        fecha_ingreso = datetime.now(zona_nicaragua)

        nuevo_cliente = Cliente(
            nombre=nombre,
            correo=correo,
            telefono=telefono,
            fecha_ingreso=fecha_ingreso
        )
        db.session.add(nuevo_cliente)
        db.session.commit()
        
        flash('Cliente registrado correctamente.')
        return redirect(url_for('registro'))
    
    return render_template('registro.html')

@app.route('/clientes', methods=['GET'])
def clientes_registrados():
    busqueda = request.args.get('busqueda', '').strip()

    if busqueda:
        clientes = Cliente.query.filter(
            (Cliente.nombre.ilike(f"%{busqueda}%")) |
            (Cliente.telefono.ilike(f"%{busqueda}%"))
        ).all()
    else:
        clientes = Cliente.query.all()

    return render_template('registrado.html', clientes=clientes)

@app.route('/inventario', methods=['GET', 'POST'])
def inventario():
    if request.method == 'POST':
        if 'agregar_producto' in request.form:
            nombre = request.form['nombre']
            descripcion = request.form['descripcion']
            precio = float(request.form['precio'])
            stock = int(request.form['stock'])
            moneda = request.form['moneda']

            nuevo_producto = Producto(
                nombre=nombre,
                descripcion=descripcion,
                precio=precio,
                stock=stock,
                moneda=moneda
            )
            db.session.add(nuevo_producto)
            db.session.commit()
            return redirect(url_for('inventario'))

    nombre_buscado = request.args.get('buscar', '').strip()
    if nombre_buscado:
        productos = Producto.query.filter(Producto.nombre.ilike(f"%{nombre_buscado}%")).all()
    else:
        productos = Producto.query.all()

    lista_productos = []
    for producto in productos:
        alerta = ''
        if producto.stock < producto.alerta_stock:
            alerta = '⚠️ Stock Bajo'

        lista_productos.append({
            'id': producto.id,
            'nombre': producto.nombre,
            'descripcion': producto.descripcion,
            'precio': producto.precio,
            'moneda': producto.moneda,
            'stock': producto.stock,
            'alerta': alerta
        })

    return render_template('inventario.html', productos=lista_productos, nombre_buscado=nombre_buscado)

@app.route('/facturacion', methods=['GET', 'POST'])
def facturacion():
    productos = Producto.query.all()
    clientes = Cliente.query.all()

    if request.method == 'POST':
        cliente_id = request.form['cliente_id']
        producto_id = request.form['producto_id']
        cantidad = int(request.form['cantidad'])

        producto = Producto.query.get(producto_id)

        if producto and producto.stock >= cantidad:
            total_sin_impuesto = producto.precio * cantidad
            impuesto = total_sin_impuesto * 0.15
            total = total_sin_impuesto + impuesto

            nueva_factura = Factura(
                cliente_id=cliente_id,
                fecha=datetime.now(zona_nicaragua),
                total=total,
                impuesto=impuesto
            )
            db.session.add(nueva_factura)
            db.session.commit()

            detalle = DetalleFactura(
                factura_id=nueva_factura.id,
                producto_id=producto.id,
                cantidad=cantidad,
                precio_unitario=producto.precio
            )
            db.session.add(detalle)

            producto.stock -= cantidad
            db.session.commit()

            return redirect(url_for('recibo', factura_id=nueva_factura.id))
        else:
            return '<h1 style="color:red;">No hay suficiente stock para completar la venta.</h1>'

    lista_productos = ''.join([f'<option value="{p.id}">{p.nombre} - ${p.precio}</option>' for p in productos])
    lista_clientes = ''.join([f'<option value="{c.id}">{c.nombre}</option>' for c in clientes])

    return render_template('facturacion.html', lista_productos=lista_productos, lista_clientes=lista_clientes)

@app.route('/recibo/<int:factura_id>')
def recibo(factura_id):
    factura = Factura.query.get_or_404(factura_id)
    cliente = Cliente.query.get(factura.cliente_id)
    detalles = DetalleFactura.query.filter_by(factura_id=factura_id).all()
    productos = {p.id: p for p in Producto.query.all()}
    return render_template('recibo.html', factura=factura, cliente=cliente, detalles=detalles, productos=productos)

@app.route('/reportes', methods=['GET'])
def reportes():
    busqueda_id = request.args.get('busqueda_id', type=int)

    if busqueda_id:
        facturas = Factura.query.filter_by(id=busqueda_id).all()
    else:
        facturas = Factura.query.order_by(Factura.fecha.desc()).all()

    return render_template('reportes.html', facturas=facturas)

@app.route('/detalle_factura/<int:factura_id>')
def detalle_factura(factura_id):
    factura = Factura.query.get_or_404(factura_id)
    detalles = DetalleFactura.query.filter_by(factura_id=factura.id).all()
    return render_template('detalle_factura.html', factura=factura, detalles=detalles)


@app.route('/buscar_producto', methods=['GET'])
def buscar_producto():
    nombre_buscado = request.args.get('nombre', '').strip()
    
    if nombre_buscado:
        productos = Producto.query.filter(Producto.nombre.ilike(f"%{nombre_buscado}%")).all()
    else:
        productos = Producto.query.all()
    
    return render_template('productos_registrados.html', productos=productos, nombre_buscado=nombre_buscado)

@app.route('/aumentar_stock/<int:producto_id>')
def aumentar_stock(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    producto.stock += 1

    movimiento = MovimientoProducto(
        producto_id=producto.id,
        tipo='entrada',
        cantidad=1,
        fecha=datetime.now(zona_nicaragua)
    )
    db.session.add(movimiento)
    db.session.commit()
    
    flash(f'Se aumentó el stock de {producto.nombre}.')
    return redirect(url_for('inventario'))

@app.route('/disminuir_stock/<int:producto_id>')
def disminuir_stock(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    if producto.stock > 0:
        producto.stock -= 1

        movimiento = MovimientoProducto(
            producto_id=producto.id,
            tipo='salida',
            cantidad=1,
            fecha=datetime.now(zona_nicaragua)
        )
        db.session.add(movimiento)
        db.session.commit()

        flash(f'Se disminuyó el stock de {producto.nombre}.')
    else:
        flash('No se puede reducir más el stock. {producto.nombre} ya está en cero.')

    return redirect(url_for('inventario'))

@app.route('/eliminar_producto/<int:producto_id>', methods=['POST'])
def eliminar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)

    try:
        db.session.delete(producto)
        db.session.commit()
        flash(f'Producto "{producto.nombre}" eliminado correctamente.')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el producto: {str(e)}')

    return redirect(url_for('inventario'))

@app.route('/productos-registrados', methods=['GET', 'POST'])
def productos_registrados():
    if request.method == 'POST':
        producto_id = request.form.get('producto_id')
        accion = request.form.get('accion')

        producto = Producto.query.get(producto_id)
        if producto:
            if accion == 'sumar':
                producto.stock += 1
            elif accion == 'restar' and producto.stock > 0:
                producto.stock -= 1

            db.session.commit()

    productos = Producto.query.all()
    return render_template('productos_registrados.html', productos=productos)
     
@app.route('/editar_cliente/<int:id>', methods=['GET', 'POST'])
def editar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    if request.method == 'POST':
        cliente.nombre = request.form['nombre']
        cliente.correo = request.form['correo']
        cliente.telefono = request.form['telefono']
        try:
            db.session.commit()
            flash('Cliente actualizado con éxito')
            return redirect(url_for('clientes_registrados'))
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar cliente')
            print(e)
    return render_template('editar_cliente.html', cliente=cliente)

@app.route('/borrar_cliente/<int:id>')
def borrar_cliente(id):
    try:
        cliente = Cliente.query.get(id)
        if cliente:
            db.session.delete(cliente)
            db.session.commit()
            return redirect(url_for('clientes_registrados'))
        else:
            return "Cliente no encontrado", 404
    except Exception as e:
        db.session.rollback()
        print(f"Error al borrar cliente: {e}")
        return "Ocurrió un error al intentar borrar el cliente", 500

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))  # Usa el puerto que Render le asigne
    app.run(host="0.0.0.0", port=port)
