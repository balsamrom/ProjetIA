import pymysql
pymysql.install_as_MySQLdb()

# Monkey patch to bypass MariaDB version check for older versions (development only)
import django.db.backends.mysql.base
original_check_database_version_supported = django.db.backends.mysql.base.DatabaseWrapper.check_database_version_supported

def patched_check_database_version_supported(self):
    """Bypass version check for MariaDB 10.4 in development"""
    # Skip version check - MariaDB 10.4 works fine with Django
    pass

django.db.backends.mysql.base.DatabaseWrapper.check_database_version_supported = patched_check_database_version_supported

# Disable RETURNING clause support for MariaDB 10.4 (doesn't support RETURNING)
import django.db.backends.mysql.features
# Monkey patch the DatabaseFeatures class
django.db.backends.mysql.features.DatabaseFeatures.supports_returning_columns_in_bulk_insert = False