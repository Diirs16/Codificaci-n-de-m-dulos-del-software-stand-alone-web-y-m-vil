"""
Módulo de conexión a la base de datos MySQL.
Implementa el patrón Singleton para reutilizar la conexión
y métodos equivalentes a JDBC (connect, close, commit, rollback).
"""

import mysql.connector
from mysql.connector import Error
from config.db_config import DB_CONFIG


class ConexionBD:
    """Gestiona la conexión a la base de datos MySQL (equivalente a JDBC DriverManager)."""

    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._conexion = None
        return cls._instancia

    def obtener_conexion(self):
        """Establece y retorna la conexión a MySQL."""
        try:
            if self._conexion is None or not self._conexion.is_connected():
                self._conexion = mysql.connector.connect(**DB_CONFIG)
            return self._conexion
        except Error as e:
            print(f"[ERROR] No se pudo conectar a la base de datos: {e}")
            return None

    def cerrar_conexion(self):
        """Cierra la conexión activa."""
        try:
            if self._conexion and self._conexion.is_connected():
                self._conexion.close()
                self._conexion = None
        except Error as e:
            print(f"[ERROR] Al cerrar la conexión: {e}")

    def commit(self):
        """Confirma la transacción actual."""
        if self._conexion and self._conexion.is_connected():
            self._conexion.commit()

    def rollback(self):
        """Revierte la transacción actual."""
        if self._conexion and self._conexion.is_connected():
            self._conexion.rollback()
