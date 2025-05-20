from importlib import metadata

from .main import PGrafCypher

version = metadata.version('pgraf_cypher')

__all__ = ['PGrafCypher', 'version']
