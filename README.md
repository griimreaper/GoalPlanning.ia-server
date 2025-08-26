# GoalPlanning

[![Python](https://img.shields.io/badge/python-3.13-blue)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-5.2.5-green)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

## Descripción

GoalPlanning es una aplicación backend desarrollada en Django que permite a los usuarios gestionar metas y objetivos personales o profesionales. Los usuarios pueden crear metas, agregar objetivos, extenderlos, actualizarlos y hacer seguimiento de su progreso de manera organizada y segura.

## Funcionalidades principales

- Crear, extender y actualizar metas y objetivos.  
- Marcar objetivos como pendientes, completados o cancelados.  
- Añadir comentarios y enlaces de apoyo (por ejemplo, YouTube).  
- Flujo guiado para la actualización de objetivos.  
- Autenticación y permisos mediante tokens.  
- Compatible con PostgreSQL en producción y SQLite en desarrollo.  

## Tecnologías

- **Backend:** Django 5.2.5, Django REST Framework  
- **Base de datos:** PostgreSQL (producción) / SQLite (desarrollo)  
- **Autenticación:** Token Authentication  
- **Otros:** CORS, variables de entorno (`DATABASE_URL`)  

## Instalación (Desarrollo)

1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/goalplanning.git
cd goalplanning
