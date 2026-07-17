1. Introducción
PetConnect es un sistema de gestión integral para mascotas desarrollado en Python con conexión a base de datos MySQL. La aplicación permite administrar usuarios, mascotas, productos y proveedores de servicios mediante operaciones CRUD (Crear, Consultar, Actualizar y Eliminar).
El proyecto sigue una arquitectura por capas utilizando el patrón DAO (Data Access Object) para separar la lógica de acceso a datos de la lógica de presentación, cumpliendo con los estándares de codificación y buenas prácticas de ingeniería de software.
2. Tecnologías Utilizadas
Tecnología	Versión	Propósito
Python	3.14.x	Lenguaje de programación principal
MySQL Server	8.x / 9.x	Sistema gestor de base de datos relacional
mysql-connector-python	9.7.0	Driver de conexión Python-MySQL (DB-API 2.0)
MySQL Workbench	8.x	Herramienta visual de administración de BD
Visual Studio Code	Actual	Entorno de desarrollo integrado (IDE)
 
3. Dependencias y Librerías
3.1 mysql-connector-python (Driver de Conexión)
Es la librería oficial de Oracle para conectar aplicaciones Python con bases de datos MySQL. Cumple con la especificación DB-API 2.0 (PEP 249), que es el estándar de Python equivalente a JDBC en Java.
Instalación:
pip install mysql-connector-python

Comparación con JDBC (Java):
Concepto	JDBC (Java)	mysql-connector (Python)
Conexión	DriverManager.getConnection()	mysql.connector.connect()
Consulta preparada	PreparedStatement	cursor.execute(sql, params)
Resultado	ResultSet	cursor.fetchall() / fetchone()
Cerrar conexión	connection.close()	conexion.close()
Transacciones	commit() / rollback()	commit() / rollback()
Parámetros	setString(1, valor)	Tupla: (valor1, valor2)

3.2 Librerías Estándar de Python
Librería	Módulo	Uso en el Proyecto
hashlib	hashlib.sha256()	Hash SHA-256 para contraseñas de usuarios
sys	sys.path, sys.exit()	Configuración de rutas y salida del programa
os	os.path.dirname()	Obtener ruta absoluta del proyecto
 
4. Arquitectura del Proyecto
4.1 Patrón de Diseño: Arquitectura por Capas
El proyecto implementa una arquitectura de tres capas que separa responsabilidades:
Capa	Paquete	Responsabilidad	Archivos
Vista (Presentación)	vista/	Interfaz de consola, menús interactivos, entrada/salida de datos	menu_principal.py, menu_usuarios.py, menu_mascotas.py, menu_productos.py, menu_proveedores.py
DAO (Acceso a Datos)	dao/	Operaciones CRUD, consultas SQL parametrizadas, mapeo de resultados	usuario_dao.py, mascota_dao.py, producto_dao.py, proveedor_dao.py
Modelo (Entidades)	modelo/	Clases que representan las tablas de la BD	usuario.py, mascota.py, producto.py, proveedor_servicio.py
Conexión	conexion/	Gestión de conexión a MySQL (Singleton)	conexion_bd.py
Configuración	config/	Parámetros de conexión a la BD	db_config.py

4.2 Estructura de Directorios
petconnect/
├── main.py                    # Punto de entrada
├── requirements.txt           # Dependencias
├── config/
│   ├── __init__.py
│   └── db_config.py           # Configuración MySQL
├── conexion/
│   ├── __init__.py
│   └── conexion_bd.py         # Clase ConexionBD (Singleton)
├── modelo/
│   ├── __init__.py
│   ├── usuario.py             # Entidad Usuario
│   ├── mascota.py             # Entidad Mascota
│   ├── producto.py            # Entidad Producto
│   └── proveedor_servicio.py  # Entidad ProveedorServicio
├── dao/
│   ├── __init__.py
│   ├── usuario_dao.py         # CRUD Usuarios
│   ├── mascota_dao.py         # CRUD Mascotas
│   ├── producto_dao.py        # CRUD Productos
│   └── proveedor_dao.py       # CRUD Proveedores
└── vista/
    ├── __init__.py
    ├── menu_principal.py      # Menú principal
    ├── menu_usuarios.py       # Submenú usuarios
    ├── menu_mascotas.py       # Submenú mascotas
    ├── menu_productos.py      # Submenú productos
    └── menu_proveedores.py    # Submenú proveedores
 
5. Módulo de Conexión a Base de Datos
5.1 Configuración (db_config.py)
El archivo db_config.py contiene un diccionario con los parámetros de conexión a MySQL:
DB_CONFIG = {
    "host": "localhost",
    "port": 3310,
    "database": "petconnect",
    "user": "root",
    "password": "",
    "charset": "utf8mb4",
    "collation": "utf8mb4_unicode_ci",
    "autocommit": False
}

Parámetro	Valor	Descripción
host	localhost	Servidor donde se ejecuta MySQL
port	3310	Puerto TCP donde escucha MySQL
database	petconnect	Nombre de la base de datos
user	root	Usuario de MySQL
password	(vacío)	Contraseña del usuario
charset	utf8mb4	Codificación de caracteres (soporta emojis)
autocommit	False	Las transacciones requieren commit() explícito

5.2 Clase ConexionBD (conexion_bd.py)
Implementa el patrón Singleton, garantizando que toda la aplicación use una única instancia de conexión a la base de datos. Equivale a la clase DriverManager de JDBC en Java.
Métodos disponibles:
Método	Descripción
obtener_conexion()	Establece y retorna la conexión activa a MySQL. Si no existe o está desconectada, crea una nueva.
cerrar_conexion()	Cierra la conexión activa y libera los recursos.
commit()	Confirma la transacción actual, haciendo permanentes los cambios en la BD.
rollback()	Revierte la transacción actual, deshaciendo los cambios no confirmados.

5.3 Flujo de Conexión
El flujo de conexión sigue estos pasos:
1.	La aplicación inicia en main.py y crea una instancia de ConexionBD.
2.	ConexionBD lee los parámetros de DB_CONFIG (host, puerto, usuario, contraseña).
3.	Se llama a mysql.connector.connect() con esos parámetros para establecer la conexión.
4.	Los DAOs solicitan la conexión mediante obtener_conexion() para ejecutar consultas SQL.
5.	Tras cada operación de escritura, se llama a commit() para confirmar o rollback() si hay error.
6.	Al salir de la aplicación, se llama a cerrar_conexion() para liberar recursos.
 
6. Capa Modelo (Entidades)
Las clases del modelo representan las tablas de la base de datos. Cada atributo corresponde a una columna de la tabla. Incluyen métodos __str__ para representación legible y __repr__ para depuración.
6.1 Clase Usuario
Atributo	Tipo	Descripción
id_usuario	int	Clave primaria autoincremental
nombres	str	Nombres del usuario
apellidos	str	Apellidos del usuario
correo	str	Correo electrónico (único)
telefono	str	Número de teléfono
password_hash	str	Hash SHA-256 de la contraseña
estado	str	activo / inactivo / bloqueado
verificado	bool	Si el correo fue verificado

6.2 Clase Mascota
Atributo	Tipo	Descripción
id_mascota	int	Clave primaria autoincremental
id_usuario	int	FK - Dueño de la mascota
nombre	str	Nombre de la mascota
especie	str	Especie (perro, gato, ave, etc.)
raza	str	Raza de la mascota
sexo	str	macho / hembra / no_definido
peso	float	Peso en kilogramos
estado	str	activa / perdida / adoptada / fallecida

6.3 Clase Producto
Atributo	Tipo	Descripción
id_producto	int	Clave primaria autoincremental
id_categoria_producto	int	FK - Categoría del producto
nombre	str	Nombre del producto
precio	float	Precio en pesos colombianos
stock	int	Unidades disponibles
activo	bool	Si el producto está disponible
 
7. Capa DAO (Operaciones CRUD)
El patrón DAO (Data Access Object) encapsula toda la lógica de acceso a la base de datos. Cada DAO utiliza consultas SQL parametrizadas con marcadores %s para prevenir inyección SQL, equivalente a PreparedStatement en JDBC.
7.1 Operaciones por DAO
DAO	Insertar	Consultar	Buscar	Actualizar	Eliminar
UsuarioDAO	insertar()	consultar_todos() consultar_por_id()	consultar_por_correo() buscar_por_nombre()	actualizar()	eliminar()
MascotaDAO	insertar()	consultar_todos() consultar_por_id()	consultar_por_usuario() buscar_por_nombre()	actualizar()	eliminar()
ProductoDAO	insertar()	consultar_todos() consultar_por_id()	consultar_por_categoria() buscar_por_nombre()	actualizar()	eliminar()
ProveedorDAO	insertar()	consultar_todos() consultar_por_id()	consultar_por_ciudad() buscar_por_nombre()	actualizar()	eliminar()

7.2 Ejemplo de Consulta SQL Parametrizada
Todas las consultas usan parámetros %s en lugar de concatenar valores directamente, previniendo ataques de inyección SQL:
# Consulta parametrizada (segura)
_INSERTAR = """
    INSERT INTO usuarios (nombres, apellidos, correo, telefono, password_hash)
    VALUES (%s, %s, %s, %s, %s)
"""

# Ejecución con tupla de valores
cursor.execute(self._INSERTAR, (usuario.nombres, usuario.apellidos,
               usuario.correo, usuario.telefono, usuario.password_hash))
self._conexion_bd.commit()  # Confirmar transacción
 
8. Capa Vista (Interfaz de Consola)
La capa de presentación implementa menús interactivos de consola. Cada módulo tiene su propio submenú con las opciones CRUD.
8.1 Menú Principal
=========================================================
        Sistema de Gestion - PetConnect v1.0
=========================================================
  1. Gestion de Usuarios
  2. Gestion de Mascotas
  3. Gestion de Productos (Tienda)
  4. Gestion de Proveedores de Servicio
  0. Salir del sistema
---------------------------------------------------------
  Seleccione un modulo: _

8.2 Submenú de cada módulo
Cada submenú ofrece 7 opciones estándar:
Opción	Acción	Operación SQL
1	Registrar	INSERT INTO tabla (...) VALUES (%s, ...)
2	Consultar todos	SELECT * FROM tabla ORDER BY id
3	Buscar por ID	SELECT * FROM tabla WHERE id = %s
4	Buscar específico	SELECT * FROM tabla WHERE campo = %s
5	Buscar por nombre	SELECT * FROM tabla WHERE nombre LIKE %s
6	Actualizar	UPDATE tabla SET ... WHERE id = %s
7	Eliminar	DELETE FROM tabla WHERE id = %s
 
9. Estándares de Codificación
El proyecto sigue las convenciones de Python (PEP 8) adaptadas al contexto del desarrollo:
Elemento	Convención	Ejemplos
Variables	snake_case	id_usuario, fecha_creacion, password_hash
Métodos	snake_case con verbos	insertar(), consultar_por_id(), buscar_por_nombre()
Clases	PascalCase	Usuario, MascotaDAO, ConexionBD, MenuPrincipal
Paquetes	snake_case minúsculas	config, conexion, modelo, dao, vista
Constantes	UPPER_SNAKE_CASE	DB_CONFIG, _INSERTAR, _CONSULTAR_TODOS
Métodos privados	_prefijo_guion_bajo	_mapear_usuario(), _registrar_mascota()
 
10. Base de Datos PetConnect
10.1 Información General
Propiedad	Valor
Nombre	petconnect
Motor	MySQL (InnoDB)
Charset	utf8mb4 / utf8mb4_unicode_ci
Total de tablas	32
Archivo SQL	PetConnect.sql

10.2 Módulos de la Base de Datos
Módulo	Tablas	Descripción
Seguridad	usuarios, roles, usuarios_roles, direcciones, metodos_pago, planes, suscripciones	Gestión de usuarios, autenticación, roles y suscripciones
Mascotas	mascotas, carnets_vacunacion, vacunas, aplicaciones_vacuna, historial_salud, citas, recordatorios	Registro de mascotas, salud, vacunas y citas
Servicios	categorias_servicio, proveedores_servicio, servicios, resenas_servicio	Directorio de proveedores y servicios
Comunidad	publicaciones_comunidad, comentarios_publicacion, reportes_publicacion	Red social de la plataforma
Adopciones	adopciones	Publicación de mascotas en adopción
Tienda	categorias_producto, productos, carritos, carrito_detalle, pedidos, pedido_detalle, pagos	Marketplace de productos para mascotas
GPS	gps_dispositivos, gps_ubicaciones	Rastreo de mascotas por GPS
Notificaciones	notificaciones	Sistema de alertas y notificaciones
 
11. Guía de Ejecución
11.1 Prerrequisitos
•	Python 3.10 o superior instalado
•	MySQL Server ejecutándose en el puerto configurado (3310)
•	Base de datos petconnect creada (ejecutar PetConnect.sql)
•	Librería mysql-connector-python instalada
11.2 Pasos de Instalación
Paso 1: Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate

Paso 2: Instalar dependencias
pip install mysql-connector-python

Paso 3: Crear la base de datos en MySQL
mysql -u root -p < PetConnect.sql

Paso 4: Configurar conexión en config/db_config.py
Modificar host, port, user y password según su entorno.
Paso 5: Ejecutar la aplicación
.venv\Scripts\python.exe petconnect\main.py
