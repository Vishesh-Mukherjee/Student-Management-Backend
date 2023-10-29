from sqlite3 import Connection
from logging import Logger
from uuid import uuid4
from constant import DatabaseColumn


class BasicRepository:

    def __init__(self, conn: Connection, table_name: str, logger: Logger):
        self._conn = conn
        self._table_name = table_name
        self._logger = logger
    
    def save(self, data_dict: dict):
        if DatabaseColumn.ID in data_dict.keys() and self.exists_by_attribute({DatabaseColumn.ID: data_dict[DatabaseColumn.ID]}):
            entity_id = data_dict[DatabaseColumn.ID]
            query = self._generate_update_query(data_dict.keys())
            argument = [x for x in data_dict.values() if x != entity_id]
            argument.append(entity_id)
            self._logger.debug(f'Executing update query: [{query}], arguments: {argument}')
        else:
            if DatabaseColumn.ID not in data_dict.keys():
                data_dict[DatabaseColumn.ID] = str(uuid4())
            query = self._generate_save_query(data_dict.keys())
            argument = list(data_dict.values())
            self._logger.debug(f'Executing insert query: [{query}], arguments: {argument}')
        self._conn.execute(query, argument)
        return data_dict
    
    def save_all(self, data_list: list):
        saved_data = []
        for data in data_list:
            saved_data.append(self.save(data))
        return saved_data

    def find_by_attribute(self, pairs: dict, separator: str = DatabaseColumn.AND, wild_card = None):
        query = f"SELECT * FROM {self._table_name} {self._generate_where_clause(pairs.keys(), separator)} {'' if wild_card is None else wild_card}"
        argument = list(pairs.values()) 
        self._logger.debug(f'Executing select query: [{query}], arguments: {argument}')
        data = self._conn.execute(query, argument).fetchone()
        return None if data is None else dict(data)
    
    def exists_by_attribute(self, pairs: dict, separator: str = DatabaseColumn.AND):
        query = f"SELECT count(*) > 0 FROM {self._table_name} {self._generate_where_clause(pairs.keys(), separator)}"
        argument = list(pairs.values())
        self._logger.debug(f'Executing exists query: [{query}], arguments: {argument}')
        entity_exists = self._conn.execute(query, argument).fetchone()[0]
        return True if entity_exists == 1 else False

    def delete_by_attribute(self, pairs: dict, separator: str = DatabaseColumn.AND):
        query = f"DELETE FROM {self._table_name} {self._generate_where_clause(pairs.keys(), separator)}"
        argument = list(pairs.values())
        self._logger.debug(f'Executing delete query: [{query}], arguments: {argument}')
        self._conn.execute(query, argument)

    def find_all_by_attribute(self, pairs: dict, separator: str = DatabaseColumn.AND):
        query = f"SELECT * FROM {self._table_name} {self._generate_where_clause(pairs.keys(), separator)}"
        argument = list(pairs.values())
        self._logger.debug(f'Executing find query: [{query}], arguments: {argument}')
        cursor = self._conn.execute(query, argument)
        return [dict(x) for x in cursor.fetchall()]

    def count_by_attribute(self, pairs: dict = {}, separator: str = DatabaseColumn.AND):
        query = f"SELECT COUNT(*) FROM {self._table_name} {self._generate_where_clause(pairs.keys(), separator)}"
        argument = list(pairs.values())
        self._logger.debug(f'Executing count query: [{query}], arguments: {argument}')
        print(query)
        return self._conn.execute(query, argument).fetchone()[0]
    
    def _generate_where_clause(self, keys: list, separator: str = DatabaseColumn.AND):
        return "" if len(keys) == 0 else f"WHERE {f' {separator} '.join([f'{key} = ?' for key in keys])}"

    def _generate_save_query(self, keys: list):
        return f"INSERT INTO {self._table_name} ({', '.join(keys)}) VALUES ({', '.join('?' for _ in range(len(keys)))})"
    
    def _generate_update_query(self, keys: list):
        return f"UPDATE {self._table_name} SET {', '.join([f'{key} = ?' for key in keys if key != DatabaseColumn.ID])} WHERE {DatabaseColumn.ID} = ?"
    
    
class ClassRepository (BasicRepository):

    def __init__(self, conn: Connection, table_name: str, logger: Logger):
        super().__init__(conn, table_name, logger)

    def findAllAvailableClasses(self):
        cursor = self._conn.execute(f"SELECT * FROM {self._table_name} where {DatabaseColumn.CURRENT_ENROLLMENT} <= {DatabaseColumn.MAX_ENROLLMENT}")
        return [dict(x) for x in cursor.fetchall()]
        

class EnrollmentRepository (BasicRepository):

    def __init__(self, conn: Connection, table_name: str, logger: Logger):
        super().__init__(conn, table_name, logger)

    def waitingListPosition(self, class_id: str, student_id: str):
        sub_query = f"SELECT student_id, ROW_NUMBER() OVER (ORDER BY {DatabaseColumn.ENROLLED_ON}) pos FROM {self._table_name} WHERE {DatabaseColumn.CLASS_ID} = ? AND {DatabaseColumn.DROPPED} = false AND {DatabaseColumn.WAITING_LIST} = true"
        query = f"SELECT pos from ({sub_query}) where {DatabaseColumn.STUDENT_ID} = ?"
        argument = [class_id, student_id]
        self._logger.debug(f'Executing row number query: [{query}], arguments: {argument}')
        data = self._conn.execute(query, argument).fetchone()
        return None if data is None else data[0]


class ProfileRepository (BasicRepository):

    def __init__(self, conn: Connection, table_name: str, logger: Logger):
        super().__init__(conn, table_name, logger)