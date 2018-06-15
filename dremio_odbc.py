#
#   Dremio Data Source Driver for Redash
#
#   Written by Brian K. Holman (bholman@dezota.com)
#   Based on the Microsoft SQL Server ODBC Driver for Dremio
#
#   This is free and unencumbered software released into the public domain.
#
#   Anyone is free to copy, modify, publish, use, compile, sell, or
#   distribute this software, either in source code form or as a compiled
#   binary, for any purpose, commercial or non-commercial, and by any
#   means.
#
#   In jurisdictions that recognize copyright laws, the author or authors
#   of this software dedicate any and all copyright interest in the
#   software to the public domain. We make this dedication for the benefit
#   of the public at large and to the detriment of our heirs and
#   successors. We intend this dedication to be an overt act of
#   relinquishment in perpetuity of all present and future rights to this
#   software under copyright law.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#   EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#   MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#   IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
#   OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#   ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#   OTHER DEALINGS IN THE SOFTWARE.
#
#   For more information, please refer to <http://unlicense.org/>
 
import json
import logging
import sys
import uuid

from redash.query_runner import *
from redash.utils import JSONEncoder

class DremioJSONEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, uuid.UUID):
            return str(o)
        return super(DremioJSONEncoder, self).default(o)

types_map = {
    1: TYPE_STRING,
    2: TYPE_STRING,
    3: TYPE_INTEGER,
    4: TYPE_DATETIME,
    5: TYPE_FLOAT,
}

logger = logging.getLogger(__name__)

try:
    import pyodbc
    enabled = True
except ImportError:
    enabled = False

class DremioODBC(BaseSQLQueryRunner):
    noop_query = "SELECT 1"

    @classmethod
    def configuration_schema(cls):
        return {
            "type": "object",
            "properties": {
                "user": {
                    "type": "string"
                },
                "password": {
                    "type": "string"
                },
                "server": {
                    "type": "string",
                    "default": "127.0.0.1"
                },
                "port": {
                    "type": "number",
                    "default": 31010
                },
                "charset": {
                    "type": "string",
                    "default": "UTF-8",
                    "title": "Character Set"
                },
                "db": {
                    "type": "string",
                    "title": "Schema Name",
                    "default": ""
                },
                "driver": {
                    "type": "string",
                    "title": "Driver Identifier",
                    "default": "{Dremio ODBC Driver 64-bit}"
                }
            },
            "required": ["server","user","password"],
            "secret": ["password"]
        }

    @classmethod
    def enabled(cls):
        return enabled

    @classmethod
    def name(cls):
        return "Dremio Server (ODBC)"

    @classmethod
    def type(cls):
        return "dremio_odbc"

    @classmethod
    def annotate_query(cls):
        return False

    def __init__(self, configuration):
        super(DremioODBC, self).__init__(configuration)

    def _get_tables(self, schema):
        query = """
        SELECT table_schema, table_name, column_name
        FROM INFORMATION_SCHEMA.COLUMNS WHERE table_schema NOT IN ('INFORMATION_SCHEMA','sys')
        """

        results, error = self.run_query(query, None)

        if error is not None:
            raise Exception("Failed getting schema.")

        results = json.loads(results)

        for row in results['rows']:
            if row['table_schema'] != self.configuration['db']:
                table_name = u'{}.{}'.format(row['table_schema'], row['table_name'])
            else:
                table_name = row['table_name']

            if table_name not in schema:
                schema[table_name] = {'name': table_name, 'columns': []}

            schema[table_name]['columns'].append(row['column_name'])

        return schema.values()

    def run_query(self, query, user):
        connection = None

        try:
            server = self.configuration.get('server', '')
            user = self.configuration.get('user', '')
            password = self.configuration.get('password', '')
            db = self.configuration['db']
            port = self.configuration.get('port', 31010)
            charset = self.configuration.get('charset', 'UTF-8')
            driver = self.configuration.get('driver', '{Dremio ODBC Driver 64-bit}')

            connection_string_fmt = 'DRIVER={};ConnectionType=Direct;HOST={};PORT={};AuthenticationType=Plain;UID={};PWD={};AdvancedProperties=CastAnyToVarchar=true;HandshakeTimeout=5;QueryTimeout=180;TimestampTZDisplayTimezone=utc;NumberOfPrefetchBuffers=5;Catalog=DREMIO;Schema={}'
            connection_string = connection_string_fmt.format(driver,server,port,user,password,db)
            
            pyodbc.autocommit = True
            connection = pyodbc.connect(connection_string, autocommit=True)
            cursor = connection.cursor()
            logger.debug("DremioODBC running query: %s", query)
            cursor.execute(query)
            data = cursor.fetchall()

            if cursor.description is not None:
                columns = self.fetch_columns([(i[0], types_map.get(i[1], None)) for i in cursor.description])
                rows = [dict(zip((c['name'] for c in columns), row)) for row in data]

                data = {'columns': columns, 'rows': rows}
                json_data = json.dumps(data, cls=DremioJSONEncoder)
                error = None
            else:
                error = "No data was returned."
                json_data = None

            cursor.close()
        except pyodbc.Error as e:
            try:
                # Query errors are at `args[1]`
                error = e.args[1]
            except IndexError:
                # Connection errors are `args[0][1]`
                error = e.args[0][1]
            json_data = None
        except KeyboardInterrupt:
            connection.cancel()
            error = "Query cancelled by user."
            json_data = None
        except Exception as e:
            raise sys.exc_info()[1], None, sys.exc_info()[2]
        finally:
            if connection:
                connection.close()

        return json_data, error

register(DremioODBC)
