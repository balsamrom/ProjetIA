# Configuration pour SQLite (pas besoin de pymysql)

try:
    import pymysql  # type: ignore
    pymysql.install_as_MySQLdb()
except Exception:
    # PyMySQL non installé, Django pourra toujours démarrer en SQLite
    pass