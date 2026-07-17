"""Entidad Mascota - Representa la tabla 'mascotas' de la base de datos."""


class Mascota:
    """Modelo de datos para una mascota registrada en PetConnect."""

    def __init__(self, id_mascota=None, id_usuario=None, nombre="",
                especie="", raza="", sexo="no_definido",
                fecha_nacimiento=None, edad_aprox=None, color="",
                peso=None, foto=None, observaciones="",
                estado="activa", fecha_registro=None):
        self.id_mascota = id_mascota
        self.id_usuario = id_usuario
        self.nombre = nombre
        self.especie = especie
        self.raza = raza
        self.sexo = sexo
        self.fecha_nacimiento = fecha_nacimiento
        self.edad_aprox = edad_aprox
        self.color = color
        self.peso = peso
        self.foto = foto
        self.observaciones = observaciones
        self.estado = estado
        self.fecha_registro = fecha_registro

    def __str__(self):
        peso_txt = f"{self.peso} kg" if self.peso else "N/A"
        return (f"ID: {self.id_mascota} | {self.nombre} | {self.especie} - {self.raza} "
                f"| Sexo: {self.sexo} | Peso: {peso_txt} | [{self.estado.upper()}]")

    def __repr__(self):
        return f"Mascota(id={self.id_mascota}, nombre='{self.nombre}')"
