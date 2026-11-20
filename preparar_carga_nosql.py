"""EP3 · Prepara los JSON para subirlos a Azure Cosmos DB for NoSQL.

Cosmos DB for NoSQL exige que cada documento tenga un campo "id" (los JSON del caso
traen "_id", que es el nombre de MongoDB). Este script SOLO renombra _id -> id y deja
los archivos en data_cosmos_nosql/ (un arreglo JSON por contenedor). No filtra campos:
la selección de atributos (Tabla RICE) la hace después Azure Data Factory.

Uso:  python preparar_carga_nosql.py
"""
import json
import os
import sys

from config import BASE_DIR, DATA_DIR

SALIDA = os.path.join(BASE_DIR, "data_cosmos_nosql")
# archivo de origen -> nombre del contenedor (sin ñ, como en la Tabla RICE)
ARCHIVOS = {"campañas.json": "campanas", "publicaciones.json": "publicaciones",
            "reacciones.json": "reacciones", "comentarios.json": "comentarios",
            "usuarios.json": "usuarios"}


def convertir(docs):
    salida = []
    for d in docs:
        nuevo = {"id": d["_id"]}
        nuevo.update({k: v for k, v in d.items() if k != "_id"})
        salida.append(nuevo)
    ids = [d["id"] for d in salida]
    if len(ids) != len(set(ids)):
        raise ValueError("hay ids repetidos")
    return salida


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(SALIDA, exist_ok=True)
    for archivo, contenedor in ARCHIVOS.items():
        with open(os.path.join(DATA_DIR, archivo), encoding="utf-8") as f:
            docs = convertir(json.load(f))
        ruta = os.path.join(SALIDA, f"{contenedor}.json")
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(docs, f, ensure_ascii=False, indent=1)
        print(f"{contenedor:14} {len(docs)} documentos -> {ruta} ({os.path.getsize(ruta)//1024} KB)")


if __name__ == "__main__":
    main()
